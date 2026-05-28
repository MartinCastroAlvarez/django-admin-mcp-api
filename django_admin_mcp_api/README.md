# `django_admin_mcp_api/`

> The shipped package — a Django app and an MCP wire-protocol adapter over
> [`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).

## In this folder

| File / dir                       | Purpose                                                                  |
| -------------------------------- | ------------------------------------------------------------------------ |
| [`__init__.py`](__init__.py)     | Package version + the default `AppConfig` pointer.                        |
| [`apps.py`](apps.py)             | `DjangoAdminMcpApiConfig` — registered via `INSTALLED_APPS`.              |
| [`conf.py`](conf.py)             | The one place to read `DJANGO_ADMIN_MCP_API` settings from.               |
| [`urls.py`](urls.py)             | Two URLs: `POST /` (MCP JSON-RPC) and `GET /manifest/`.                    |
| [`server/`](server/)             | The wire layer — views, JSON-RPC envelopes, dispatcher, manifest.         |
| [`tools/`](tools/)               | One module per MCP tool (16 tools total).                                  |

## What does NOT belong here

- **Database queries.** Every queryset comes from `ModelAdmin.get_queryset` inside `django-admin-rest-api`.
- **Permission checks** beyond the baseline staff gate in `server/views.py`. The real per-tool authorization lives in rest-api.
- **Field serialization.** Forwarded rest-api responses are passed through; no transformation happens here.
- **Any new admin behaviour.** If a feature isn't in `django-admin-rest-api`, it isn't here.

## See also

- [`../README.md`](../README.md) — user-facing docs.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — request flow + dispatcher seam.
- [`../SECURITY.md`](../SECURITY.md) — non-negotiable security rules.
- [`../docs/api-contract.md`](../docs/api-contract.md) — the MCP wire contract.
