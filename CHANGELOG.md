# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **`__version__` no longer drifts from the packaged version** (#62).
  It is now derived from the installed package metadata via
  `importlib.metadata.version`, so `manifest.server_info()` (and the MCP
  `initialize` block) always advertise the real release version instead
  of a hand-maintained string that had fallen to `1.0.4`.

### Changed
- **Consolidated the Python lint stack on Ruff + mypy + bandit** (#63).
  Removed Black, standalone isort, flake8, and pylint (their config
  blocks, dev dependencies, pre-commit hooks, and CI steps). Ruff now
  owns linting, formatting, and import sorting (`I`); the lockfile,
  `scripts/lint.sh`, and the docs are updated to match.
- **Enabled `mypy --strict`** (#64). Fixed the two `no-any-return`
  errors at the dispatch seam (`server/dispatch.py`) by casting the
  resolver view callable and the synthetic `RequestFactory` request to
  their concrete Django types.
- **Future-proofed the dispatcher except clause** (#67). Dispatcher
  exceptions now share a `DispatchError` base; the view catches that
  base so any new dispatcher failure mode maps to `SERVER_ERROR_UPSTREAM`
  instead of escaping to a Django 500.

### Removed
- **Deprecated `default_app_config`** from the package `__init__` (#65).
  It was removed in Django 4.1 and this package supports Django >=4.2,
  where `apps.py` is auto-discovered.
- **Inert `# noqa` directives** (`A003`, `D401`) that suppressed rules no
  configured tool enforces (#68); the explanatory text is kept as plain
  comments.

## [1.1.0] — 2026-05-31

### Added
- **Django 4.2 LTS support** ([django-admin-react#622](https://github.com/MartinCastroAlvarez/django-admin-react/issues/622)).
  The pin is relaxed from `django >=5.0,<7.0` to `django >=4.2,<7.0`;
  the CI matrix exercises 4.2 alongside 5.0 / 5.1 / 5.2 across Python
  3.10–3.13 (3.13 excluded for 4.2 conservatively since pip may
  resolve to a pre-4.2.16 release).
- **`Framework :: Django :: 4.2`** classifier.

### Changed
- **`django-admin-rest-api` constraint** `^1.0.11` → `^1.1.0` to pick
  up the API package's own Django 4.2 support and its
  `SimpleListFilter` value-shape normalisation. Supersedes the
  `^1.0.6` → `^1.0.11` bump from 1.0.4 — 1.1.0 is a strict
  superset.

### Why a minor bump
New supported environment (Django 4.2 LTS) per SemVer's "additive
features that broaden compatibility" guideline. No behaviour change
for consumers already on 5.0+; the MCP package forwards everything
to `django-admin-rest-api` and adds no Django logic of its own.

## [1.0.4] — 2026-05-31

### Changed
- **`django-admin-rest-api` constraint floor raised `^1.0.6` → `^1.0.11`.**
  Pulls in the upstream improvements since 1.0.6: actions runner caps
  pk-list length, history view redacts a denylist of field names
  (1.0.7); `PanelEndpointsMixin` deprecated in favour of declaring
  `panels = {...}` directly on `ModelAdmin` (1.0.8); rest-api's own
  system checks for settings hygiene (1.0.9); N+1 perf + custom-user-
  model safety (1.0.11). URL surface is unchanged across the range;
  the MCP dispatcher forwards to the same paths.
- **`admin.panel` tool description** updated — no longer mentions
  `PanelEndpointsMixin`. New copy describes the plain-Django
  `panels = {"name": "method_name"}` attribute approach; the mixin
  is now a deprecated no-op shim in rest-api and is kept only as a
  historical parenthetical so consumers on older rest-api versions
  recognise the term.
- **`docs/tools-reference.md` panel section** updated to match.

### Fixed
- README `serverInfo.version` example bumped 1.0.2 → 1.0.3 to reflect
  the previous shipped release; test count 95 → 96 to match current.

## [1.0.3] — 2026-05-31

The "ship the audit fixes" release. 16 audit issues triaged and closed
across six PRs. Two new public settings, one new endpoint shape, one
new URL conf, two new example directories, two new long-form docs,
plus an end-to-end Trusted-Publishing pipeline that no longer needs a
local token to ship a release.

### Added
- **`MAX_REQUEST_BYTES` setting** (default 256 KiB) — caps `/mcp/`
  POST envelopes well below Django's project-wide 2.5 MiB form-upload
  ceiling. Oversized requests return 413 + `INVALID_REQUEST` before
  the JSON parser runs.
- **`DISABLED_TOOLS` setting** — tuple of tool names to suppress from
  `tools/list` and reject in `tools/call`. Read-only deployments
  typically set `("admin.destroy", "admin.bulk_update", "admin.set_password")`.
- **`manage.py check` integration.** Three hooks: `E001` (rest-api
  missing from `INSTALLED_APPS`), `E002` (`ADMIN_SITE` doesn't
  resolve), `W001` (typo in `DISABLED_TOOLS`).
- **`GET /mcp/` landing.** Content-negotiated — HTML for browsers,
  JSON for `Accept: application/json`. Shows server name, version,
  protocol, tool count, and links to the manifest.
- **`django_admin_mcp_api.bundle_urls`** — opt-in one-include URL conf
  that auto-mounts rest-api alongside MCP under the consumer's prefix.
- **Structured logging at `django_admin_mcp_api.server.views`**
  (`mcp.auth.*`, `mcp.tools_call`, `mcp.tools_call.upstream_error`).
  Bodies are never logged — only `{user, tool, status}`.
- **`docs/tools-reference.md`** — one section per tool with the
  schema, the forwarded rest-api endpoint, and a worked example.
- **`docs/deployment.md`** — WSGI / ASGI, TLS, CORS, rate-limit,
  logging, and health-check recipes.
- **`examples/clients/`** — drop-in Claude Desktop / Cursor / VS Code
  MCP config templates.
- **`examples/headless-client/`** — programmatic-login bootstrap +
  stdlib-only MCP client for scripts / CI / services.
- **README "Why two apps?" callout** + the agent recipe for
  `admin.action` discovery + Custom AdminSite subsection.
- **Auto-create GitHub Releases on tag push.** `publish.yml` extracts
  the CHANGELOG entry, marks pre-releases by version suffix, and
  attaches the wheel + sdist.

### Changed
- **Security: `_dont_enforce_csrf_checks` flag no longer forwarded**
  to the synthetic rest-api request. Latent CSRF-bypass risk closed.
- **Security: `UnknownRestApiPath` and `UnsupportedDispatchMethod`
  now caught** into JSON-RPC `SERVER_ERROR_UPSTREAM` envelopes instead
  of bubbling to Django's 500 handler.

### Notes
First release shipped end-to-end through PyPI Trusted Publishing —
no `.env` token, no manual `poetry publish`. The Trusted Publisher
was registered on PyPI for this project; the workflow's OIDC token
authenticates every future tag push.

Tests: 81 → **96 passing**, 91% → **93% line coverage**.

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
