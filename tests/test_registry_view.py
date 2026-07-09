from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from django_diagnostic.decorators import Diagnostic
from django_diagnostic.views import RegistryDiagnosticView

UserModel = get_user_model()


class RegistryDiagnosticViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = UserModel.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",  # noqa: S106 -- throwaway test fixture, not a real credential
        )

    def _render(self) -> dict:
        request = self.factory.get("/django_diagnostic/diagnostic-reports-registry/")
        request.user = self.superuser
        view = RegistryDiagnosticView()
        view.setup(request)
        return view.get_context_data()

    def test_lists_builtin_reports(self) -> None:
        context = self._render()
        slugs = {entry["slug"] for entry in context["entries"]}
        self.assertIn("debug", slugs)
        self.assertIn("diagnostic-reports-registry", slugs)
        self.assertEqual(context["registry_count"], len(Diagnostic.registry))

    def test_surfaces_import_failures_instead_of_hiding_them(self) -> None:
        registry_key = Diagnostic.build_registry_key("tests", "broken-registration")
        Diagnostic.registry[registry_key] = {
            "name": "DoesNotExist",
            "module": "tests.test_registry_view",
            "app_name": "tests",
            "slug": "broken-registration",
            "args": (),
            "kwargs": {"link_name": "Broken"},
        }
        try:
            context = self._render()
            entry = next(
                e for e in context["entries"] if e["registry_key"] == registry_key
            )
            self.assertIsNotNone(entry["import_error"])
            self.assertEqual(context["failed_count"], 1)
        finally:
            del Diagnostic.registry[registry_key]
