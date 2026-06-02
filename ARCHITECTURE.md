# Architecture

This is the design contract for `django-admin-mcp-api`. Read it before
making structural changes.

## The one-line summary

`django-admin-mcp-api` is a **wire-protocol adapter** that turns MCP
JSON-RPC requests into `django-admin-rest-api` HTTP requests. It contains
no admin logic.

```
┌─────────────────┐   MCP JSON-RPC over HTTP   ┌──────────────────────────┐   Django HTTP   ┌────────────────────────┐
│  Agent / Client │ ────────────────────────▶  │  django-admin-mcp-api    │ ──────────────▶ │  django-admin-rest-api │ ──▶ ModelAdmin
└─────────────────┘                            └──────────────────────────┘                 └────────────────────────┘
                                               (this package)                               (the REST surface, owner of all admin logic)
```

## Package layout

```
django_admin_mcp_api/
├── __init__.py        — version + default_app_config
├── apps.py            — Django AppConfig
├── conf.py            — DJANGO_ADMIN_MCP_API settings reader (one place)
├── urls.py            — two URLs: POST / (MCP), GET /manifest/
├── server/
│   ├── views.py       — McpEndpointView + ManifestView (HTTP entry)
│   ├── jsonrpc.py     — JSON-RPC 2.0 envelope helpers
│   ├── errors.py      — error code constants
│   ├── manifest.py    — initialize + tools/list payload builders
│   └── dispatch.py    — the ONE seam to django-admin-rest-api
└── tools/
    ├── base.py        — Tool dataclass + shared schema fragments
    ├── registry.py    — admin.registry
    ├── schema.py      — admin.schema
    ├── recent_actions.py
    ├── list_objects.py
    ├── retrieve.py
    ├── add_form.py
    ├── create.py
    ├── update.py
    ├── destroy.py
    ├── bulk_update.py
    ├── autocomplete.py
    ├── action.py
    ├── history.py
    ├── delete_preview.py
    ├── set_password.py
    └── panel.py
```

## Request flow

1. **HTTP arrives** at `McpEndpointView`. CSRF is checked by Django
   middleware before the view runs.
2. **Auth gate** — `_auth_gate(request)` rejects anonymous (`401`) and
   non-staff (`403`). This is the *minimum* gate; the real permission
   check happens inside rest-api per tool.
3. **Envelope parse** — `jsonrpc.parse_request` validates the JSON-RPC
   2.0 envelope.
4. **Method dispatch** — `initialize` / `tools/list` / `tools/call` are
   each one branch in `_handle_jsonrpc`. Everything else is
   `METHOD_NOT_FOUND`.
5. **For `tools/call`** — look up the tool by name. If unknown,
   `METHOD_NOT_FOUND`. Validate `arguments` against the tool's
   declared JSON Schema (`jsonschema.Draft202012Validator`); any
   violation surfaces as `INVALID_PARAMS` with a json-pointer path of
   the failing field. Then run `tool.build_target(arguments)` to
   translate into a `DispatchTarget` (method + path + body + query).
6. **Forward** — `dispatcher.dispatch(request=…, target=…)` hands the
   forward off to rest-api. The dispatcher carries the original
   authenticated `HttpRequest` so session + CSRF + user identity are
   preserved untouched.
7. **Wrap** — the rest-api `HttpResponse` body is decoded and wrapped in
   the MCP `result.content` envelope. Non-2xx responses become
   `isError: true`.

## The dispatcher seam

`server/dispatch.py::Dispatcher` is a `Protocol`. There are three
implementations:

- **`RestApiDispatcher`** — the live default. Resolves the target's
  path against `django_admin_rest_api.api.urls`, builds a synthetic
  `HttpRequest`, and calls the matched view in-process. `django-admin-rest-api`
  is a hard runtime dependency, so a normal install always uses this.
- **`PendingDispatcher`** — fallback used only if rest-api is not
  importable. Every call raises `DispatcherNotInstalled` pointing at the
  install step.
- **`FakeDispatcher`** (in `tests/helpers.py`) — echoes the target back.
  Used by the test suite (via the `DISPATCHER_FACTORY` setting) to
  exercise the full wire path without rest-api.

`dispatch.py` is the *only* file that crosses the rest-api boundary.
When rest-api ships a change, this is the only file that should need to
move. Everything else — views, tools, manifest — stays as written.

### Synthetic-request attribute contract

`RestApiDispatcher` does **not** run the synthetic forward through
Django's middleware stack — it resolves the rest-api URL conf and calls
the matched view callable directly. It therefore copies a **deliberately
minimal, explicit** set of attributes from the original (middleware-
processed) request onto the synthetic one. rest-api views can rely on
exactly these and no more:

| Attribute   | Carried? | Notes                                                                 |
| ----------- | -------- | --------------------------------------------------------------------- |
| `user`      | ✅ always | The authenticated caller. Auth identity matches the MCP request exactly, so rest-api's per-model/per-object permission and queryset checks run against the same caller. |
| `session`   | ✅ if set | Copied when the original request has one (`hasattr` guarded).         |
| `COOKIES`   | ✅ always | The original cookie dict.                                             |
| `_messages` | ✅ if set | Django's private messages backend, so rest-api views can emit admin messages. The one private-API touch. |

**Deliberately NOT carried** (because middleware is skipped):

- `_dont_enforce_csrf_checks` — the per-request CSRF bypass flag. CSRF is
  verified once at the outer `McpEndpointView` POST; the in-process
  forward does not re-run middleware, so copying this flag would only
  carry a future bypass risk (#44).
- Anything set by other middleware the consumer installs (locale,
  GeoIP, custom `request.*` attributes, etc.). A rest-api view that
  assumes a middleware-set attribute beyond the four above will **not**
  see it across this seam and should fail loudly by contract rather than
  silently misbehave.

The original request is never mutated — the synthetic request gets its
own attributes. This contract is the authoritative statement; the inline
comments in `dispatch.py::_build_synthetic_request` defer to it (#82b).

## Tool ↔ rest-api endpoint mapping

See [`django_admin_mcp_api/tools/README.md`](django_admin_mcp_api/tools/README.md)
for the full table. The invariant: one MCP tool ↔ one rest-api endpoint,
no more, no less.

## What lives in rest-api, not here

- All permission checks (`has_view_permission`, `has_add_permission`,
  `has_change_permission`, `has_delete_permission`, plus the per-object
  variants).
- All queryset construction (`ModelAdmin.get_queryset`).
- All form / formset processing (`ModelAdmin.get_form`,
  `save_model`, inline formsets).
- All field serialization + the denylist on top of `exclude`/`readonly_fields`.
- All cascade computation for `admin.delete_preview`.
- All `LogEntry` writes.
- All admin-action execution.
- Authentication beyond "user is signed in as staff".

If you're tempted to add any of the above here, stop and open an issue
against rest-api instead.

## Settings

All consumer-tunable knobs live under one namespace and are read through
`conf.get`. Every key has a sensible default — overrides are optional.

```python
# settings.py
DJANGO_ADMIN_MCP_API = {
    "PROTOCOL_VERSION":  "2024-11-05",            # MCP spec version we speak
    "SERVER_NAME":       "django-admin",          # advertised via initialize
    "SERVER_VERSION":    None,                    # None -> package __version__
    "ADMIN_SITE":        "django.contrib.admin.site",
    "DISPATCHER_FACTORY": None,                   # dotted path; None = built-in
}
```

Defaults live in `conf.DEFAULTS`. Unknown keys raise `KeyError` to catch
typos in consumer settings at startup. See the README's "Configuration"
section for the per-key explanation table, and the commented block in
[`examples/quickstart/myproject/settings.py`](examples/quickstart/myproject/settings.py)
for a copy-paste-ready example.

## Testing

The test suite runs against a minimal test project in
`tests/test_project/` configured with `DISPATCHER_FACTORY` pointing at
`FakeDispatcher`. That lets us assert the exact HTTP shape we would
forward to rest-api without rest-api itself being installed. See
[`tests/README.md`](tests/README.md) for the layout.

## Future work

Tracked in the [project board](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/projects).
Highlights:

- Wire `RestApiDispatcher` once `django-admin-rest-api` is on PyPI.
- Decide MCP transport(s) for v0.1 (HTTP-only, stdio, or both).
- Screenshot script.
- v0.1.0 PyPI release.
