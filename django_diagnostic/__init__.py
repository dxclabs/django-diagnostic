from django.utils.module_loading import autodiscover_modules

__version__ = "0.4.0"

__all__ = [
    "autodiscover",
]


def autodiscover():
    autodiscover_modules("diagnostic", "diagnostic_views", "diagnostic_views.")


default_app_config = "django_diagnostic.apps.DjangoDiagnosticConfig"
