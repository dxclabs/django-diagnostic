CHANGELOG
###############

1.8.0 - 2026-07-09
==================

fix: DispatcherView no longer forwards its own app_name/slug URL kwargs into host-app-registered report views, and no longer swallows exceptions raised by those views into a silent redirect -- this was why host-app-registered reports showed up in the index but failed to execute
fix: importing django_diagnostic.views no longer hard-fails when the optional GitPython extra isn't installed
fix: registry key building is now centralized in Diagnostic.build_registry_key, eliminating a raw-vs-slugified key mismatch between registration and lookup
feat: add built-in "Diagnostic Reports Registry" report, showing the full report registry including entries that fail to import
build: migrate from poetry to uv, PEP 621 dependency-groups
build: switch build backend to hatchling
ci: migrate github actions to uv, add dedicated tests workflow
ci: migrate pre-commit to prek
chore: replace mypy/django-stubs with ty
chore: fix DJANGO_SETTINGS_MODULE in pytest config (was pointing at a nonexistent settings module)
chore: remove legacy build tooling (poetry.lock, poetry.toml, MANIFEST.in, .travis.yml, tox.ini, setup.cfg, Makefile)
build: update dependencies to clear open Dependabot alerts (Django, cryptography, idna)

1.7.0 - 2025-12-28
==================

ci: update pre-commit
ci: update github actions
build: update pip packages
chore: update format of pyproject.toml to have [project] stanza
chore: revise pyproject.toml for optional dependencies
chore: remove .coveragerc, revise .editorconfig
refactor: clean up templates, enhance sessions, postgresql, debug, hide sensitive data in environment and settings
ci: remove group `types` install from install test in github lint workflow

1.6.0 - 2024-11-09
==================

ci: update pre-commit
build: update python and django versions
ci: update github actions, dependabot.yaml, travis.yml
refactor: ruff reformat files
fix: changelog.rst header for autopub

1.5.0 - 2023-02-11
==================

Update iPython version
