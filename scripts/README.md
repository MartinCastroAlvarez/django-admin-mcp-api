# `scripts/`

Developer scripts. These are *helpers* — none of them are required to
ship the package. The shipped wheel/sdist do not include this folder.

| Script           | Purpose                                                       |
| ---------------- | ------------------------------------------------------------- |
| `lint.sh`        | Run the full lint gate (ruff, black, isort, flake8, pylint --errors-only, mypy, bandit). |
| `audit-deps.sh`  | `pip-audit` against the locked dependencies.                   |
| `build.sh`       | Clean + `poetry build`. Use before a release.                  |

Run any of them with:

```bash
poetry run bash scripts/<name>.sh
```

## What does NOT live here

- Anything that needs to be importable from the package (it goes in
  `django_admin_mcp_api/`).
- Anything project-specific (CI workflows live in `.github/workflows/`).
- Secrets, tokens, or credentials of any kind.
