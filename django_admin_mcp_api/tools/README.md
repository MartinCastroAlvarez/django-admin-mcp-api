# `django_admin_mcp_api/tools/`

> One module per MCP tool. Each tool is a tiny declarative object — a
> name, a description, a JSON Schema, and one function that translates
> arguments into the HTTP shape rest-api expects.

## Tool ↔ rest-api endpoint mapping

| MCP tool                | rest-api endpoint                                       | Method |
| ----------------------- | ------------------------------------------------------- | ------ |
| `admin.registry`        | `/api/v1/registry/`                                     | GET    |
| `admin.schema`          | `/api/v1/schema/`                                       | GET    |
| `admin.recent_actions`  | `/api/v1/recent-actions/`                               | GET    |
| `admin.list`            | `/api/v1/<app>/<model>/`                                | GET    |
| `admin.retrieve`        | `/api/v1/<app>/<model>/<pk>/`                           | GET    |
| `admin.add_form`        | `/api/v1/<app>/<model>/add/`                            | GET    |
| `admin.create`          | `/api/v1/<app>/<model>/`                                | POST   |
| `admin.update`          | `/api/v1/<app>/<model>/<pk>/`                           | PATCH  |
| `admin.destroy`         | `/api/v1/<app>/<model>/<pk>/`                           | DELETE |
| `admin.bulk_update`     | `/api/v1/<app>/<model>/bulk/`                           | PATCH  |
| `admin.autocomplete`    | `/api/v1/<app>/<model>/autocomplete/`                   | GET    |
| `admin.action`          | `/api/v1/<app>/<model>/actions/<action_name>/`          | POST   |
| `admin.history`         | `/api/v1/<app>/<model>/<pk>/history/`                   | GET    |
| `admin.delete_preview`  | `/api/v1/<app>/<model>/<pk>/delete-preview/`            | GET    |
| `admin.set_password`    | `/api/v1/<app>/<model>/<pk>/password/`                  | POST   |
| `admin.panel`           | `/api/v1/<app>/<model>/<pk>/panel/<panel_name>/`        | GET    |

## What every tool module looks like

A `name`, `description`, `inputSchema`, and a `build_target(arguments)`
function. That is the whole interface — no execution, no permission
check, no database query. Execution happens in
[`../server/dispatch.py`](../server/dispatch.py).

## What does NOT belong here

- **Execution.** Tools build a `DispatchTarget`; the dispatcher executes it.
- **Database queries.**
- **Permission checks.**
- **Field serialization.**
- **Any tool that does not have a corresponding rest-api endpoint.** If you need a new behaviour, add it to rest-api first, then add the matching tool here.

## Adding a new tool

1. Add the module in [`./<name>.py`](./).
2. Register it in [`__init__.py::_TOOLS`](__init__.py).
3. Add a case to [`../../tests/test_tools.py::CASES`](../../tests/test_tools.py).
4. Add the tool to the mapping table above and the README at the repo root.
5. Bump the count in [`../../tests/test_views.py::test_tools_list_returns_all_tools`](../../tests/test_views.py).

## See also

- [`../../docs/api-contract.md`](../../docs/api-contract.md) — JSON Schema dialect and stability policy.
- [`base.py`](base.py) — the `Tool` dataclass + shared schema fragments.
