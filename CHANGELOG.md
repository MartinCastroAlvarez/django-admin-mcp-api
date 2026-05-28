# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-05-28

### Added
- JSON Schema input validation on every `tools/call`. Arguments are
  checked against the tool's declared `input_schema` (Draft 2020-12)
  *before* forwarding to django-admin-rest-api, so malformed calls
  surface as `INVALID_PARAMS` with the json-pointer path of the
  failing field instead of bubbling up as a generic rest-api 400.
- `docs/threat-model.md` — MCP-layer threat model (assets, trust
  boundaries, mitigations, out-of-scope items, review checklist).
- `docs/api-contract.md` — the full MCP wire contract (JSON-RPC
  envelope, the three methods, error code vocabulary, semver policy).
- GitHub issue templates (`bug_report.yml`, `feature_request.yml`,
  `config.yml`) and a PR template that nudge contributors toward the
  right venue and the right information.
- `.github/CODEOWNERS` routing every PR review through the
  package maintainer with extra protection on the wire layer and the
  `.github/` folder.

### Changed
- **Pinned to `django-admin-rest-api ^1.0.0`** — the upstream REST API
  shipped its stable 1.0 at the same time, so the MCP adapter now
  requires the matching major. Users on the `0.1.0a0` alpha must
  upgrade to rest-api 1.x before installing this release.
- CI matrix swaps Django via `pip install` instead of `poetry add`, so
  the Python 3.12+ × Django 6.0 cells now resolve and pass.
- `Development Status` classifier promoted to `5 - Production/Stable`.

### Notes
This is the first stable release. The wire contract is now covered by
the semver policy in `docs/api-contract.md` §7 — any breaking change
will be a major version bump with a migration paragraph in this file.

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
