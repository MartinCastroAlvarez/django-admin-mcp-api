# Contributing to django-admin-mcp-api

Thank you for considering a contribution. This package is small by design
— a wire-protocol adapter, no admin logic — so most contributions land
fast.

## TL;DR

```bash
poetry install
poetry run pytest                    # full test suite
poetry run bash scripts/lint.sh      # ruff (check + format) + mypy + bandit
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

## Releases

Releases ship to PyPI through GitHub Actions. The process is:

1. **Bump the version** in a release PR — `pyproject.toml`,
   `django_admin_mcp_api/__init__.py`, and `CHANGELOG.md`.
2. **Merge the release PR** to `main`.
3. **Tag the merge commit** with the matching `vX.Y.Z` and push it:

   ```bash
   git tag -a v1.2.3 -m "django-admin-mcp-api 1.2.3"
   git push origin v1.2.3
   ```

4. **GitHub Actions takes over.** The
   [`Publish`](.github/workflows/publish.yml) workflow runs the full
   test suite, builds the sdist + wheel, scans the artefacts for any
   token-shaped string, and uploads to PyPI via Trusted Publishing
   (no API token in the repo). The deployment shows up in the repo's
   **Deployments** sidebar under the `pypi` environment, and the PR
   merge commit picks up a green "Deployed to pypi" badge.

If the tag does not match `pyproject.toml`'s version the workflow
fails before publishing — that catches half-finished release PRs.

## Reporting bugs

[Open an issue](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/issues/new).
For security issues, see [SECURITY.md](SECURITY.md) — use a private
advisory, not a public issue.

## License

MIT — see [LICENSE](LICENSE).
