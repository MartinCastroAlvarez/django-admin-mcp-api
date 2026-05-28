# `django_admin_mcp_api/server/`

> The MCP protocol layer — speaks JSON-RPC 2.0 and forwards to
> **django-admin-rest-api**. Owns *zero* admin logic.

## In this folder

| File                                 | Purpose                                                          |
| ------------------------------------ | ---------------------------------------------------------------- |
| [`views.py`](views.py)               | `McpEndpointView` (`POST /`) and `ManifestView` (`GET /manifest/`). The staff-only auth gate lives here. |
| [`jsonrpc.py`](jsonrpc.py)           | JSON-RPC 2.0 request / response envelope helpers + the parse error type. |
| [`errors.py`](errors.py)             | JSON-RPC + MCP error code constants used across the package.      |
| [`manifest.py`](manifest.py)         | Builds the `initialize` result and the `tools/list` catalogue.    |
| [`dispatch.py`](dispatch.py)         | The **single seam** that forwards a `DispatchTarget` to a rest-api view. The only file that changes when integrating against a different rest-api version. |

## What does NOT belong here

- **Database queries** of any kind.
- **Permission checks.** Django session + CSRF + `ModelAdmin.has_*_permission` are the only auth signals, and they belong to rest-api.
- **Field serialization.** The rest-api response is forwarded as-is in the MCP `result.content`.
- **Any feature that is not already present in rest-api.** If you reach for `objects.all()`, `user.has_perm`, or a serializer, you are in the wrong package — open the change against rest-api instead.

## See also

- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — request flow + the dispatcher seam.
- [`../../docs/api-contract.md`](../../docs/api-contract.md) — the wire format spec.
- [`../tools/README.md`](../tools/README.md) — the tool catalogue.
