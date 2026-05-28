# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- JSON Schema input validation on every `tools/call`. Arguments are
  checked against the tool's declared `input_schema` (Draft 2020-12)
  *before* forwarding to django-admin-rest-api, so malformed calls
  surface as `INVALID_PARAMS` with the json-pointer path of the
  failing field instead of bubbling up as a generic rest-api 400.

### Changed
- CI matrix swaps Django via `pip install` instead of `poetry add`, so
  the Python 3.12+ × Django 6.0 cells now resolve and pass.

## [0.1.0a0] — 2026-05-28

### Added

- Initial package: `django_admin_mcp_api` Django app + URL conf.
- MCP JSON-RPC 2.0 wire protocol: `initialize`, `tools/list`, `tools/call`.
- 16-tool catalogue mirroring every `django-admin-rest-api` endpoint
  (registry, schema, recent_actions, list, retrieve, add_form, create,
  update, destroy, bulk_update, autocomplete, action, history,
  delete_preview, set_password, panel).
- `RestApiDispatcher` — forwards every MCP tool call through Django's
  URL resolver to the matching `django-admin-rest-api` view, carrying
  the caller's session/user/cookies/CSRF state untouched.
- `django-admin-rest-api` (>=0.1.0a0) declared as a mandatory runtime
  dependency; Dependabot watches it for automatic version bumps.
- Test suite (74 tests, 91% coverage) including end-to-end integration
  tests that exercise the full MCP → rest-api → response path.
- Linter stack matching `django-admin-react`: ruff, black, isort,
  flake8, pylint, mypy, bandit, pip-audit, plus a pre-commit config
  with gitleaks and a `no-partial-tokens` pygrep hook.
- Documentation: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`,
  `CONTRIBUTING.md`, `CLAUDE.md`, plus a folder-level README in every
  package directory.
