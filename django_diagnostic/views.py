# import importlib
import json
import logging
import os
import pprint
import re
import socket
import sys
from pathlib import Path
from typing import Any

import django
from braces.views import SuperuserRequiredMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.validators import slug_re
from django.db import connection
from django.db.models import Case, Count, IntegerField, Max, Min, When
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import cached_import
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from git import InvalidGitRepositoryError, NoSuchPathError
from psycopg2.extensions import (
    STATUS_BEGIN,
    STATUS_IN_TRANSACTION,
    STATUS_PREPARED,
    STATUS_READY,
)

from django_diagnostic.decorators import Diagnostic

HAS_GIT = False
try:
    from git import Repo

    HAS_GIT = True
except ImportError:
    pass

HAS_TASK_RESULT = False
try:
    from django_celery_results.models import TaskResult

    HAS_TASK_RESULT = True
except ImportError:
    pass

module_logger = logging.getLogger(__name__)


QUERY_SECRET_KEYS = {"SENTRY_KEY", "TOKEN", "API_KEY", "PASSWORD", "SECRET"}


def mask_query_params(url: str) -> str:
    if "?" not in url:
        return url
    base, query = url.split("?", 1)
    parts = []
    for pair in query.split("&"):
        k, sep, v = pair.partition("=")
        if k.upper() in QUERY_SECRET_KEYS:
            v = "******"
        parts.append(f"{k}{sep}{v}")
    return f"{base}?{'&'.join(parts)}"


# Match user:password@ in URLs
URL_PASSWORD_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*:\/\/[^/:]+:)([^@]+)(@)")


def mask_url_string(url: str) -> str:
    # Replace password portion with ******
    return URL_PASSWORD_RE.sub(r"\1******\3", url)


def mask_url(value: str) -> str:
    value = mask_url_string(value)
    return mask_query_params(value)


def mask_value(key: str, value: Any) -> Any:  # noqa: ANN401
    SENSITIVE_KEYS = ["SECRET", "PASSWORD", "TOKEN", "HMAC", "KEY"]
    WHITELISTED_KEYS = [
        "PASSWORD_HASHERS",
        "CHANGE_PASSWORD",
        "RESET_PASSWORD",
        "RESET_PASSWORD_FROM_KEY",
    ]
    if key.upper() in WHITELISTED_KEYS:
        return value
    if any(pat in key.upper() for pat in SENSITIVE_KEYS):
        return "******"
    return value


def mask_sensitive(key: str, value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, str):
        if URL_PASSWORD_RE.search(value) or ("?" in value and "=" in value):
            return mask_url(value)
        return mask_value(key, value)

    if isinstance(value, dict):
        return {k: mask_sensitive(k, v) for k, v in value.items()}

    if isinstance(value, list):
        return [mask_sensitive(key, v) for v in value]

    return value


class IndexView(SuperuserRequiredMixin, TemplateView):
    page_title = _("Diagnostic Page Registry")
    page_heading = _("Diagnostic Page Registry")

    def get_template_names(self) -> str:
        return "django_diagnostic/index.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        registry_dict = {}

        for _key, value in sorted(Diagnostic.registry.items()):
            try:
                entry = {}
                # module_name = value["module"]
                # function_name = value["name"]
                # my_module = importlib.import_module(module_name)
                # my_klass = getattr(my_module, function_name)
                my_klass = cached_import(value["module"], value["name"])
                app_name = value["app_name"]
                entry["doc"] = my_klass.__doc__

                slug_value = value["slug"]
                slug = slugify(slug_value, allow_unicode=True)
                if slug_re.match(slug):
                    entry["slug"] = slug

                app_name_slug = slugify(app_name)
                if slug_re.match(app_name_slug):
                    entry["app_name"] = app_name_slug

                if "app_name" in entry and "slug" in entry:
                    module_logger.debug(
                        "Adding diagnostic to index: %s %s", app_name, slug
                    )

                    entry["link_name"] = value["kwargs"]["link_name"]
                    registry_key = slugify(
                        f"{app_name} {slug_value}", allow_unicode=True
                    )

                    if registry_key not in registry_dict:
                        registry_dict[registry_key] = entry

            except KeyError:
                pass

        context["registry"] = registry_dict
        return context


class DispatcherView(SuperuserRequiredMixin, TemplateView):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            slug = self.kwargs.get("slug", "")
            module_logger.debug(
                "DIAGNOSTIC DISPATCHER attempting to use slug: %s", slug
            )
            app_name = self.kwargs.get("app_name", "")
            module_logger.debug(
                "DIAGNOSTIC DISPATCHER attempting to use app_name: %s", app_name
            )
            if slug_re.match(slug) and slug_re.match(app_name):
                registry_key = slugify(f"{app_name} {slug}", allow_unicode=True)
                module_logger.debug(
                    "DIAGNOSTIC DISPATCHER retrieving entry with registry key: %s",
                    registry_key,
                )
                entry = Diagnostic.registry[registry_key]
                # module_name = entry["module"]
                # function_name = entry["name"]
                # my_module = importlib.import_module(module_name)
                # my_klass = getattr(my_module, function_name)
                my_klass = cached_import(entry["module"], entry["name"])
                return my_klass.as_view()(request, *args, **kwargs)
            return HttpResponseRedirect(reverse("django_diagnostic:index"))
        except KeyError:
            return HttpResponseRedirect(reverse("django_diagnostic:index"))
        except Exception as e:
            module_logger.exception(
                "Rendering diagnostic page resulted in error: %s", e
            )
            return HttpResponseRedirect(reverse("django_diagnostic:index"))


class GitCodeRunning:
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        try:
            repo = Repo(search_parent_directories=True)
            context["git_describe"] = repo.git.describe()
            context["git_detached_head"] = repo.head.is_detached
            if repo.head.is_detached is not True:
                context["git_active_branch"] = repo.active_branch.name
                context["active_branch_tracking_branch"] = (
                    repo.active_branch.tracking_branch()
                )
                context["hexsha"] = repo.active_branch.object.hexsha
            else:
                context["hexsha"] = repo.head.object.hexsha
        except (InvalidGitRepositoryError, NoSuchPathError):
            context["git_describe"] = os.environ.get("SHORT_SHA", _("<unknown>"))
            context["git_active_branch"] = os.environ.get("BRANCH_NAME", _("<unknown>"))
            context["active_branch_tracking_branch"] = _("<unknown>")
            context["hexsha"] = os.environ.get("COMMIT_SHA", _("<unknown>"))

        context["django_version"] = django.VERSION
        context["python_version"] = sys.version

        try:
            hostname = socket.gethostname()
        except OSError:
            hostname = ""

        context["hostname"] = hostname

        return context


# @Diagnostic.register(link_name='Celery', slug='celery')
class CeleryView(SuperuserRequiredMixin, TemplateView):
    """
    Celery system settings and controls
    """

    page_title = _("Celery Diagnostic")
    page_heading = _("Celery Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/celery.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


@Diagnostic.register(link_name="Celery Results Summary", slug="celery-results-summary")
class CeleryResultsSummary(SuperuserRequiredMixin, TemplateView):
    """
    Summary of celery results from TaskResults table.
    """

    page_title = _("Celery Results Summary")
    page_heading = _("Celery Results Summary")

    def get_template_names(self) -> str:
        return "django_diagnostic/celery_results_summary.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if settings.RESULTS_BACKEND == "django-db":
            tasks = (
                TaskResult.objects.values("task_name")
                .annotate(total=Count("id"))
                .annotate(earliest=Min("date_done"))
                .annotate(latest=Max("date_done"))
                .annotate(
                    successes=Count(
                        Case(
                            When(status="SUCCESS", then=1),
                            output_field=IntegerField(),
                        )
                    )
                )
                .annotate(
                    failures=Count(
                        Case(
                            When(status="FAILURE", then=1),
                            output_field=IntegerField(),
                        )
                    )
                )
                .order_by("task_name")
            )

            context["tasks"] = tasks

            totals = TaskResult.objects.aggregate(
                total=Count("id"),
                earliest=Min("date_done"),
                latest=Max("date_done"),
                successes=Count(
                    Case(
                        When(status="SUCCESS", then=1),
                        output_field=IntegerField(),
                    )
                ),
                failures=Count(
                    Case(
                        When(status="FAILURE", then=1),
                        output_field=IntegerField(),
                    )
                ),
            )

            context["totals"] = totals

        return context


def fetch_scalar(cursor: Any, sql: str) -> Any:  # noqa: ANN401
    cursor.execute(sql)
    return cursor.fetchone()[0]


def fetch_all(cursor: Any, sql: str) -> list[tuple]:  # noqa: ANN401
    cursor.execute(sql)
    return cursor.fetchall()


STATUS_MAP = {
    STATUS_READY: "Ready",
    STATUS_BEGIN: "Transaction started",
    STATUS_PREPARED: "Prepared",
    STATUS_IN_TRANSACTION: "In transaction",
}


@Diagnostic.register(link_name="Database PostgreSQL", slug="database-postgresql")
class DatabasePostgreSQLView(SuperuserRequiredMixin, TemplateView):
    """
    Basic information about postgresql database
    """

    page_title = _("PostgreSQL Diagnostic")
    page_heading = _("PostgreSQL Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/database_postgresql.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["db_name"] = settings.DATABASES.get("default", {}).get(
            "NAME", "<unknown>"
        )

        context["app_env"] = settings.APP_ENV
        context["db_version"] = connection.cursor().connection.server_version
        status_code = connection.cursor().connection.status
        context["db_status"] = (
            f"{STATUS_MAP.get(status_code, 'Unknown')} ({status_code})"
        )
        context["db_dsn"] = connection.cursor().connection.dsn

        with connection.cursor() as cursor:
            context.update(
                {
                    "db_size": fetch_scalar(
                        cursor,
                        "SELECT pg_size_pretty(pg_database_size(current_database()));",
                    ),
                    "db_extensions": fetch_all(
                        cursor,
                        """
                    SELECT extname, extversion, nspname
                    FROM pg_extension
                    JOIN pg_namespace
                    ON pg_extension.extnamespace = pg_namespace.oid
                    ORDER BY extname;
                    """,
                    ),
                    "db_table_sizes": fetch_all(
                        cursor,
                        """
                        SELECT *, pg_size_pretty(total_bytes) AS total,
                        pg_size_pretty(index_bytes) AS INDEX,
                        pg_size_pretty(toast_bytes) AS toast,
                        pg_size_pretty(table_bytes) AS TABLE
                        FROM (
                            SELECT *,
                                total_bytes - index_bytes - COALESCE(toast_bytes,0)
                                AS table_bytes
                            FROM (
                                SELECT c.oid, nspname AS table_schema,
                                    relname AS TABLE_NAME,
                                    c.reltuples AS row_estimate,
                                    pg_total_relation_size(c.oid) AS total_bytes,
                                    pg_indexes_size(c.oid) AS index_bytes,
                                    pg_total_relation_size(reltoastrelid) AS toast_bytes
                                FROM pg_class c LEFT JOIN pg_namespace n
                                    ON n.oid = c.relnamespace
                                WHERE relkind = 'r'
                            ) a
                        ) a
                        ORDER BY table_bytes DESC
                        LIMIT 10;
                        """,
                    ),
                    "db_checksums": fetch_scalar(cursor, "SHOW data_checksums;"),
                    "db_connections": fetch_all(
                        cursor,
                        """
                    SELECT
                        COUNT(*) FILTER (WHERE state = 'active') AS active,
                        COUNT(*) FILTER (WHERE state = 'idle') AS idle,
                        COUNT(*) FILTER (WHERE state = 'idle in transaction')
                          AS idle_in_tx,
                        COUNT(*) AS total
                    FROM pg_stat_activity;
                    """,
                    ),
                    "db_long_queries": fetch_all(
                        cursor,
                        """
                    SELECT pid, now() - query_start, state,
                        wait_event_type, wait_event, query
                    FROM pg_stat_activity
                    WHERE state <> 'idle'
                    ORDER BY query_start ASC
                    LIMIT 10;
                    """,
                    ),
                    "db_blocked_locks": fetch_all(
                        cursor,
                        """
                    SELECT locktype, relation::regclass, mode
                    FROM pg_locks
                    WHERE NOT granted;
                    """,
                    ),
                }
            )

        return context


@Diagnostic.register(link_name="Debug", slug="debug")
class DebugView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Generates a debug message using django debug traceback
    """

    page_title = _("Debug Diagnostic")
    page_heading = _("Debug Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/debug.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["debug_context"] = pprint.pformat(context, width=120)

        return context


@Diagnostic.register(link_name="Demo", slug="demo")
class DemoView(SuperuserRequiredMixin, TemplateView):
    """
    Demo system settings and controls
    """

    page_title = _("Demo Diagnostic")
    page_heading = _("Demo Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/demo.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["demo"] = settings.DEMO

        return context


@Diagnostic.register(link_name="Devops", slug="devops")
class DevopsView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Integration tests externally provided services and common functionality
    """

    page_title = _("DevOps Diagnostic")
    page_heading = _("DevOps Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/devops.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["environ"] = {k: mask_sensitive(k, v) for k, v in os.environ.items()}
        return context


@Diagnostic.register(link_name="Environment", slug="environment")
class EnvironmentView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Show the OS environment
    """

    page_title = _("Environment Diagnostic")
    page_heading = _("Environment Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/environment.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["environ"] = {k: mask_sensitive(k, v) for k, v in os.environ.items()}
        return context


@Diagnostic.register(link_name="Static Manifest", slug="manifest")
class ManifestView(SuperuserRequiredMixin, TemplateView):
    """
    Show the Whitenoise Static Manifest
    """

    page_title = _("Whitenoise Static Manifest Diagnostic")
    page_heading = _("Whitenoise Static Manifest Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/manifest.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        staticfiles = (
            f"{settings.STATIC_ROOT}/staticfiles.json" if settings.STATIC_ROOT else ""
        )
        context["staticfiles"] = staticfiles

        for key in dir(settings):
            if "static" in key.casefold():
                context[key.casefold()] = getattr(settings, key)

        context["staticfiles_storage"] = settings.STORAGES.get("staticfiles")

        try:
            with Path.open(staticfiles) as f:
                manifest_json_object = json.load(f)
            context["manifest"] = manifest_json_object
        except FileNotFoundError as e:
            context["error"] = str(e)

        return context


@Diagnostic.register(link_name="Settings", slug="settings")
class SettingsView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Django settings
    """

    page_title = _("Settings Diagnostic")
    page_heading = _("Settings Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/settings.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context_settings = {}
        for key in dir(settings):
            if key.isupper():  # only real settings
                val = getattr(settings, key)
                val = mask_sensitive(key, val)
                context_settings[key] = val

        context["settings"] = context_settings
        return context


@Diagnostic.register(link_name="Sessions", slug="sessions")
class SessionsView(SuperuserRequiredMixin, TemplateView):
    """
    Current Sessions and Users
    """

    page_title = _("Sessions Diagnostic")
    page_heading = _("Sessions Diagnostic")

    def get_template_names(self) -> str:
        return "django_diagnostic/sessions.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        # context["sessions"] = sessions.values_list(
        #     "session_key", "expire_date"
        # ).order_by("-expire_date")

        decoded_sessions = {}
        uid_list = []
        for session in sessions:
            decoded_session = {}
            decoded_session["session_key"] = session.session_key
            decoded_session["expire_date"] = session.expire_date
            data = session.get_decoded()
            attributes = data.get("attributes")
            if attributes:
                for key, value in attributes.items():
                    decoded_session[key] = value
            decoded_session["auth_user_id"] = data.get("_auth_user_id", None)
            decoded_session["auth_user_backend"] = data.get("_auth_user_backend", None)
            decoded_session["auth_user_hash"] = data.get("_auth_user_hash", None)
            module_logger.debug(
                "DIAGNOSTIC REGISTER adding decoded session to context: %s",
                decoded_session,
            )

            decoded_sessions[session.session_key] = decoded_session

            # also build a list of user ids from that query
            uid_list.append(data.get("_auth_user_id", None))

        context["decoded_sessions"] = decoded_sessions
        module_logger.debug(
            "DIAGNOSTIC REGISTER decoded sessions context: %s",
            context["decoded_sessions"],
        )

        # Query all logged in users based on id list
        UserModel = get_user_model()
        users_by_id = {
            str(user.id): user for user in UserModel.objects.filter(id__in=uid_list)
        }

        for _session_key, session_data in decoded_sessions.items():
            user_id = str(session_data["auth_user_id"])
            user = users_by_id.get(user_id)
            if user:
                session_data["username"] = user.get_username()
                session_data["full_name"] = user.get_full_name()
            else:
                session_data["username"] = None
                session_data["full_name"] = None

        return context
