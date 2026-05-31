# Deployment

Operational guidance for putting `django-admin-mcp-api` in front of
external traffic. The HTML admin is often internal-only; the MCP
endpoint exists to be reached by agents over the network, so the
operational concerns matter more than a typical Django admin
deployment.

Most of what's below is **standard Django operational practice**.
The novelty is the threat profile, not the toolchain. Cross-reference
your existing Django deployment runbook before adopting any specific
recipe here — your platform may already cover some of these.

## WSGI vs ASGI

`django_admin_mcp_api/server/views.py` ships **sync** views. Both
WSGI (gunicorn) and ASGI (uvicorn / daphne / hypercorn) servers run
them correctly; on ASGI, Django wraps sync views in a thread.

No additional configuration is needed for either side. If your
project is async-first and you call the dispatcher from an
`async def` view of your own, wrap the call in `sync_to_async`.

## Reverse proxy + TLS termination

A typical layout: agent → CDN/WAF → nginx/Caddy → gunicorn/uvicorn →
Django. Settings that matter when the MCP endpoint is exposed:

```python
# settings.py
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    "https://mcp.example.com",          # public origin agents hit
    "https://admin.example.com",        # if the HTML admin shares the cookie domain
]
ALLOWED_HOSTS = ["mcp.example.com", "admin.example.com"]

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"         # see Cross-origin below
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False            # MCP clients need to read it to send X-CSRFToken
```

The `CSRF_TRUSTED_ORIGINS` list **must** include the public origin
clients hit. Forgetting it produces 403 on every POST with the
unhelpful "CSRF verification failed" message — same failure mode
as misconfiguring any Django POST endpoint behind a proxy.

## Body-size limit

The MCP endpoint enforces its own envelope cap via
`DJANGO_ADMIN_MCP_API["MAX_REQUEST_BYTES"]` (default 256 KiB).
Pair it with a proxy-side limit so oversized bodies are dropped
before they hit Django:

```nginx
location /mcp/ {
    client_max_body_size 512k;          # twice the MCP cap; gives room for headers
    proxy_pass http://django_upstream;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host  $host;
    proxy_set_header X-Real-IP         $remote_addr;
}
```

For projects that use `admin.bulk_update` with large pk arrays, raise
`MAX_REQUEST_BYTES` accordingly — but keep the proxy limit just
above so the proxy still drops obvious abuse before parsing.

## CORS for browser-hosted clients

If your MCP client runs in a browser on a different origin (e.g. a
hosted Claude web client at `claude.ai/...` calling
`mcp.example.com/mcp/`), you need CORS. The HTML admin doesn't
need it — its client is same-origin — so this is the first time a
Django shop typically meets the CORS requirements.

Install [`django-cors-headers`](https://pypi.org/project/django-cors-headers/)
and configure:

```python
# settings.py
INSTALLED_APPS += ["corsheaders"]

# CorsMiddleware MUST be above CommonMiddleware and CsrfViewMiddleware.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "https://your-client-origin.example.com",
]
CORS_ALLOW_CREDENTIALS = True                # required for session cookies
CORS_ALLOW_HEADERS = [
    "accept",
    "content-type",
    "x-csrftoken",                           # MCP clients send this on POSTs
    "x-requested-with",
]
```

Two CSRF-related gotchas when CORS is on:

1. `SESSION_COOKIE_SAMESITE = "None"` is required for cross-site
   cookie sending, and `SESSION_COOKIE_SECURE = True` is then
   non-optional. (Browsers refuse SameSite=None over plain HTTP.)
2. The MCP client must include the CSRF token in the
   `X-CSRFToken` request header on every POST — same as Django's
   own AJAX recipe.

## Rate limiting

The package ships no rate limiting. An agent that misbehaves (or a
compromised session) can hammer `/mcp/` faster than any human ever
could. Add `django-ratelimit` and pin a per-user limit at the view
layer.

```python
# urls.py
from django.urls import include, path
from django_ratelimit.decorators import ratelimit
from django_admin_mcp_api.server.views import McpEndpointView

mcp_view = ratelimit(key="user", rate="60/m", block=True)(
    McpEndpointView.as_view()
)

urlpatterns = [
    path("mcp/", mcp_view),
    path("mcp/", include("django_admin_mcp_api.urls")),  # for /mcp/manifest/
]
```

Tune by tool weight: `admin.list` is cheap; `admin.bulk_update` on a
1k-row queryset is not. If your usage skews toward bulk operations,
add a lower limit on the bulk endpoint or move heavy work to a
background task.

## Logging

The MCP layer emits structured records via
`logging.getLogger("django_admin_mcp_api.server.views")`:

| Logger name | Level | Emitted on |
| --- | --- | --- |
| `mcp.auth.unauthenticated` | WARNING | 401 — anonymous caller |
| `mcp.auth.forbidden` | WARNING | 403 — non-staff caller |
| `mcp.request.too_large` | WARNING | 413 — body exceeded `MAX_REQUEST_BYTES` |
| `mcp.tools_call` | INFO | every successful or upstream-4xx `tools/call` |
| `mcp.tools_call.upstream_error` | WARNING | dispatcher raised |

The package never logs request bodies — payloads can contain
passwords (`admin.set_password`) or PII (any model row).

Wire the logger into your existing aggregator:

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            # or whatever shape your stack expects
        },
    },
    "loggers": {
        "django_admin_mcp_api": {
            "level": "INFO",
            "handlers": ["json"],
            "propagate": False,
        },
    },
}
```

## Health checks

Don't point your load balancer at `/mcp/` — that endpoint requires
auth, so the LB health-check would fail. Add a separate URL that
doesn't depend on the MCP package:

```python
# urls.py
from django.http import HttpResponse
urlpatterns = [
    path("healthz", lambda r: HttpResponse("ok")),
    # ...
]
```

If you want a deeper liveness probe that confirms the MCP wire is
actually up, an authenticated `GET /mcp/` returns a JSON status
payload (see the README "GET /mcp/" landing) — but it costs an auth
round-trip per probe.

## Backups + audit retention

The MCP layer doesn't write to the database. Every write is in
rest-api, where it goes through Django's `LogEntry`. The audit
trail you keep is the same one your HTML admin already produces —
back up the `django_admin_log` table the same way you back up the
rest of your application database.

For finer-grained traffic logs, retain the `mcp.tools_call` records
emitted by the MCP layer for as long as your incident-response
policy requires. Typical: 30–90 days hot, 1 year cold.

## What's NOT covered here

- **Database tuning.** rest-api's queryset behaviour is its own
  concern; the MCP layer adds nothing to it.
- **Static / media files.** The package serves no static assets and
  uploads nothing to media.
- **Session backend choice.** Whatever you use for the HTML admin
  works for MCP — they share the cookie.
- **Migrations.** The package has no models, so no migrations.

See [`SECURITY.md`](../SECURITY.md) for the in-scope security
invariants, and [`threat-model.md`](threat-model.md) for what's
delegated to rest-api / the consumer's deployment.
