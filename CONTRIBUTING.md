# Contributing to django-admin-mcp-api

Thank you for considering a contribution. This package is small by design
— a wire-protocol adapter, no admin logic — so most contributions land
fast.

## TL;DR

```bash
poetry install
poetry run pytest                    # full test suite
poetry run bash scripts/lint.sh      # ruff + black + isort + flake8 + pylint + mypy + bandit
poetry run pip-audit                 # dependency audit
```

Open a PR against `main` with a `feat/…`, `fix/…`, `docs/…`, or
`chore/…` branch. Link the PR to its issue.

## What this package will not accept

This is the strictest rule in the repo: **no new admin functionality
lives here**.

- Database queries — go to `django-admin-rest-api`.
- Permission checks — go to `django-admin-rest-api`.
- Serialization — go to `django-admin-rest-api`.
- New endpoints, new validation, new behaviour — go to
  `django-admin-rest-api`.

If your PR touches one of those, the reviewer will redirect you. If
your PR teaches an MCP tool to do something rest-api can't already do,
the PR will be closed in favour of an issue on the rest-api repo.

## What this package *does* accept

- New tools that mirror a new rest-api endpoint, 1:1.
- Better JSON-Schema input validation for existing tools.
- Improvements to the JSON-RPC error mapping.
- Documentation, screenshots, examples.
- Test coverage improvements.
- Performance / readability improvements that do not change behaviour.

## House rules

Mirrored from [`django-admin-react`](https://github.com/MartinCastroAlvarez/django-admin-react)
for family consistency:

1. **Every folder has a `README.md`.** If you add a folder, add one in the
   same commit.
2. **Tests before or alongside features.** Each new tool needs a
   `build_target` case in `tests/test_tools.py` and (where it adds wire
   behaviour) a view-level case in `tests/test_views.py`.
3. **CSRF stays on.** No `@csrf_exempt`.
4. **No `objects.all()` / `objects.filter()` in `server/`.** Queries
   belong to rest-api.
5. **No secrets in commits.** Pre-commit hooks (gitleaks + pygrep) will
   stop you; never bypass with `--no-verify`.
6. **One PR per branch.** Keep PRs small; split aggressively.

## Pre-commit hooks

Install once:

```bash
poetry run pip install pre-commit
pre-commit install
```

After that, every commit runs the same gate CI runs. The hooks are
authoritative — if one fires, fix the diff, don't `--no-verify`.

## Reporting bugs

[Open an issue](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/issues/new).
For security issues, see [SECURITY.md](SECURITY.md) — use a private
advisory, not a public issue.

## License

MIT — see [LICENSE](LICENSE).
