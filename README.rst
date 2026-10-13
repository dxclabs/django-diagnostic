=================
Django Diagnostic
=================

Diagnostic pages for a Django application: settings, environment, database, sessions,
the running code's git revision and more, all behind a superuser login. Host apps can
register their own reports alongside the built-in ones.

Quickstart
----------

Add it to the host app's dependencies, pinned to a release tag (it isn't on PyPI):

.. code-block:: toml

    dependencies = [
        "django-diagnostic[git,celery_results] @ git+https://github.com/dxclabs/django-diagnostic.git@v1.8.1",
    ]

Add it to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "django_diagnostic",
    ]

Include its URLs:

.. code-block:: python

    from django.urls import include, path

    urlpatterns = [
        ...
        path("diagnostic/", include("django_diagnostic.urls")),
    ]

``/diagnostic/`` then lists every registered report. See ``docs/installation.rst`` and
``docs/usage.rst`` for the extras, the settings some reports need, and how to register
your own.

Development
-----------

See ``CONTRIBUTING.rst`` and ``docs/development/``.
