"""Main FastAPI application for DataDotMD."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from datadotmd.app.config import settings
from datadotmd.database.service import init_db
from datadotmd.system.scheduler import DirectoryScanScheduler


# Global scheduler instance
_scheduler: DirectoryScanScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _scheduler
    
    # Startup
    init_db()
    
    if settings.enable_auto_scan:
        _scheduler = DirectoryScanScheduler(interval_minutes=settings.auto_scan_interval_minutes)
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
    )

    # Import and include routers
    from datadotmd.app import routes
    app.include_router(routes.router)

    return app


app = create_app()
