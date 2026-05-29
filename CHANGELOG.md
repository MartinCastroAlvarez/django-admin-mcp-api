# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] — 2026-05-29

### Changed
- **`django-admin-rest-api` constraint floor raised from `^1.0.0` → `^1.0.6`.**
  Required to expose the new `target` field on action descriptors
  (batch vs detail). Fresh installs were already on 1.0.6 via the
  caret range; this just makes the requirement explicit.
- **`admin.action` tool description** spells out the new batch/detail
  dispatch — agents reading `tools/list` (or `admin.registry`) see
  the `target` field on each action and can decide whether to pass
  one pk (detail) or many (batch). The wire endpoint is unchanged;
  rest-api dispatches internally based on the action callable's
  signature.
- **`admin.action.pks` schema description** notes the per-target
  constraint (exactly 1 for detail, ≥1 for batch).

### Notes
No code change in the dispatch layer. The new `target` field flows
through every existing tool that surfaces action descriptors
(`admin.registry`, `admin.list`, `admin.retrieve`) without any
wrapping — rest-api adds the field; this package forwards it. The
74 existing tests still pass; agents that already use `admin.action`
keep working unchanged for batch actions.

## [1.0.1] — 2026-05-28

### Changed
- README rewritten in `django-admin-rest-api`'s visual style — simple
  `#` H1 + blockquote tagline, six-badge row, three-package family
  table with emoji-coded rows, and single-emoji section markers
  throughout.
- Folder READMEs (`django_admin_mcp_api/`, `server/`, `tools/`,
  `tests/`, `scripts/`, `docs/`, `examples/`) standardised on the
  same "tagline → In this folder → What does NOT belong here →
  See also" pattern.
- `django-admin-rest-api` lockfile pinned to `1.0.1`.
- Top-level README now includes a "Configuration" section surfacing
  the `DJANGO_ADMIN_MCP_API` settings namespace.

### Added
- `.github/workflows/publish.yml` — auto-publishes to PyPI on `v*`
  tag push via Trusted Publishing. Records the publish as a
  deployment under the `pypi` environment so it shows in the GitHub
  Deployments sidebar.
- `CONTRIBUTING.md` "Releases" section documenting the tag-and-push
  flow.

### Removed
- `.github/README.md` — GitHub was surfacing it on the repo home
  page in place of the root README.
- `ALLOW_ANONYMOUS` from every user-facing doc (README, ARCHITECTURE,
  quickstart settings). The setting is now an internal test-only knob;
  the security suite scans for it leaking back into docs.

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
