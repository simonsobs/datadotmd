"""Template rendering utilities using Jinja2 with the templateify pattern."""

from functools import lru_cache, wraps
import inspect
import asyncio
from pathlib import Path
from typing import Annotated, Callable, Iterable

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from structlog import get_logger
from structlog.types import FilteringBoundLogger

from datadotmd.app.config import settings


def setup_templating(
    template_directory: Path,
    available_strings: dict[str, str] | None = None,
    extra_functions: dict[str, Callable] | None = None,
    context_processors: Iterable[Callable] = (),
) -> Callable:
    """
    Set up the Jinja2-based templating system.
    Returns a function for getting the templating system ready for use as a dependency.
    """

    def strings(r):
        """Add available strings to template context."""
        return available_strings or {}

    def functions(r):
        """Add extra functions to template context."""
        return extra_functions or {}

    templates = Jinja2Templates(
        directory=template_directory,
        context_processors=[strings, functions] + list(context_processors),
    )

    @lru_cache
    def get_templates():
        """Get cached templates instance."""
        return templates

    return get_templates


def logger():
    """Get structured logger."""
    return get_logger()


# Initialize templates with available strings
templates = setup_templating(
    template_directory=Path(__file__).parent / "templates",
    available_strings={
        "app_name": settings.app_name,
        "root_directory_name": settings.root_directory_name,
        "app_base_url": settings.app_base_url,
        "root_path": settings.get_root_path(),
        "auth_type": settings.auth_type,
        "auth_url": f"{settings.authentication_base_url}/{settings.app_id}"
        if settings.auth_type == "soauth"
        else None,
    },
)

# Type annotations for dependencies
LoggerDependency = Annotated[FilteringBoundLogger, Depends(logger)]
TemplateDependency = Annotated[Jinja2Templates, Depends(templates)]


def templateify(template_name: str | None = None, log_name: str | None = None):
    """
    Decorator to apply a template to a route.

    Your route should return a dictionary which is added to the template context.
    You must have `request: Request` and `templates: TemplateDependency` in your kwargs.
    If log_name is not None, you must also have `log: LoggerDependency`.

    Parameters
    ----------
    template_name : str | None
        The name of the template file to render
    log_name : str | None
        Optional log message to emit when the route is called
    """

    def decorator(route: Callable):
        @wraps(route)
        async def wrapped(*args, **kwargs):
            # Bind args/kwargs to the original route signature to get injected values
            bound = inspect.signature(route).bind_partial(*args, **kwargs)
            bound.apply_defaults()

            # Call the original route function to get context
            context = route(*args, **kwargs)
            if asyncio.iscoroutine(context):
                context = await context

            if context is None:
                context = {}

            request = bound.arguments.get("request")
            templates_instance: Jinja2Templates | None = (
                bound.arguments.get("templates")
                or bound.arguments.get("templates_obj")
                or kwargs.get("templates")
            )

            if templates_instance is None:
                raise RuntimeError("Template dependency was not injected.")

            if log_name is not None:
                log = bound.arguments.get("log") or kwargs.get("log")
                log.info(log_name)

            return templates_instance.TemplateResponse(
                request=request,
                name=template_name,
                context=context,
            )

        return wrapped

    return decorator
