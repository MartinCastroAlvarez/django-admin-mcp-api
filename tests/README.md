# `tests/`

Pytest suite. Runs against a minimal Django project in
[`test_project/`](test_project/) configured with `DJANGO_ADMIN_MCP_API.DISPATCHER_FACTORY`
pointing at [`tests/helpers.py::make_fake_dispatcher`](helpers.py). That
lets us assert the exact HTTP shape we would forward to
`django-admin-rest-api` without needing rest-api itself.

## Layout

| File / dir              | Purpose                                                   |
| ----------------------- | --------------------------------------------------------- |
| `test_project/`         | A throwaway Django project for the test client.            |
| `conftest.py`           | Shared fixtures: `staff_client`, `anon_client`, etc.       |
| `helpers.py`            | `FakeDispatcher` + JSON-RPC body helpers.                  |
| `test_apps.py`          | App config wiring.                                         |
| `test_conf.py`          | `conf.get` defaults / overrides / unknown-key errors.      |
| `test_jsonrpc.py`       | Envelope parsing happy + error paths.                      |
| `test_manifest.py`      | The tool catalogue + `initialize` shape.                   |
| `test_dispatch.py`      | `Dispatcher` resolution + `PendingDispatcher` placeholder. |
| `test_tools.py`         | Per-tool `build_target` translation table.                 |
| `test_views.py`         | HTTP-level: auth gates, JSON-RPC routing, error mapping.   |
| `test_security.py`      | Security invariants (no `csrf_exempt`, no `objects.all`, no token strings). |

## Running

```bash
poetry run pytest                          # full suite
poetry run pytest tests/test_views.py       # one file
poetry run pytest -k tools                  # by keyword
poetry run pytest --no-cov                  # skip coverage for speed
```

Coverage threshold lives in `pyproject.toml` under `[tool.coverage.report]`.
The suite must pass cleanly on every PR — the CI workflow enforces it.

## Adding a new tool

1. Add the module in `django_admin_mcp_api/tools/<name>.py`.
2. Register it in `django_admin_mcp_api/tools/__init__.py::_TOOLS`.
3. Add a case to `tests/test_tools.py::CASES` describing the exact HTTP
   shape the tool forwards.
4. Add the tool to the mapping table in
   `django_admin_mcp_api/tools/README.md` and the README.md table at
   the repo root.
5. Bump the count in `tests/test_views.py::test_tools_list_returns_all_tools`.

That is the whole checklist.
