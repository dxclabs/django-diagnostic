# uv

Dependencies are managed with [uv](https://docs.astral.sh/uv/): `pyproject.toml`
(`[project]` + `[dependency-groups]`) and `uv.lock`. django-diagnostic is a package (built
with hatchling), so `uv sync` also installs it into `.venv` in editable mode.

Host apps don't use `uv.lock`: they get the ranges in `[project].dependencies` and the
`git` / `celery_results` extras. Raise a floor there when a version must be avoided (for
example after a security advisory), not just in the lock.

## Local setup

```powershell
uv sync                             # main + the default `dev` group
uv sync --all-groups                # also linters and tests
uv run pytest tests/                # settings: tests/settings.py
```

## Dependency groups

| Group | Used for | Installed by host apps? |
|---|---|---|
| main (`[project].dependencies`) | the package | yes |
| extras `git`, `celery_results` | optional reports | when asked for |
| `dev` (synced by default) | ipython, ipdb, debug toolbar, commitizen | no |
| `linters` | ruff, pyupgrade, django-upgrade, codespell, ty | no |
| `tests` | pytest and friends | no |

## Updating

```powershell
uv lock --upgrade                   # everything, within the constraints in pyproject.toml
uv lock --upgrade-package django    # one package
uv add "package>=X.Y,<Z"            # add or raise a constraint (add --group <name> for a group)
uv tree --outdated --depth 1 --all-groups
```

The prek `uv-lock` hook checks `uv.lock` matches `pyproject.toml`. Commit both together.

## Type checking

```powershell
uv run ty check
```
