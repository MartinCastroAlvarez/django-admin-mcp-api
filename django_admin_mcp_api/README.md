# `django_admin_mcp_api/`

The shipped package. A Django app + an MCP wire-protocol adapter over
[`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).

## What lives here

| File / dir            | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `__init__.py`         | Version + default app config pointer.                          |
| `apps.py`             | `DjangoAdminMcpApiConfig` — registered via `INSTALLED_APPS`.   |
| `conf.py`             | The one place to read `DJANGO_ADMIN_MCP_API` settings from.    |
| `urls.py`             | Two URLs: `POST /` (MCP JSON-RPC) and `GET /manifest/`.         |
| [`server/`](server/)  | The wire layer (views, JSON-RPC, dispatcher, manifest).         |
| [`tools/`](tools/)    | One module per MCP tool (16 tools total).                        |

## What must NOT live here

- Database queries.
- Permission checks (the staff gate in `server/views.py` is the only
  exception, and it is a baseline — the real check is in rest-api).
- Serialization.
- Any new admin behaviour.

## Pointers

- [`../README.md`](../README.md) — user-facing docs.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — request flow + dispatcher seam.
- [`../SECURITY.md`](../SECURITY.md) — security invariants.
- [`../CLAUDE.md`](../CLAUDE.md) — agent contract.
