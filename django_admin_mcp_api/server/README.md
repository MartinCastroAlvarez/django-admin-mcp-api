# `django_admin_mcp_api/server/`

The MCP protocol layer. Speaks MCP JSON-RPC and forwards to
**django-admin-rest-api**. Owns *zero* admin logic.

## What lives here

| Module       | Purpose                                                          |
| ------------ | ---------------------------------------------------------------- |
| `views.py`   | `McpEndpointView` (POST → JSON-RPC), `ManifestView` (GET → manifest). |
| `jsonrpc.py` | JSON-RPC 2.0 request/response envelopes + parse helpers.          |
| `errors.py`  | MCP / JSON-RPC error code constants.                              |
| `manifest.py`| Builds the tool catalogue from the `tools/` registry.             |
| `dispatch.py`| The single forward point into django-admin-rest-api.              |

## What must NOT live here

- Database queries.
- Permission checks (Django session + CSRF + `ModelAdmin.has_*_permission`
  are the only auth signals, and they belong to django-admin-rest-api).
- Field serialization. The rest-api response is forwarded as-is in the
  MCP `result.content`.
- Any feature that is not already present in django-admin-rest-api.

If you find yourself reaching for `objects.all()`, `user.has_perm`, or a
serializer, you are in the wrong package — open the change against
django-admin-rest-api instead.

## Pointers

- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — the wire shape.
- [`../../SECURITY.md`](../../SECURITY.md) — the non-negotiables.
- [`../tools/README.md`](../tools/README.md) — the tool catalogue.
