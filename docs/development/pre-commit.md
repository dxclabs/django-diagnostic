### Prek

Prek is a fast, Rust-native git hooks runner. Reference: https://prek.j178.dev/

Install prek following the instructions at https://prek.j178.dev/quickstart/ (standalone binary, no Python required).

Install git hooks with:
```
prek install
```

Run all hooks manually:
```
prek run --all-files
```

Update hook versions with:
```
prek autoupdate
```

---

### Pre Commit (deprecated)

> **Deprecated** — this project has migrated to [prek](#prek). The instructions below are kept for reference only.

Here's a useful reference:
https://pre-commit.com/

install pre-commit
```
python -m pip install pre-commit
```
or
```
python -m pip install -r requirements/requirements-dev.txt
```

Make sure you have the linters install (black, bandit, isort etc)

install git hooks with:
```
pre-commit install
```

Test with:
```
pre-commit run --all-files
```

Update hooks with:
```
pre-commit autoupdate
```
