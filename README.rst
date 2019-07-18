=============================
Django Diagnostic
=============================

.. image:: https://badge.fury.io/py/django-diagnostic.svg
    :target: https://badge.fury.io/py/django-diagnostic

.. image:: https://travis-ci.org/campbellmc/django-diagnostic.svg?branch=master
    :target: https://travis-ci.org/campbellmc/django-diagnostic

.. image:: https://codecov.io/gh/campbellmc/django-diagnostic/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/campbellmc/django-diagnostic

provides basic diagnostic pages for django application

Documentation
-------------

The full documentation is at https://django-diagnostic.readthedocs.io.

Quickstart
----------

Install Django Diagnostic::

    pip install django-diagnostic

Add it to your `INSTALLED_APPS`:

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

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
