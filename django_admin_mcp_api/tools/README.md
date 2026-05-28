# `django_admin_mcp_api/tools/`

One module per MCP tool. Each tool is a thin declarative object:

- **name** — the public MCP tool name (e.g. `admin.list`).
- **description** — what the tool does, surfaced to the agent.
- **input_schema** — JSON Schema for the arguments.
- **build_target(arguments)** — translate the arguments into the
  equivalent django-admin-rest-api HTTP shape
  (`DispatchTarget`). This is the *only* code path that runs in this
  package per call.

There is no admin logic here. Permissions, querysets, forms,
serialization — all of that lives in django-admin-rest-api and is
applied when the dispatcher forwards the target.

## Tool ↔ rest-api endpoint mapping

| MCP tool                | rest-api endpoint                                       | HTTP  |
| ----------------------- | ------------------------------------------------------- | ----- |
| `admin.registry`        | `/api/v1/registry/`                                     | GET   |
| `admin.schema`          | `/api/v1/schema/`                                       | GET   |
| `admin.recent_actions`  | `/api/v1/recent-actions/`                               | GET   |
| `admin.list`            | `/api/v1/<app>/<model>/`                                | GET   |
| `admin.retrieve`        | `/api/v1/<app>/<model>/<pk>/`                           | GET   |
| `admin.add_form`        | `/api/v1/<app>/<model>/add/`                            | GET   |
| `admin.create`          | `/api/v1/<app>/<model>/`                                | POST  |
| `admin.update`          | `/api/v1/<app>/<model>/<pk>/`                           | PATCH |
| `admin.destroy`         | `/api/v1/<app>/<model>/<pk>/`                           | DELETE|
| `admin.bulk_update`     | `/api/v1/<app>/<model>/bulk/`                           | PATCH |
| `admin.autocomplete`    | `/api/v1/<app>/<model>/autocomplete/`                   | GET   |
| `admin.action`          | `/api/v1/<app>/<model>/actions/<action_name>/`          | POST  |
| `admin.history`         | `/api/v1/<app>/<model>/<pk>/history/`                   | GET   |
| `admin.delete_preview`  | `/api/v1/<app>/<model>/<pk>/delete-preview/`            | GET   |
| `admin.set_password`    | `/api/v1/<app>/<model>/<pk>/password/`                  | POST  |
| `admin.panel`           | `/api/v1/<app>/<model>/<pk>/panel/<panel_name>/`        | GET   |

## What must NOT live here

- Database queries.
- Permission checks.
- Field serialization.
- Any tool that does not have a corresponding rest-api endpoint. If you
  need a new behaviour, add it to django-admin-rest-api first, then add
  the matching tool here.
