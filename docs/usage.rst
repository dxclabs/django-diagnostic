=====
Usage
=====

To use Django Diagnostic in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_diagnostic.apps.DjangoDiagnosticConfig',
        ...
    )

Add Django Diagnostic's URL patterns:

.. code-block:: python

    from django_diagnostic import urls as django_diagnostic_urls


    urlpatterns = [
        ...
        url(r'^', include(django_diagnostic_urls)),
        ...
    ]
