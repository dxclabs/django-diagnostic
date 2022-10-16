from django.apps import AppConfig


class DjangoDiagnosticConfig(AppConfig):
    name = "django_diagnostic"

    def ready(self):
        super().ready()
        self.module.autodiscover()
