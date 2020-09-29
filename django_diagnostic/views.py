import importlib
import json
import logging
import os
import socket
import sys

import django
from braces.views import SuperuserRequiredMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.validators import slug_re
from django.db import connection
from django.db.models import Case, Count, IntegerField, Max, Min, When
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

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

from django_diagnostic.decorators import Diagnostic

module_logger = logging.getLogger(__name__)


class IndexView(SuperuserRequiredMixin, TemplateView):
    page_title = _("Diagnostic Page Registry")
    page_heading = _("Diagnostic Page Registry")

    def get_template_names(self):
        return 'django_diagnostic/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registry_dict = dict()
        # for key, value in sorted(Diagnostic.registry.items(),
        #                          key=lambda item: item[1].get('kwargs', dict()).get('app_name', '')):
        for key, value in sorted(Diagnostic.registry.items()):
            try:
                entry = dict()
                module_name = value['module']
                function_name = value['name']
                my_module = importlib.import_module(module_name)
                my_klass = getattr(my_module, function_name)
                app_name = my_module.__package__
                entry['doc'] = my_klass.__doc__

                slug_value = value['slug']
                slug = slugify(slug_value, allow_unicode=True)
                if slug_re.match(slug):
                    entry['slug'] = slug

                app_name_slug = slugify(app_name)
                if slug_re.match(app_name_slug):
                    entry['app_name'] = app_name_slug

                if 'app_name' in entry and 'slug' in entry:
                    module_logger.debug(f'Adding diagnostic to index: {app_name} {slug}')

                    entry['link_name'] = value['kwargs']['link_name']
                    registry_key = slugify(f'{app_name} {slug_value}', allow_unicode=True)

                    if registry_key not in registry_dict:
                        registry_dict[registry_key] = entry

            except Exception:
                pass

        context['registry'] = registry_dict
        return context


class DispatcherView(SuperuserRequiredMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        try:
            slug = self.kwargs.get('slug', '')
            module_logger.debug(f'diagnostic dispatcher attempting to use slug: {slug}')
            app_name = self.kwargs.get('app_name', '')
            module_logger.debug(f'diagnostic dispatcher attempting to use app_name: {app_name}')
            if slug_re.match(slug) and slug_re.match(app_name):
                registry_key = slugify(f'{app_name} {slug}', allow_unicode=True)
                module_logger.debug(f'retrieving entry with registry key: {registry_key}')
                entry = Diagnostic.registry[registry_key]
                module_name = entry['module']
                function_name = entry['name']
                my_module = importlib.import_module(module_name)
                my_klass = getattr(my_module, function_name)
                return my_klass.as_view()(request, *args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('django_diagnostic:index'))
        except KeyError:
            return HttpResponseRedirect(reverse('django_diagnostic:index'))
        except Exception as e:
            module_logger.error(f'Rendering diagnostic page resulted in error: {str(e)}')
            return HttpResponseRedirect(reverse('django_diagnostic:index'))


class GitCodeRunning(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            repo = Repo(search_parent_directories=True)
            context['git_describe'] = repo.git.describe()
            context['git_detached_head'] = repo.head.is_detached
            if repo.head.is_detached is not True:
                context['git_active_branch'] = repo.active_branch.name
                context['active_branch_tracking_branch'] = repo.active_branch.tracking_branch()
                context['hexsha'] = repo.active_branch.object.hexsha
            else:
                context['hexsha'] = repo.head.object.hexsha
        except Exception:
            context['git_describe'] = os.environ.get('SHORT_SHA', _('<unknown>'))
            context['git_active_branch'] = os.environ.get('BRANCH_NAME', _('<unknown>'))
            context['active_branch_tracking_branch'] = _('<unknown>')
            context['hexsha'] = os.environ.get('COMMIT_SHA', _('<unknown>'))

        context['django_version'] = django.VERSION
        context['python_version'] = sys.version

        try:
            hostname = socket.gethostname()
        except:
            hostname = ''
        context['hostname'] = hostname

        return context


# @Diagnostic.register(link_name='Celery', slug='celery')
class CeleryView(SuperuserRequiredMixin, TemplateView):
    """
    Celery system settings and controls
    """

    page_title = _('Celery Diagnostic')
    page_heading = _('Celery Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/celery.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


@Diagnostic.register(link_name='Celery Results Summary', slug='celery-results-summary')
class CeleryResultsSummary(SuperuserRequiredMixin, TemplateView):
    """
    Summary of celery results from TaskResults table
    """

    page_title = _('Celery Results Summary')
    page_heading = _('Celery Results Summary')

    def get_template_names(self):
        return 'django_diagnostic/celery_results_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.CELERY_RESULT_BACKEND == 'django-db':
            tasks = TaskResult.objects.values('task_name') \
                .annotate(total=Count('id')) \
                .annotate(earliest=Min('date_done')) \
                .annotate(latest=Max('date_done')) \
                .annotate(successes=Count(Case(When(status='SUCCESS', then=1), output_field=IntegerField(), ))) \
                .annotate(failures=Count(Case(When(status='FAILURE', then=1), output_field=IntegerField(), ))) \
                .order_by('task_name')

            context['tasks'] = tasks

            totals = TaskResult.objects \
                .aggregate(total=Count('id'),
                           earliest=Min('date_done'),
                           latest=Max('date_done'),
                           successes=Count(Case(When(status='SUCCESS', then=1), output_field=IntegerField(), )),
                           failures=Count(Case(When(status='FAILURE', then=1), output_field=IntegerField(), ))
                           )

            context['totals'] = totals

        return context


@Diagnostic.register(link_name='Database PostgreSQL', slug='database-postgresql')
class DatabasePostgreSQLView(SuperuserRequiredMixin, TemplateView):
    """
    Basic information about postgresql database
    """

    page_title = _('PostgreSQL Diagnostic')
    page_heading = _('PostgreSQL Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/database_postgresql.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            db_name = settings.DATABASES['default']['NAME']
            context['db_name'] = db_name

            context['db_version'] = connection.cursor().connection.server_version
            context['db_status'] = connection.cursor().connection.status
            context['db_dsn'] = connection.cursor().connection.dsn

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_size_pretty( pg_database_size(%s));", [db_name])
                db_size_row = cursor.fetchone()
                context['db_size'] = db_size_row[0]

                table_size_sql = f"SELECT *, pg_size_pretty(total_bytes) AS total, " \
                                 f"pg_size_pretty(index_bytes) AS INDEX, " \
                                 f"pg_size_pretty(toast_bytes) AS toast, " \
                                 f"pg_size_pretty(table_bytes) AS TABLE " \
                                 f"FROM (" \
                                 f"  SELECT *, total_bytes-index_bytes-COALESCE(toast_bytes,0) AS table_bytes" \
                                 f"  FROM (" \
                                 f"    SELECT c.oid,nspname AS table_schema," \
                                 f"           relname AS TABLE_NAME, " \
                                 f"           c.reltuples AS row_estimate, " \
                                 f"           pg_total_relation_size(c.oid) AS total_bytes," \
                                 f"           pg_indexes_size(c.oid) AS index_bytes," \
                                 f"           pg_total_relation_size(reltoastrelid) AS toast_bytes" \
                                 f"    FROM pg_class c LEFT JOIN pg_namespace n ON n.oid = c.relnamespace" \
                                 f"    WHERE relkind = 'r'" \
                                 f"  ) a" \
                                 f") a;"
                cursor.execute(table_size_sql)
                db_table_sizes = cursor.fetchall()
                context['db_table_sizes'] = db_table_sizes

        except Exception:
            pass

        return context


@Diagnostic.register(link_name='Debug', slug='debug')
class DebugView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Generates a debug message using django debug traceback
    """

    page_title = _('Debug Diagnostic')
    page_heading = _('Debug Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/debug.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #
    #     return context


@Diagnostic.register(link_name='Demo', slug='demo')
class DemoView(SuperuserRequiredMixin, TemplateView):
    """
    Demo system settings and controls
    """

    page_title = _('Demo Diagnostic')
    page_heading = _('Demo Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/demo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['demo'] = settings.DEMO
        # context['title'] = _('Demo Diagnostic')

        return context


@Diagnostic.register(link_name='Devops', slug='devops')
class DevopsView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Integration tests externally provided services and common functionality
    """

    page_title = _('DevOps Diagnostic')
    page_heading = _('DevOps Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/devops.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['environ'] = os.environ

        return context


@Diagnostic.register(link_name='Environment', slug='environment')
class EnvironmentView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Show the OS environment
    """

    page_title = _('Environment Diagnostic')
    page_heading = _('Environment Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/environment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['environ'] = os.environ

        return context


@Diagnostic.register(link_name='Static Manifest', slug='manifest')
class ManifestView(SuperuserRequiredMixin, TemplateView):
    """
    Show the Whitenoise Static Manifest
    """

    page_title = _('Whitenoise Static Manifest Diagnostic')
    page_heading = _('Whitenoise Static Manifest  Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/manifest.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if settings.STATIC_ROOT:
            staticfiles = f'{settings.STATIC_ROOT}/staticfiles.json'
        else:
            staticfiles = ''
        context['staticfiles'] = staticfiles

        for key in dir(settings):
            if 'static' in key.casefold():
                context[key.casefold()] = getattr(settings, key)

        try:
            with open(staticfiles, 'r') as f:
                manifest_json_object = json.load(f)
            context['manifest'] = manifest_json_object
        except FileNotFoundError as e:
            context['error'] = str(e)

        return context


@Diagnostic.register(link_name='Settings', slug='settings')
class SettingsView(SuperuserRequiredMixin, GitCodeRunning, TemplateView):
    """
    Django settings
    """

    page_title = _('Settings Diagnostic')
    page_heading = _('Settings Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['settings'] = settings.__dict__['_wrapped'].__dict__
        # context['title'] = _('Settings Diagnostic')

        return context


@Diagnostic.register(link_name='Sessions', slug='sessions')
class SessionsView(SuperuserRequiredMixin, TemplateView):
    """
    Current Sessions and Users
    """

    page_title = _('Sessions Diagnostic')
    page_heading = _('Sessions Diagnostic')

    def get_template_names(self):
        return 'django_diagnostic/sessions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        context['sessions'] = sessions.values_list('session_key', 'expire_date').order_by('-expire_date')

        decoded_sessions = dict()
        uid_list = []
        for session in sessions:
            decoded_session = dict()
            decoded_session['session_key'] = session.session_key
            decoded_session['expire_date'] = session.expire_date
            data = session.get_decoded()
            attributes = data.get('attributes')
            if attributes:
                for key, value in attributes.items():
                    decoded_session[key] = value
            decoded_session['auth_user_id'] = data.get('_auth_user_id', None)
            decoded_session['auth_user_backend'] = data.get('_auth_user_backend', None)
            decoded_session['auth_user_hash'] = data.get('_auth_user_hash', None)
            module_logger.debug(f'adding decoded session to context: {decoded_session}')

            decoded_sessions[f'{session}'] = decoded_session

            # also build a list of user ids from that query
            uid_list.append(data.get('_auth_user_id', None))

        context['decoded_sessions'] = decoded_sessions
        module_logger.debug(f"decoded sessions context: {context['decoded_sessions']}")

        # Query all logged in users based on id list
        UserModel = get_user_model()
        context['users'] = UserModel.objects.filter(id__in=uid_list)

        return context
