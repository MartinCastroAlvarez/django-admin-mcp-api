# `tests/`

> The pytest suite — 77 tests, 91% line coverage, including a real
> end-to-end run against `django-admin-rest-api`.

## In this folder

| File / dir                               | Purpose                                                   |
| ---------------------------------------- | --------------------------------------------------------- |
| [`test_project/`](test_project/)         | A throwaway Django project that the test client drives.    |
| [`conftest.py`](conftest.py)             | Shared fixtures: `staff_client`, `anon_client`, etc.       |
| [`helpers.py`](helpers.py)               | `FakeDispatcher` (echo-back) and JSON-RPC body helpers.    |
| [`test_apps.py`](test_apps.py)           | App config wiring.                                         |
| [`test_conf.py`](test_conf.py)           | `conf.get` defaults / overrides / unknown-key errors.      |
| [`test_jsonrpc.py`](test_jsonrpc.py)     | Envelope parsing — happy + error paths.                    |
| [`test_manifest.py`](test_manifest.py)   | The tool catalogue + `initialize` shape.                   |
| [`test_dispatch.py`](test_dispatch.py)   | `Dispatcher` resolution + `RestApiDispatcher` defaults.    |
| [`test_tools.py`](test_tools.py)         | Per-tool `build_target` translation table.                 |
| [`test_views.py`](test_views.py)         | HTTP-level: auth gates, JSON-RPC routing, error mapping.   |
| [`test_integration.py`](test_integration.py) | End-to-end through the real rest-api view set.         |
| [`test_security.py`](test_security.py)   | Security invariants — no `csrf_exempt`, no `objects.all`, no token strings. |

## Running

```bash
poetry run pytest                          # full suite
poetry run pytest tests/test_views.py       # one file
poetry run pytest -k tools                  # by keyword
poetry run pytest --no-cov                  # skip coverage for speed
```

The coverage threshold lives in `pyproject.toml`; CI enforces it on every PR.

## Adding tests for a new tool

1. Add a case to [`test_tools.py::CASES`](test_tools.py) describing the exact HTTP shape the tool forwards.
2. Bump the count in [`test_views.py::test_tools_list_returns_all_tools`](test_views.py).
3. Add an integration assertion in [`test_integration.py`](test_integration.py) if the tool exercises a new rest-api code path.

## See also

- [`../django_admin_mcp_api/tools/README.md`](../django_admin_mcp_api/tools/README.md) — tool authoring checklist.
- [`../docs/api-contract.md`](../docs/api-contract.md) — the wire contract.
