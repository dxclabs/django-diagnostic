import logging
from collections.abc import Callable
from typing import Any, TypeVar

from django.core.validators import slug_re
from django.utils.text import slugify

module_logger = logging.getLogger(__name__)

T = TypeVar("T")


class Diagnostic:
    """Registry of superuser diagnostic reports, built-in and host-app registered."""

    registry: dict[str, dict[str, Any]] = {}

    @classmethod
    def build_registry_key(cls, app_name: str, slug: str) -> str:
        """Canonical registry key shared by registration and dispatch lookups."""
        return slugify(f"{app_name} {slug}", allow_unicode=True)

    @classmethod
    def register(cls, *args, **kwargs) -> Callable[[type[T]], type[T]]:
        def decorator(fn: type[T]) -> type[T]:
            slug = slugify(kwargs["slug"], allow_unicode=True)
            app_name = fn.__module__.split(".")[0]

            if not slug_re.match(slug):
                module_logger.debug(
                    "unable to register diagnostic, invalid slug: %s", slug
                )
                return fn

            registration = {
                "name": fn.__name__,
                "module": fn.__module__,
                "app_name": app_name,
                "slug": slug,
                "args": args,
                "kwargs": kwargs,
            }

            registry_key = cls.build_registry_key(app_name, slug)
            if registry_key not in cls.registry:
                cls.registry[registry_key] = registration
                module_logger.debug(
                    "registered diagnostic %s at registry key: %s",
                    registration["name"],
                    registry_key,
                )

            return fn

        return decorator
