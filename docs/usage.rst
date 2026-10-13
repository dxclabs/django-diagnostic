=====
Usage
=====

Setup
-----

Add the app and its URLs to the host project:

.. code-block:: python

    # settings
    INSTALLED_APPS = [
        ...
        "django_diagnostic",
    ]

    # urls.py
    from django.urls import include, path

    urlpatterns = [
        ...
        path("diagnostic/", include("django_diagnostic.urls")),
    ]

Every page requires a logged-in superuser (django-braces ``SuperuserRequiredMixin``).
``/diagnostic/`` is the index of registered reports; each report is served at
``/diagnostic/<app_name>/<slug>/``.

The templates extend the host's ``base.html`` and fill its ``title`` and ``content``
blocks.

Built-in reports
----------------

==============================  ====================================================
Report                          Shows
==============================  ====================================================
Celery Results Summary          task results from django-celery-results (needs the
                                ``celery_results`` extra and ``RESULTS_BACKEND``)
Database PostgreSQL             server version and status, size, extensions, the
                                largest tables, connections, long-running queries
                                and blocked locks (needs ``APP_ENV``)
Debug                           the page's full template context, pretty-printed
Demo                            demo system settings (needs ``DEMO``)
Devops                          the running code's revision, Python and Django
                                versions and host, and a placeholder table of
                                service checks (not implemented yet)
Environment                     the OS environment, with secrets masked
Static Manifest                 the static files manifest and storage settings
Settings                        Django settings, with secrets masked
Sessions                        current sessions and their users
Diagnostic Reports Registry     every registered report, including any that fail to
                                import (the index skips those)
==============================  ====================================================

Settings
--------

The package adds no settings of its own. A few reports read settings the host defines:

``APP_ENV``
    a label for the environment, shown by the database report.

``DEMO``
    a boolean, shown by the demo report.

``RESULTS_BACKEND``
    the Celery results backend; the summary only reads results when it's
    ``"django-db"``.

Registering your own reports
----------------------------

Decorate a view class with ``Diagnostic.register``. The report is listed on the index
under the app that defines it, using the class docstring as its description:

.. code-block:: python

    from braces.views import SuperuserRequiredMixin
    from django.views.generic import TemplateView
    from django_diagnostic.decorators import Diagnostic


    @Diagnostic.register(link_name="Fact Types", slug="fact-types")
    class FactTypesView(SuperuserRequiredMixin, TemplateView):
        """Fact types and their counts."""

        template_name = "fact/diagnostic_fact_types.html"

* The app name is the first part of the class's module path (``fact`` for
  ``fact.diagnostic_view_fact_types``), so this report is at
  ``/diagnostic/fact/fact-types/``.
* Registration happens when the module is imported. Import it somewhere that always
  loads, such as the app's ``urls.py``, or the report won't appear.
* Keep ``SuperuserRequiredMixin`` on the view: the dispatcher checks the superuser
  login, but a report that's also routed directly needs its own check.
* The dispatcher calls the view with no URL arguments, and errors the report raises go
  to Django's normal error handling.
