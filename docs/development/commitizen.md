# Commitizen

This repo uses [Commitizen](https://commitizen-tools.github.io/commitizen/) to bump the
version, tag the release and write the changelog from Conventional Commits, automatically on
every merge to `master`. It replaced autopub.

## What happens on a merge to master

`.github/workflows/bump.yaml` runs on every push to `master` (skipped when the commit itself
starts with `bump:`):

1. It signs in as the release-bot GitHub App (`RELEASE_BOT_CLIENT_ID` variable,
   `RELEASE_BOT_PRIVATE_KEY` secret) and runs `cz bump --yes --changelog`.
2. Commitizen reads the commits since the last version tag, works out the bump level, updates
   the version, prepends a changelog entry, and creates a `bump: version X → Y` commit and a
   `vY` tag.
3. The workflow pushes the commit and tag.

Nothing is deployed: django-diagnostic is a package that host apps install, pinned to a tag
(showoff-mint:
`django-diagnostic[git,celery_results] @ git+https://github.com/dxclabs/django-diagnostic.git@v1.8.1`).
A new release reaches a host app only when it moves that pin.

PRs are squash-merged, so **the PR title is the commit message commitizen sees** and must be
a valid Conventional Commit (`feat: ...`, `fix: ...`). A non-conventional title means no
release.

## Bump levels

Configured under `[tool.commitizen.customize]` in `pyproject.toml`:

| Commit prefix | Bump |
|---|---|
| `feat` | MINOR |
| `fix`, `perf`, `refactor`, `build` | PATCH |
| any type with `!` (`feat!:`), or a `BREAKING CHANGE` footer | MAJOR |
| `chore`, `ci`, `docs`, `style`, `test`, `revert`, `bump` | no release |

## Version source

`version_provider = "uv"`: the version lives in `[project].version` in `pyproject.toml`,
and a bump also updates this project's entry in `uv.lock`. `version_files` also updates
`django_diagnostic/__init__.py`, which the Sphinx docs and the index page read.

Tags are `v$version` (e.g. `v1.8.1`). Older tags without the `v` are still recognised
(`legacy_tag_formats`).

## Changelog

`docs/changelog.rst`, regenerated on every bump. Entries before the switch keep autopub's
format; don't hand-edit new ones.

## Checking locally

```powershell
uv run cz bump --dry-run --changelog       # preview the next version and changelog entry
uv run cz check --rev-range origin/master..HEAD   # check commit messages on a branch
```

The prek `commit-msg` hook runs `cz check` on every commit.
