# `tests/test_project/`

A minimal Django project used by the test client. Mounts
`django_admin_mcp_api` at `/mcp/` and configures
`DJANGO_ADMIN_MCP_API["DISPATCHER_FACTORY"]` to use the FakeDispatcher
from [`../helpers.py`](../helpers.py).

## What lives here

| File           | Purpose                                                |
| -------------- | ------------------------------------------------------ |
| `settings.py`  | Django settings (in-memory SQLite, no real models).     |
| `urls.py`      | `path("mcp/", include("django_admin_mcp_api.urls"))`.   |

## What does NOT live here

- Example admin models. The MCP wire is exercised against the fake
  dispatcher, which doesn't query the DB. If a future test needs real
  models, it goes in a sibling `tests/example_models/` Django app
  instead of polluting this minimal project.
