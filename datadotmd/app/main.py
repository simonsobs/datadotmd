"""Main FastAPI application for DataDotMD."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from datadotmd.app.config import settings
from datadotmd.database.service import init_db
from datadotmd.system.scheduler import DirectoryScanScheduler
from soauth.toolkit.fastapi import global_setup, mock_global_setup


# Global scheduler instance
_scheduler: DirectoryScanScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _scheduler

    # Startup
    init_db()

    if settings.enable_auto_scan:
        _scheduler = DirectoryScanScheduler(
            interval_minutes=settings.auto_scan_interval_minutes
        )
        _scheduler._scan_job()  # Run on startup
        _scheduler.start()

    yield

    # Shutdown
    if _scheduler:
        _scheduler.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    root_path = settings.get_root_path()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        root_path=root_path,
        openapi_url=f"{root_path}/openapi.json" if settings.debug else None,
    )

    if settings.auth_type == "soauth":
        app = global_setup(
            app=app,
            app_base_url=settings.app_base_url,
            authentication_base_url=settings.authentication_base_url,
            app_id=settings.app_id,
            client_secret=settings.client_secret,
            public_key=settings.public_key,
            key_pair_type=settings.key_pair_type,
        )

        app.add_exception_handler(401, lambda request, exc: RedirectResponse(url=f"{settings.authentication_base_url}/login/{settings.app_id}"))
        app.add_exception_handler(403, lambda request, exc: RedirectResponse(url=f"{settings.authentication_base_url}/login/{settings.app_id}"))
    else:
        app = mock_global_setup(app, grants=[settings.required_grant])

    static_dir = Path(__file__).parent / "static"
    static = StaticFiles(directory=static_dir)
    app.mount("/static", static, name="static")

    # Import and include routers
    from datadotmd.app import routes

    app.include_router(routes.router)

    return app


app = create_app()
