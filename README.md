# django-admin-mcp-api

> An MCP server for the Django admin — **same permissions, same `ModelAdmin`, no new features.**

[![PyPI version](https://img.shields.io/pypi/v/django-admin-mcp-api.svg)](https://pypi.org/project/django-admin-mcp-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-admin-mcp-api.svg)](https://pypi.org/project/django-admin-mcp-api/)
[![Django versions](https://img.shields.io/badge/Django-5.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-44b78b.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![MCP protocol](https://img.shields.io/badge/MCP-2024--11--05-orange.svg)](https://modelcontextprotocol.io)
[![Wire contract: stable](https://img.shields.io/badge/wire%20contract-stable-44b78b.svg)](CHANGELOG.md)
[![Latest on Django Packages](https://img.shields.io/badge/Django%20Packages-django--admin--mcp--api-8c3c26.svg)](https://djangopackages.org/packages/p/django-admin-mcp-api/)

`django-admin-mcp-api` lets AI agents — Claude, Cursor, anything that
speaks the [Model Context Protocol](https://modelcontextprotocol.io) —
drive your Django admin. Every `ModelAdmin` you've already registered
on `django.contrib.admin.site` becomes an MCP tool, with the **same**
permissions, the **same** form validation, and the **same** session
auth as the HTML admin.

It is the MCP face on top of
[`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).
No parallel permission system. No parallel form layer. No features the
Django admin doesn't already have.

| Project | Role | PyPI |
| --- | --- | --- |
| 🟦 [`django-admin-react`](https://github.com/MartinCastroAlvarez/django-admin-react) | React single-page admin frontend | [`django-admin-react`](https://pypi.org/project/django-admin-react/) |
| 🟩 [`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api) | JSON REST API over `ModelAdmin` | [`django-admin-rest-api`](https://pypi.org/project/django-admin-rest-api/) |
| 🟪 **`django-admin-mcp-api`** *(this repo)* | MCP server exposing the same API to LLMs | [`django-admin-mcp-api`](https://pypi.org/project/django-admin-mcp-api/) |

---

## ✨ The one design principle

**This package adds no new behavior. It is an MCP wire adapter.**

Every one of these is owned by your existing Django setup — not by
this library:

- 🔐 **Authentication** — Django's session + login. The MCP endpoint
  enforces the same `is_active` + `is_staff` + `AdminSite.has_permission`
  gate the HTML admin uses. No tokens, no custom backends, no JWTs.
- 🛡️ **Authorization** — every tool delegates to the matching
  `ModelAdmin.has_view_permission` / `has_add_permission` /
  `has_change_permission` / `has_delete_permission` via
  django-admin-rest-api. If your admin says no, the tool returns the
  upstream 403.
- 📋 **Field validation** — `admin.create` / `admin.update` route the
  payload through the same `ModelForm` Django would render in the HTML
  admin, plus a JSON Schema check on the wire so malformed calls fail
  fast with a json-pointer path of the offending field.
- ⚙️ **Actions** — `admin.action` runs the same action callables
  registered on `ModelAdmin.actions`. Your code runs unmodified.
  Each action's descriptor carries a `target` (`batch` or `detail`),
  derived by rest-api from the callable's signature: signatures
  ending in `queryset` are batch (changelist shape), signatures
  ending in `obj_id`/`pk`/`id` are detail (single-object shape).
  Agents pass the right number of pks for the action's target.
- 🔎 **Search & filters** — `admin.list` uses
  `ModelAdmin.get_search_results` and `list_filter`. No parallel
  implementation.
- 📜 **Audit log** — writes go through Django's `LogEntry`, surfaced
  by `admin.history` and `admin.recent_actions`.
- 🌐 **CSRF & sessions** — Django's middleware. Nothing is
  `@csrf_exempt`.

If a behavior isn't in the HTML admin, it isn't here. If it is in the
HTML admin, this library exposes it over MCP.

---

## 🚀 Plug-and-play install

```bash
pip install django-admin-mcp-api
```

Two changes to your project:

```python
# settings.py
INSTALLED_APPS = [
    # ... your existing apps ...
    "django.contrib.admin",
    "django_admin_rest_api",         # ← the REST surface (mandatory)
    "django_admin_mcp_api",          # ← the MCP adapter
]
```

```python
# urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/",  admin.site.urls),
    path("",        include("django_admin_rest_api.urls")),    # REST
    path("mcp/",    include("django_admin_mcp_api.urls")),     # MCP
]
```

That's it. Your admin now answers JSON-RPC at `POST /mcp/`, with the
same session cookie and CSRF token your HTML admin already uses.

---

## 📡 The 16 tools

Each MCP tool is a 1:1 mirror of a `django-admin-rest-api` endpoint —
that's the whole design.

| MCP tool                | What it does                                       | rest-api endpoint                                       |
| ----------------------- | -------------------------------------------------- | ------------------------------------------------------- |
| `admin.registry`        | List every model the user can see                  | `GET /api/v1/registry/`                                 |
| `admin.schema`          | Full admin metadata schema                         | `GET /api/v1/schema/`                                   |
| `admin.recent_actions`  | The user's own `LogEntry` feed                     | `GET /api/v1/recent-actions/`                           |
| `admin.list`            | A page of list-view results                        | `GET /api/v1/<app>/<model>/`                            |
| `admin.retrieve`        | A single object's detail view                      | `GET /api/v1/<app>/<model>/<pk>/`                       |
| `admin.add_form`        | Create-page field descriptors                      | `GET /api/v1/<app>/<model>/add/`                        |
| `admin.create`          | Create one object                                  | `POST /api/v1/<app>/<model>/`                           |
| `admin.update`          | Partial-update one object                          | `PATCH /api/v1/<app>/<model>/<pk>/`                     |
| `admin.destroy`         | Delete one object                                  | `DELETE /api/v1/<app>/<model>/<pk>/`                    |
| `admin.bulk_update`     | Apply the same patch to many objects               | `PATCH /api/v1/<app>/<model>/bulk/`                     |
| `admin.autocomplete`    | Autocomplete a related model                       | `GET /api/v1/<app>/<model>/autocomplete/`               |
| `admin.action`          | Run a `ModelAdmin.actions` action (batch or detail) | `POST /api/v1/<app>/<model>/actions/<name>/`            |
| `admin.history`         | One object's `LogEntry` timeline                   | `GET /api/v1/<app>/<model>/<pk>/history/`               |
| `admin.delete_preview`  | Cascade preview before a destroy                   | `GET /api/v1/<app>/<model>/<pk>/delete-preview/`        |
| `admin.set_password`    | Set/change a user-like password                    | `POST /api/v1/<app>/<model>/<pk>/password/`             |
| `admin.panel`           | A custom panel registered on the `ModelAdmin`      | `GET /api/v1/<app>/<model>/<pk>/panel/<name>/`          |

Two endpoints expose them — both gated by the same auth your admin
already has:

- `POST /mcp/` — the MCP JSON-RPC 2.0 entry point. Speaks `initialize`,
  `tools/list`, `tools/call`. Full wire spec in [`docs/api-contract.md`](docs/api-contract.md).
- `GET /mcp/manifest/` — a read-only catalogue (server info + every
  tool's name, description, JSON Schema) for humans and dashboards.

---

## 📸 See it run

Captured against the [`examples/quickstart/`](examples/quickstart/)
demo — fresh `pip install`, `runserver`, `python smoke.py`. No mocks.

```jsonc
// POST /mcp/  method=initialize
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo":      { "name": "django-admin", "version": "1.0.2" },
    "capabilities":    { "tools": { "listChanged": false } }
  }
}

// POST /mcp/  method=tools/call  name=admin.registry
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "content": [{ "type": "json", "json": {
      "user":  { "id": 1, "username": "admin", "is_staff": true },
      "apps":  [
        { "app_label": "auth",
          "models": [
            { "model_name": "group",
              "permissions": { "view": true, "add": true, "change": true, "delete": true } },
            { "model_name": "user",
              "permissions": { "view": true, "add": true, "change": true, "delete": true } }
          ] }
      ]
    } }],
    "isError": false,
    "status":  200
  }
}
```

The `permissions` block above comes straight from
`ModelAdmin.has_*_permission` — the MCP layer doesn't decide a thing
about authorization. That's the prime directive.

---

## ⚙️ Configuration

All settings live under a single optional dict — defaults are sane,
so most projects need no entry at all.

```python
# settings.py (all keys optional)
DJANGO_ADMIN_MCP_API = {
    # MCP protocol version advertised in the `initialize` result.
    "PROTOCOL_VERSION":  "2024-11-05",

    # The `serverInfo.name` field. Useful per-environment labelling.
    "SERVER_NAME":       "django-admin",

    # The `serverInfo.version`. None → falls back to the package version.
    "SERVER_VERSION":    None,

    # Dotted path to the AdminSite the package introspects.
    "ADMIN_SITE":        "django.contrib.admin.site",

    # Dotted path to a zero-arg callable returning a Dispatcher.
    # None uses the built-in RestApiDispatcher.
    "DISPATCHER_FACTORY": None,
}
```

A copy-paste-ready block lives at the bottom of
[`examples/quickstart/myproject/settings.py`](examples/quickstart/myproject/settings.py).

---

## 🔒 Security

- The MCP endpoint is **not** a parallel auth surface. It refuses any
  caller the HTML admin would refuse, with the same gate.
- Anonymous → `401`. Authenticated but non-staff → `403`. CSRF
  missing on `POST` → Django's middleware 403.
- Every `tools/call` is validated against the tool's JSON Schema
  *before* it reaches the database. Schema violations return
  `INVALID_PARAMS` with the json-pointer path of the failing field.
- The dispatcher carries the caller's session / user / cookies / CSRF
  state to django-admin-rest-api untouched. Per-tool permission is
  enforced inside rest-api by the relevant `ModelAdmin.has_*_permission`.
- CSRF is enforced everywhere. No view in this package is
  `@csrf_exempt` — a pre-commit hook and a test assert this.
- No token-shaped string is permitted in the repo (gitleaks + a
  pygrep hook + `tests/test_security.py`).

Threat model: [`docs/threat-model.md`](docs/threat-model.md). Report
a vulnerability privately
[here](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/security/advisories/new).

---

## 🧪 Local development

```bash
git clone https://github.com/MartinCastroAlvarez/django-admin-mcp-api
cd django-admin-mcp-api
poetry install
poetry run pytest
poetry run bash scripts/lint.sh
poetry run bash scripts/audit-deps.sh
```

77 tests, 91% line coverage, including a real end-to-end run through
`django-admin-rest-api`. CI runs the same suite across Python
3.10–3.13 × Django 5.0/5.1/5.2/6.0 on every PR.

---

## 🤝 Contributing

Issues, PRs, and the roadmap are on GitHub:

- 📋 [Issues](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/issues)
- 🗺️ [Project board](https://github.com/users/MartinCastroAlvarez/projects/4)
- 📖 [`CONTRIBUTING.md`](CONTRIBUTING.md) — house rules
- 🤖 [`CLAUDE.md`](CLAUDE.md) — agent contract

The lint + security gate is the same set the upstream
`django-admin-rest-api` and `django-admin-react` repos use:
**ruff, black, isort, flake8, pylint, mypy, bandit, pip-audit,
gitleaks.** Every change must pass all of them before merge.

---

## 📜 License

MIT. See [LICENSE](LICENSE).
