<h1 align="center">django-admin-mcp-api</h1>

<p align="center">
  <strong>The Model Context Protocol adapter for the Django admin.</strong><br/>
  Let AI agents drive your <code>ModelAdmin</code> — with your existing auth, permissions, and validation.
</p>

<p align="center">
  <a href="https://pypi.org/project/django-admin-mcp-api/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/django-admin-mcp-api.svg?color=2b7"></a>
  <a href="https://pypi.org/project/django-admin-mcp-api/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/django-admin-mcp-api.svg"></a>
  <img alt="Django 5.0 – 6.0" src="https://img.shields.io/badge/django-5.0%20%E2%80%93%206.0-blue.svg">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://github.com/MartinCastroAlvarez/django-admin-mcp-api/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/MartinCastroAlvarez/django-admin-mcp-api/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://modelcontextprotocol.io"><img alt="MCP 2024-11-05" src="https://img.shields.io/badge/MCP-2024--11--05-orange.svg"></a>
</p>

---

## Install in 30 seconds

```bash
pip install django-admin-mcp-api
```

```python
# settings.py
INSTALLED_APPS += [
    "django_admin_rest_api",
    "django_admin_mcp_api",
]
```

```python
# urls.py
urlpatterns = [
    path("admin/",  admin.site.urls),
    path("",        include("django_admin_rest_api.urls")),  # REST
    path("mcp/",    include("django_admin_mcp_api.urls")),   # MCP
]
```

Your admin now answers JSON-RPC at `POST /mcp/`. Same session, same CSRF,
same permissions. Agents can list, retrieve, create, update, destroy,
run actions, autocomplete, browse history, and more — through one
endpoint your `ModelAdmin` already controls.

---

## Why use it

- **Plug-and-play.** Three lines in `settings.py`, one `include()` in `urls.py`. Nothing else to configure.
- **Same admin, new surface.** Reuses your `ModelAdmin` as the only source of truth for permissions, querysets, forms, and serialization. The MCP layer adds **zero** new functionality.
- **Auth that already works.** Django session + CSRF + `AdminSite.has_permission`. No tokens, no parallel permission system, no surprises.
- **Schema-validated.** Every `tools/call` is validated against the tool's JSON Schema before it reaches your database. Malformed calls fail fast with a json-pointer path of the offending field.
- **Stable contract.** Wire shape is semver-protected ([`docs/api-contract.md`](docs/api-contract.md) §7). Backward-compatible additions only until v2.
- **74 tests, 91% coverage.** Includes end-to-end integration against the real REST API.

---

## How it fits

`django-admin-mcp-api` is one of three sibling packages that share the
same admin core. Pick the protocol that fits your client:

| Package | Protocol | PyPI | When to use it |
| --- | --- | --- | --- |
| [`django-admin-react`](https://github.com/MartinCastroAlvarez/django-admin-react) | React SPA over HTTP/JSON | [`django-admin-react`](https://pypi.org/project/django-admin-react/) | A humans-and-mice frontend that replaces the HTML admin. |
| [`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api) | HTTP REST/JSON | [`django-admin-rest-api`](https://pypi.org/project/django-admin-rest-api/) `1.0.0` | A REST surface for non-Django clients or other UIs. |
| **`django-admin-mcp-api`** *(this repo)* | **MCP JSON-RPC** | [`django-admin-mcp-api`](https://pypi.org/project/django-admin-mcp-api/) `1.0.0` | **An MCP server for AI agents (Claude, Cursor, custom).** |

All three reuse your existing `ModelAdmin`. No fork, no parallel models, no migrations.

---

## The 16 tools

Each MCP tool is a 1:1 mirror of a `django-admin-rest-api` endpoint —
that's the whole design.

| MCP tool                | What it does                                                          | rest-api endpoint                                       |
| ----------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| `admin.registry`        | List every model the user can see                                     | `GET /api/v1/registry/`                                 |
| `admin.schema`          | Full admin metadata schema                                            | `GET /api/v1/schema/`                                   |
| `admin.recent_actions`  | The user's own `LogEntry` feed                                        | `GET /api/v1/recent-actions/`                           |
| `admin.list`            | A page of list-view results                                           | `GET /api/v1/<app>/<model>/`                            |
| `admin.retrieve`        | A single object's detail view                                         | `GET /api/v1/<app>/<model>/<pk>/`                       |
| `admin.add_form`        | Create-page field descriptors                                         | `GET /api/v1/<app>/<model>/add/`                        |
| `admin.create`          | Create one object                                                     | `POST /api/v1/<app>/<model>/`                           |
| `admin.update`          | Partial-update one object                                             | `PATCH /api/v1/<app>/<model>/<pk>/`                     |
| `admin.destroy`         | Delete one object                                                     | `DELETE /api/v1/<app>/<model>/<pk>/`                    |
| `admin.bulk_update`     | Apply the same patch to many objects                                  | `PATCH /api/v1/<app>/<model>/bulk/`                     |
| `admin.autocomplete`    | Autocomplete a related model                                          | `GET /api/v1/<app>/<model>/autocomplete/`               |
| `admin.action`          | Run a `ModelAdmin.actions` action                                     | `POST /api/v1/<app>/<model>/actions/<name>/`            |
| `admin.history`         | One object's `LogEntry` timeline                                      | `GET /api/v1/<app>/<model>/<pk>/history/`               |
| `admin.delete_preview`  | Cascade preview before a destroy                                      | `GET /api/v1/<app>/<model>/<pk>/delete-preview/`        |
| `admin.set_password`    | Set/change a user-like password                                       | `POST /api/v1/<app>/<model>/<pk>/password/`             |
| `admin.panel`           | A custom panel registered on the `ModelAdmin`                         | `GET /api/v1/<app>/<model>/<pk>/panel/<name>/`          |

The wire-format details are in [`docs/api-contract.md`](docs/api-contract.md).

---

## See it run

Captured against the [`examples/quickstart/`](examples/quickstart/)
demo — a fresh `pip install`, `runserver`, and `python smoke.py`. No
mocks. No stubs.

```jsonc
// POST /mcp/  method=initialize
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo":      { "name": "django-admin", "version": "1.0.0" },
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

## What this package will *never* do

- ❌ Add a new permission system.
- ❌ Bypass CSRF or session auth.
- ❌ Add a feature that isn't in `django-admin-rest-api`.
- ❌ Touch the database or call `user.has_perm()`.

If a behaviour isn't in `django-admin-rest-api`, it isn't here. Period.
That rule is enforced by pre-commit hooks **and** the test suite (see
[`tests/test_security.py`](tests/test_security.py)).

---

## Security at a glance

| Default                                            | Status                                          |
| -------------------------------------------------- | ----------------------------------------------- |
| Anonymous request → `401`                          | enforced in `server/views.py::_auth_gate`        |
| Non-staff request → `403`                          | enforced in `server/views.py::_auth_gate`        |
| CSRF on `POST /mcp/`                                | enforced by Django middleware; no view bypasses |
| Schema validation on `tools/call`                  | `jsonschema` Draft 2020-12 against each tool     |
| No `csrf_exempt` / no `objects.all()` / no `user.has_perm` | pygrep pre-commit hooks + test suite     |
| No token-shaped strings in the repo                | `gitleaks` + pygrep + test suite                  |
| Bandit, pip-audit, ruff, black, isort, flake8, pylint, mypy | green on every PR via CI                  |

Full set of invariants: [`SECURITY.md`](SECURITY.md). Threat model:
[`docs/threat-model.md`](docs/threat-model.md). Report a vulnerability
[privately here](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/security/advisories/new).

---

## Contribute

```bash
poetry install
poetry run pytest
poetry run bash scripts/lint.sh
```

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the agent
contract in [CLAUDE.md](CLAUDE.md). The roadmap lives on the
[project board](https://github.com/users/MartinCastroAlvarez/projects/4).

---

## License

[MIT](LICENSE) — © 2026 Martín Castro Alvarez and django-admin-mcp contributors.
