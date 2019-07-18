from django.utils.module_loading import autodiscover_modules

__version__ = '0.1.0'

__all__ = [
    'autodiscover',
]


def autodiscover():
    autodiscover_modules('diagnostic')


default_app_config = 'django_diagnostic.apps.DjangoDiagnosticConfig'
