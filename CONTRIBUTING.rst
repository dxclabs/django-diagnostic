============
Contributing
============

Issues and pull requests go to https://github.com/dxclabs/django-diagnostic.

Setup
-----

You need `uv <https://docs.astral.sh/uv/>`_ and `prek <https://prek.j178.dev/>`_::

    git clone git@github.com:dxclabs/django-diagnostic.git
    cd django-diagnostic
    uv sync --all-groups
    prek install

``prek install`` sets up the ``pre-commit`` hooks (ruff, pyupgrade, django-upgrade,
codespell, the uv lock check and file hygiene) and the ``commit-msg`` hook that checks
Conventional Commit messages. More in ``docs/development/``.

Tests and checks
----------------

::

    uv run pytest tests/          # uses tests/settings.py
    uv run ty check
    prek run --all-files

CI runs the same lint, ruff and tests on every pull request to ``master``.

Making a change
---------------

1. Branch from ``master`` (the ``no-commit-to-branch`` hook stops commits to it).
2. Commit with Conventional Commit messages: ``feat:``, ``fix:``, ``build:``,
   ``docs:``, ``chore:`` and so on.
3. Open a pull request. It's squash-merged, so **its title becomes the commit
   message** that decides the release: ``feat`` is a minor release, ``fix``, ``perf``,
   ``refactor`` and ``build`` a patch, and ``chore``, ``ci``, ``docs``, ``style`` and
   ``test`` none. See ``docs/development/commitizen.md``.
4. Add or update tests for behaviour changes, and update ``docs/usage.rst`` when
   reports or settings change.

Merging to ``master`` bumps the version, updates ``docs/changelog.rst`` and tags the
release. Host apps get it when they move their tag pin.
