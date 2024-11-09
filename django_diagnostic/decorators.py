import logging

from django.core.validators import slug_re
from django.utils.text import slugify

module_logger = logging.getLogger(__name__)


# class Diagnostic:
#     @classmethod
#     def register(cls, *args, **kwargs):
#         def decorator(fn):
#             return fn
#         return decorator


class Diagnostic:
    registry: dict = {}

    @classmethod
    def register(cls, *args, **kwargs):
        def decorator(fn):
            # module_logger.debug(f"diag register args: {args} kwargs: {kwargs}")
            registration = {}
            registration["name"] = fn.__name__
            registration["module"] = fn.__module__
            try:
                app_name = fn.__module__.split(".")[0]
                registration["app_name"] = app_name
            except KeyError:
                pass

            registration["args"] = args
            registration["kwargs"] = kwargs
            slug = kwargs["slug"]

            registry_key = slugify(f"{app_name} {slug}", allow_unicode=True)

            if slug_re.match(slug):
                # module_logger.debug(f"slug valid: {slug} registry entry: {registration}")
                registration["slug"] = slugify(slug, allow_unicode=True)

                if registry_key and registry_key not in cls.registry:
                    cls.registry[registry_key] = registration

                # module_logger.debug(f"diag registry key: {registry_key} reg length: {len(cls.registry.keys())}")
            else:
                module_logger.debug(
                    f"unable to register diagnostic registry key: {registry_key}"
                )

            return fn

        return decorator
