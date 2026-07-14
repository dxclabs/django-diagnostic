CHANGELOG
###############

v1.8.1 (2026-07-14)
===================


- build: bump Django to 6.0.7 and GitPython to 3.1.51, clear RHDA vulnerabilities (#44)
- Django>=6.0.7,<7.0 (was <6.0), GitPython>=3.1.51 in the git extra (was
>=3.1.27) - clears the flagged RHDA vulnerabilities in both. Test suite
(6 tests) passes against Django 6.0.7.
- Also: prek autoupdate (ruff-pre-commit v0.15.20 -> v0.15.21, uv-pre-commit
0.11.25 -> 0.11.28), and bump astral-sh/ruff-action v4.0.0 -> v4.1.0 in
ruff.yaml to match open Dependabot PR #43.
- Co-authored-by: Claude Sonnet 5 <noreply@anthropic.com>

v1.8.0 (2026-07-09)
===================


- feat: migrate build tooling to uv/prek/ty, fix host-app report dispatch
- * Migrate build tooling to uv/prek/ty and fix host-app report dispatch
- Mirrors the poetry->uv/PEP 621, ty, GitHub Actions, and prek migrations
already done on showoff-mint, plus a lint/typing cleanup pass and a
dependency refresh that clears the 3 open Dependabot alerts (Django,
cryptography, idna).
- The functional fix this was in service of: DispatcherView forwarded its
own app_name/slug URL kwargs into host-app-registered report views, and
swallowed any exception those views raised into a silent redirect back
to the index. That's why host-app-registered reports showed up in the
list but never actually executed. Diagnostic.build_registry_key is now
the single source of truth for registry keys (register()/IndexView/
DispatcherView previously built the same key two different ways), and
DispatcherView now only catches registry-lookup failures, letting real
report errors propagate to Django's normal exception handling.
- Also fixes two related latent bugs found while tracing this: views.py
imported GitPython unconditionally despite it being an optional extra,
and pyproject.toml's DJANGO_SETTINGS_MODULE pointed at a nonexistent
"zoo.settings.docker" (copied from mint), so pytest couldn't even boot.
- Adds a built-in "Diagnostic Reports Registry" report for introspecting
the registry itself, including entries that fail to import.
- Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- * Show django-diagnostic's version on the index page
- Muted text next to the "Diagnostic Page Registry" heading.
- Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- * Replace autopub with commitizen for version bumps, matching showoff-mint
- Adds bump.yaml, triggered on push to master (post-merge), that runs
`cz bump --changelog` and pushes the resulting version bump + tag.
Lint/ruff/tests workflows already only trigger on pull_request, so no
change needed there.
- [tool.autopub] is removed in favor of [tool.commitizen], configured the
same way as showoff-mint except tag_format stays unprefixed ("$version")
to match this repo's existing tag history (1.7.0, not v1.7.0).
- Note: this PR bumps the version to 1.8.0 manually rather than via cz
bump, so pyproject.toml and the latest git tag (1.7.0) are out of sync
until a 1.8.0 tag is pushed after merge -- cz bump will fail with "No
tag matching configuration could be found" until that's done once.
- Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- * Use v-prefixed tags going forward, matching showoff-mint
- tag_format = "v\$version" / legacy_tag_formats = ["\$version"], same as
mint. django-diagnostic's tag history is mixed (some v-prefixed like
v0.4.0, some not like 1.7.0) -- this makes new tags consistent with
mint while still letting commitizen recognize the latest unprefixed
tag (1.7.0) as the pre-migration baseline.
- Note: the one-time seed tag needed after this PR merges (see previous
commit) should now be v1.8.0, not 1.8.0.
- Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- * Revert manual 1.8.0 bump, let cz bump handle it on merge
- This PR should land at 1.7.0 and let bump.yaml's cz bump do the actual
version/tag/changelog work after merge, rather than pre-baking a
version this branch never tagged. Confirmed locally that the existing
unprefixed "1.7.0" tag alone is a sufficient baseline for cz bump via
legacy_tag_formats -- no separate v1.7.0 tag is needed.
- Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- ---------
- Co-authored-by: Claude Sonnet 5 <noreply@anthropic.com>

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
