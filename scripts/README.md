# `scripts/`

> Developer helpers. None of these scripts ship in the wheel or sdist —
> they exist to make running the lint gate, the dependency audit, and
> the build pipeline a single command.

## In this folder

| Script                       | Runs                                                                  |
| ---------------------------- | --------------------------------------------------------------------- |
| [`lint.sh`](lint.sh)         | The full lint gate: ruff (lint + format), black, isort, flake8, pylint `--errors-only`, mypy, bandit. CI runs the same set. |
| [`audit-deps.sh`](audit-deps.sh) | `pip-audit` against the locked dependencies.                       |
| [`build.sh`](build.sh)       | Clean + `poetry build`. Use before a release.                          |

## Run it

```bash
poetry run bash scripts/lint.sh
poetry run bash scripts/audit-deps.sh
poetry run bash scripts/build.sh
```

## What does NOT belong here

- **Importable code.** Anything the package needs lives in [`../django_admin_mcp_api/`](../django_admin_mcp_api/).
- **CI workflows.** Those live in [`../.github/workflows/`](../.github/workflows/).
- **Secrets or credentials** of any kind.
