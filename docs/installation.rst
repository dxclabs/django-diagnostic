============
Installation
============

django-diagnostic isn't published to PyPI. Host apps install it from GitHub, pinned to a
release tag. Releases are tagged ``vX.Y.Z`` on every merge to ``master`` (see
``docs/development/commitizen.md``).

With uv, in the host app's ``pyproject.toml``:

.. code-block:: toml

    dependencies = [
        "django-diagnostic[git,celery_results] @ git+https://github.com/dxclabs/django-diagnostic.git@v1.8.1",
    ]

or from the command line::

    uv add "django-diagnostic[git] @ git+https://github.com/dxclabs/django-diagnostic.git@v1.8.1"

To upgrade, move the tag and run ``uv lock``.

Requirements
------------

* Python 3.12+
* Django 6.0+
* PostgreSQL (``psycopg2-binary`` is a dependency; the database report queries
  PostgreSQL's catalogue)

Extras
------

``git``
    GitPython. The Debug, Devops, Environment and Settings reports show the running
    code's git describe, branch and commit. Without it, or when the app isn't running
    from a git checkout (a container image, say), they fall back to the ``SHORT_SHA``,
    ``BRANCH_NAME`` and ``COMMIT_SHA`` environment variables.

``celery_results``
    django-celery-results, for the Celery Results Summary report.
