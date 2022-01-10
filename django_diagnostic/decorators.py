import logging

from django.core.validators import slug_re
from django.utils.text import slugify

module_logger = logging.getLogger(__name__)


class Diagnostic:
    registry = dict()

    @classmethod
    def register(cls, *args, **kwargs):
        def decorator(fn):
            module_logger.debug(f"args: {args}")
            module_logger.debug(f"kwargs: {kwargs}")
            module_logger.debug(f"registry dict currently has {len(cls.registry.keys())}")
            registration = dict()
            registration["name"] = fn.__name__
            registration["module"] = fn.__module__
            try:
                app_name = fn.__module__.split(".")[0]
                registration["app_name"] = app_name
            except Exception:
                pass

            registration["args"] = args
            registration["kwargs"] = kwargs
            slug = kwargs["slug"]

            registry_key = slugify(f"{app_name} {slug}", allow_unicode=True)

            if slug_re.match(slug):
                module_logger.debug(f"slug matched ok: {slug}")
                module_logger.debug(f"Storing dict in registry: {registration}")
                registration["slug"] = slugify(slug, allow_unicode=True)

                if registry_key and registry_key not in cls.registry:
                    cls.registry[registry_key] = registration
                module_logger.debug(f"registry key is {registry_key}")
                module_logger.debug(f"registry dict now has {len(cls.registry.keys())} items")
            else:
                module_logger.debug(f"unable to register diagnostic registry key: {registry_key}")

            return fn

        return decorator
