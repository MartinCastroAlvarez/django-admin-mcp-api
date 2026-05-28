# django-admin-mcp-api

[![PyPI version](https://img.shields.io/pypi/v/django-admin-mcp-api.svg)](https://pypi.org/project/django-admin-mcp-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-admin-mcp-api.svg)](https://pypi.org/project/django-admin-mcp-api/)
[![Django versions](https://img.shields.io/badge/django-5.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-blue.svg)](https://pypi.org/project/django-admin-mcp-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/MartinCastroAlvarez/django-admin-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/MartinCastroAlvarez/django-admin-mcp/actions/workflows/ci.yml)

> **An MCP (Model Context Protocol) adapter for the Django admin.**
> Lets AI agents reach every operation of your `ModelAdmin` — list, retrieve,
> create, update, delete, run admin actions, autocomplete — through the
> standard MCP wire protocol, with the **same** authentication, permissions,
> and validation as the rest of your admin.

`django-admin-mcp-api` is a thin **wire-protocol adapter** sitting on top of
[`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).
It introduces **no new functionality, no parallel permission system, no extra
validation, and no new business logic** — it is the MCP face on the REST API
your admin already speaks.

---

## The three-repo family

`django-admin-mcp-api` is one of three sibling packages that share the same
admin core. Each one exposes the same surface in a different protocol:

| Repo                                                                                  | Protocol         | PyPI                                                      | Status                |
| ------------------------------------------------------------------------------------- | ---------------- | --------------------------------------------------------- | --------------------- |
| [`django-admin-react`](https://github.com/MartinCastroAlvarez/django-admin-react)     | React SPA over HTTP/JSON | [`django-admin-react`](https://pypi.org/project/django-admin-react/)             | Published             |
| [`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api) | HTTP REST/JSON   | _to be published_                                          | Extraction in progress |
| **`django-admin-mcp`** (this repo)                                                    | **MCP (JSON-RPC)** | [`django-admin-mcp-api`](https://pypi.org/project/django-admin-mcp-api/)         | Pre-alpha (this is the v0)             |

All three reuse your existing `ModelAdmin` as the **only** source of truth
for querysets, permissions, forms, and serialization.

---

## Why this exists

LLM agents speak the [Model Context Protocol](https://modelcontextprotocol.io)
natively. Today they cannot reach a Django admin without a custom integration
per project. `django-admin-mcp-api` gives them a standard MCP endpoint that
exposes every admin endpoint as a tool — `admin.list`, `admin.retrieve`,
`admin.create`, `admin.update`, `admin.destroy`, `admin.action`,
`admin.autocomplete`, `admin.history`, and ten more — using the same
authentication mechanism, permissions, validation, and serialization that the
REST API and the React admin already use.

What this package is **not**:

- ❌ A new permission system.
- ❌ A new ORM layer.
- ❌ A bypass for CSRF or session auth.
- ❌ An owner of any admin behaviour.

If a behaviour is not in `django-admin-rest-api`, it is not in
`django-admin-mcp-api`. Period.

---

## Install (plug-and-play)

```bash
pip install django-admin-mcp-api
```

In `settings.py`:

```python
INSTALLED_APPS = [
    # ...your apps...
    "django.contrib.admin",
    "django_admin_rest_api",   # the REST layer (mandatory at v0.1+)
    "django_admin_mcp_api",    # the MCP adapter
]
```

In your root `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("django_admin_rest_api.urls")),   # REST
    path("mcp/",     include("django_admin_mcp_api.urls")),    # MCP (this package)
]
```

That is the entire integration. There is nothing else to configure.

---

## What you get

Two endpoints, both gated by the **same** auth your admin already has
(Django session + CSRF + `AdminSite.has_permission`):

- `POST /mcp/` — the MCP JSON-RPC 2.0 entry point. Speaks `initialize`,
  `tools/list`, and `tools/call`.
- `GET /mcp/manifest/` — a read-only catalogue (server info + every tool's
  name, description, JSON-Schema) for humans and dashboards.

### The tool catalogue

| MCP tool                | What it does                                                          | rest-api endpoint                                       |
| ----------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| `admin.registry`        | List every model the user can see                                     | `GET /api/v1/registry/`                                 |
| `admin.schema`          | The full admin metadata schema                                        | `GET /api/v1/schema/`                                   |
| `admin.recent_actions`  | The user's own LogEntry feed                                          | `GET /api/v1/recent-actions/`                           |
| `admin.list`            | A page of list-view results                                           | `GET /api/v1/<app>/<model>/`                            |
| `admin.retrieve`        | A single object's detail view                                         | `GET /api/v1/<app>/<model>/<pk>/`                       |
| `admin.add_form`        | Create-page field descriptors                                         | `GET /api/v1/<app>/<model>/add/`                        |
| `admin.create`          | Create one object                                                     | `POST /api/v1/<app>/<model>/`                           |
| `admin.update`          | Partial-update one object                                             | `PATCH /api/v1/<app>/<model>/<pk>/`                     |
| `admin.destroy`         | Delete one object                                                     | `DELETE /api/v1/<app>/<model>/<pk>/`                    |
| `admin.bulk_update`     | Apply the same patch to many objects                                  | `PATCH /api/v1/<app>/<model>/bulk/`                     |
| `admin.autocomplete`    | Autocomplete a related model                                          | `GET /api/v1/<app>/<model>/autocomplete/`               |
| `admin.action`          | Run a `ModelAdmin.actions` action                                     | `POST /api/v1/<app>/<model>/actions/<name>/`            |
| `admin.history`         | One object's LogEntry timeline                                        | `GET /api/v1/<app>/<model>/<pk>/history/`               |
| `admin.delete_preview`  | Cascade preview before a destroy                                      | `GET /api/v1/<app>/<model>/<pk>/delete-preview/`        |
| `admin.set_password`    | Set/change a user-like password                                       | `POST /api/v1/<app>/<model>/<pk>/password/`             |
| `admin.panel`           | A custom panel registered on the ModelAdmin                           | `GET /api/v1/<app>/<model>/<pk>/panel/<name>/`          |

Every tool is a 1:1 mirror of a `django-admin-rest-api` endpoint.

---

## Quick tour

### Discover the catalogue

```console
$ curl -s http://localhost:8000/mcp/manifest/ \
    --cookie "sessionid=…" | jq '.tools[].name'
"admin.registry"
"admin.schema"
"admin.recent_actions"
"admin.list"
...
```

### Initialize an MCP session

```console
$ curl -s http://localhost:8000/mcp/ \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $(grep csrftoken ~/.cookies)" \
    --cookie "sessionid=…" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | jq .
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": { "name": "django-admin", "version": "0.1.0" },
    "capabilities": { "tools": { "listChanged": false } }
  }
}
```

### Call a tool

```console
$ curl -s http://localhost:8000/mcp/ \
    -H "Content-Type: application/json" -H "X-CSRFToken: …" \
    --cookie "sessionid=…" \
    -d '{
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "admin.list",
        "arguments": {"app_label": "auth", "model_name": "user", "page": 1}
      }
    }' | jq .
```

The response is the rest-api response, wrapped in an MCP `content` envelope.

---

## See it work

Captured against the [`examples/quickstart/`](examples/quickstart/)
demo project — a fresh `pip install django-admin-mcp-api` and
`runserver`. No mocks, no stubs:

```text
$ python smoke.py
============================================================
 POST /mcp/  method=initialize
============================================================
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": { "name": "django-admin", "version": "0.1.0a0" },
    "capabilities": { "tools": { "listChanged": false } }
  }
}

============================================================
 POST /mcp/  method=tools/call  name=admin.registry
============================================================
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "json", "json": {
      "mount": "/",
      "user":  { "id": 1, "username": "admin", "is_staff": true, ... },
      "apps":  [
        { "app_label": "auth", "name": "Authentication and Authorization",
          "models": [
            { "model_name": "group", "verbose_name": "group",
              "permissions": { "view": true, "add": true,
                               "change": true, "delete": true } },
            { "model_name": "user",  "verbose_name": "user",
              "permissions": { "view": true, "add": true,
                               "change": true, "delete": true } }
          ] }
      ]
    } }],
    "isError": false,
    "status":  200
  }
}
```

The permissions block comes straight from `ModelAdmin.has_*_permission` —
the MCP layer doesn't decide a thing about authorization. PNG screenshots
of Claude Desktop driving the same endpoint are tracked in
[#2](https://github.com/MartinCastroAlvarez/django-admin-mcp/issues/2).

---

## Security

Defaults are deliberately strict and match the rest of the family:

- **Staff-only.** Anonymous requests get `401`, non-staff get `403`. The
  staff gate is the *minimum* — the real permission check happens inside
  `django-admin-rest-api` per tool.
- **CSRF always on.** No view in this package is `@csrf_exempt`. The
  pre-commit hook fails any PR that introduces one.
- **No new permission code.** This package never calls `user.has_perm` or
  `objects.all()` — those checks belong to rest-api.
- **No secrets in code or commits.** `gitleaks` + a pygrep hook block any
  token-shaped string from reaching the index.

See [SECURITY.md](SECURITY.md) for the full set of invariants and how to
report a vulnerability.

---

## Status

| Component                                  | Status                                       |
| ------------------------------------------ | -------------------------------------------- |
| MCP wire protocol (initialize, tools/list, tools/call) | ✅ implemented + tested            |
| 16-tool catalogue                          | ✅ implemented + tested                       |
| Default dispatcher                         | ⏳ placeholder until `django-admin-rest-api` is on PyPI |
| PyPI release                               | ⏳ blocked on `django-admin-rest-api`           |

Tracked in the [GitHub project board](https://github.com/MartinCastroAlvarez/django-admin-mcp/projects).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The TL;DR:

```bash
poetry install
poetry run pytest
poetry run bash scripts/lint.sh
```

PRs go through review per [CLAUDE.md](CLAUDE.md). The same linters,
formatters, and security gates as `django-admin-react` run on every PR.

---

## License

MIT — see [LICENSE](LICENSE).
