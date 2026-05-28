# `tests/test_project/`

> Minimal Django project the test client drives. Mounts
> `django_admin_mcp_api` at `/mcp/` and points
> `DJANGO_ADMIN_MCP_API.DISPATCHER_FACTORY` at the `FakeDispatcher` in
> [`../helpers.py`](../helpers.py) — so wire-level tests can assert
> the exact HTTP shape forwarded to rest-api without standing rest-api up.

## In this folder

| File                       | Purpose                                                |
| -------------------------- | ------------------------------------------------------ |
| [`settings.py`](settings.py) | Django settings (in-memory SQLite, no real models).     |
| [`urls.py`](urls.py)         | `path("mcp/", include("django_admin_mcp_api.urls"))`.   |

## What does NOT belong here

- **Example admin models.** The MCP wire is exercised against the fake dispatcher, which doesn't query the database. If a future test needs real models, it goes in a sibling `tests/example_models/` Django app instead of polluting this minimal project.
- **Production-shaped settings.** This is a *test* harness — `SECRET_KEY` is a constant, `DEBUG` is off, `ALLOWED_HOSTS` is `["*"]`. Do not copy.

## See also

- [`../README.md`](../README.md) — running the suite.
- [`../../docs/api-contract.md`](../../docs/api-contract.md) — the wire contract the tests assert against.
