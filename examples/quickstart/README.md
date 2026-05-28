# quickstart

Smallest possible Django project that wires `django-admin-mcp-api` on
top of `django-admin-rest-api`. It's about 30 lines of settings and
two routes — exactly what you'd add to your own project.

## Run it

```bash
cd examples/quickstart
python -m venv .venv
. .venv/bin/activate
pip install django-admin-mcp-api
python manage.py migrate              # creates a SQLite DB
python manage.py createsuperuser      # pick a staff user/password
python manage.py runserver
```

Then in another shell:

```bash
# Curl the read-only manifest as the staff user.
python smoke.py                       # ships in this folder
```

`smoke.py` logs in, calls `GET /mcp/manifest/`, then runs an MCP
`tools/list` and `tools/call admin.registry`. The output is what an
agent would see.

## What's interesting in the files

- [`settings.py`](myproject/settings.py): both `django_admin_rest_api`
  and `django_admin_mcp_api` are in `INSTALLED_APPS`. That is the
  whole install step.
- [`urls.py`](myproject/urls.py): two `include(...)` lines mount the
  REST API at `/api/v1/` and the MCP endpoint at `/mcp/`. That is the
  whole URL step.
- No custom views, no custom admin code. Everything that worked in your
  existing admin keeps working — and now an agent can drive it via MCP.
