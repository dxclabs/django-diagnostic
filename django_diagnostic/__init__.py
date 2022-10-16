from django.utils.module_loading import autodiscover_modules

__version__ = "1.0.0"

__all__ = [
    "autodiscover",
]


def autodiscover():
    autodiscover_modules("diagnostic", "diagnostic_views", "diagnostic_views.")
