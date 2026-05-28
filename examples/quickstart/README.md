# quickstart

> The smallest possible Django project that wires `django-admin-mcp-api`
> on top of `django-admin-rest-api`. About 30 lines of settings + two
> `include()`s — exactly what you'd add to your own project.

## Run it

```bash
cd examples/quickstart
python -m venv .venv
. .venv/bin/activate
pip install django-admin-mcp-api
python manage.py migrate
python manage.py createsuperuser        # pick a staff user/password
python manage.py runserver
```

Then in another shell:

```bash
python smoke.py --user <USER> --password <PW>
```

`smoke.py` logs in, fetches a CSRF token, then exercises both
`GET /mcp/manifest/` and the JSON-RPC `POST /mcp/` endpoint — the output
is exactly what an MCP agent sees.

## In this folder

| File                                              | What it shows                                                                 |
| ------------------------------------------------- | ----------------------------------------------------------------------------- |
| [`manage.py`](manage.py)                          | Standard Django entry point.                                                  |
| [`myproject/settings.py`](myproject/settings.py)  | Both `django_admin_rest_api` and `django_admin_mcp_api` in `INSTALLED_APPS`. That is the whole install step. |
| [`myproject/urls.py`](myproject/urls.py)          | Two `include(...)` lines mount the REST API at `/` and the MCP endpoint at `/mcp/`. |
| [`smoke.py`](smoke.py)                            | Stdlib-only HTTP driver that logs in and exercises every MCP method end-to-end. |

No custom views, no custom admin code. Everything that worked in your
existing admin keeps working — and now an agent can drive it via MCP.

## See also

- [`../../README.md`](../../README.md) — the upstream README's "See it run" section is captured from `smoke.py` output.
- [`../../docs/api-contract.md`](../../docs/api-contract.md) — the wire contract.
