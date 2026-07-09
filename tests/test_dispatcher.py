"""
Regression tests for DispatcherView: host-app-registered reports must
receive no forwarded URL kwargs, and errors they raise must not be
silently swallowed into a redirect back to the index.
"""

from typing import Any

from braces.views import SuperuserRequiredMixin
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.views.generic import View

from django_diagnostic.decorators import Diagnostic
from django_diagnostic.views import DispatcherView

UserModel = get_user_model()


@Diagnostic.register(link_name="Kwargs Probe", slug="kwargs-probe")
class KwargsProbeDiagnosticView(SuperuserRequiredMixin, View):
    """Host-app-style report used to verify the dispatcher forwards no kwargs."""

    captured_kwargs: dict[str, Any] = {}

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # noqa: ARG002
        KwargsProbeDiagnosticView.captured_kwargs = dict(self.kwargs)
        return HttpResponse("ok")


@Diagnostic.register(link_name="Boom", slug="boom")
class BoomDiagnosticView(SuperuserRequiredMixin, View):
    """Host-app-style report that always raises, to prove errors propagate."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # noqa: ARG002
        raise RuntimeError("report exploded")


class DispatcherViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = UserModel.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",  # noqa: S106 -- throwaway test fixture, not a real credential
        )

    def _dispatch(self, app_name: str, slug: str) -> HttpResponse:
        request = self.factory.get(f"/{app_name}/{slug}/")
        request.user = self.superuser
        return DispatcherView.as_view()(request, app_name=app_name, slug=slug)

    def test_unknown_report_redirects_to_index(self) -> None:
        response = self._dispatch("unknown-app", "unknown-report")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_registered_report_receives_no_dispatcher_kwargs(self) -> None:
        KwargsProbeDiagnosticView.captured_kwargs = {"sentinel": "not cleared"}

        response = self._dispatch("tests", "kwargs-probe")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(KwargsProbeDiagnosticView.captured_kwargs, {})

    def test_exception_in_registered_report_propagates(self) -> None:
        with self.assertRaises(RuntimeError):
            self._dispatch("tests", "boom")
