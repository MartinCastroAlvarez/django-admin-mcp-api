# Tool reference

The MCP catalogue is self-describing — `tools/list` returns the
JSON Schema of every tool's `arguments`. This document is the
human-readable mirror of that schema: one section per tool, with
the input shape, the rest-api endpoint each tool forwards to, and
a worked example.

Conventions:

- `app_label` and `model_name` are lowercase Django identifiers
  (`^[a-z][a-z0-9_]*$`).
- `pk` is always a string on the wire, even if the database column
  is integer-typed. The MCP layer forwards the value as-is to
  rest-api, which coerces it through Django's URL converter.
- Every tool runs through the same auth gate (staff + CSRF) and
  the same per-tool permission check inside rest-api (your
  `ModelAdmin.has_*_permission`). If your admin would say 403, the
  tool returns the upstream 403 inside the MCP envelope's
  `isError: true` content.

## Quick index

| Tool | Method | Required arguments |
| --- | --- | --- |
| [`admin.registry`](#adminregistry) | GET | _none_ |
| [`admin.schema`](#adminschema) | GET | _none_ |
| [`admin.recent_actions`](#adminrecent_actions) | GET | _none_ |
| [`admin.list`](#adminlist) | GET | `app_label`, `model_name` |
| [`admin.retrieve`](#adminretrieve) | GET | `app_label`, `model_name`, `pk` |
| [`admin.add_form`](#adminadd_form) | GET | `app_label`, `model_name` |
| [`admin.create`](#admincreate) | POST | `app_label`, `model_name`, `data` |
| [`admin.update`](#adminupdate) | PATCH | `app_label`, `model_name`, `pk`, `data` |
| [`admin.destroy`](#admindestroy) | DELETE | `app_label`, `model_name`, `pk` |
| [`admin.bulk_update`](#adminbulk_update) | PATCH | `app_label`, `model_name`, `pks`, `data` |
| [`admin.autocomplete`](#adminautocomplete) | GET | `app_label`, `model_name` |
| [`admin.action`](#adminaction) | POST | `app_label`, `model_name`, `action_name`, `pks` |
| [`admin.history`](#adminhistory) | GET | `app_label`, `model_name`, `pk` |
| [`admin.delete_preview`](#admindelete_preview) | GET | `app_label`, `model_name`, `pk` |
| [`admin.set_password`](#adminset_password) | POST | `app_label`, `model_name`, `pk`, `password` |
| [`admin.panel`](#adminpanel) | GET | `app_label`, `model_name`, `pk`, `panel_name` |

---

## `admin.registry`

List every model registered on the `AdminSite` that the authenticated
user is allowed to see.

- **Forwards to**: `GET /api/v1/registry/`
- **Arguments**: none (closed schema; extra keys rejected).

```jsonc
{ "method": "tools/call", "params": { "name": "admin.registry", "arguments": {} } }
```

The response carries the user, the registered apps, and for each
model the user's permission flags plus the available admin actions
with their `target` field.

---

## `admin.schema`

Return the full admin metadata schema — field types, widgets,
list columns, filters — for every model the user can see.

- **Forwards to**: `GET /api/v1/schema/`
- **Arguments**: none.

---

## `admin.recent_actions`

The signed-in user's own `LogEntry` history (the admin index's
"Recent actions" panel).

- **Forwards to**: `GET /api/v1/recent-actions/`
- **Arguments**: none.

---

## `admin.list`

Return one page of list-view results for a model, honouring the
consumer's `ModelAdmin` queryset, `list_display`, `list_filter`,
ordering, and search.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/`
- **Arguments**:
  - `app_label` (required, string)
  - `model_name` (required, string)
  - `page` (optional, integer ≥1)
  - `page_size` (optional, integer 1–200)
  - `search` (optional, string — free-text)
  - `ordering` (optional, string — comma-separated field names; leading `-` for descending)
  - Any other key is forwarded **verbatim** as a query parameter — the
    schema is `additionalProperties: true` (the only tool that is) so
    arbitrary `ModelAdmin.list_filter` keys can be passed through.

> **Intentional open passthrough (#78).** `admin.list` mirrors the
> Django admin changelist querystring, where the valid filter keys are
> whatever the consumer's `ModelAdmin.list_filter` declares — an
> open-ended, per-deployment set that the schema cannot enumerate. So
> unlike every other tool (all `additionalProperties: false`),
> `admin.list` deliberately forwards unknown keys verbatim to rest-api.
>
> The trade-off: a **typo'd filter key** (e.g. `serach=ada` instead of
> `search=ada`) passes JSON-Schema validation and is forwarded to
> rest-api, which ignores unrecognised query params rather than
> erroring. The agent gets **no** json-pointer feedback for that one
> mistake. Values are always coerced to strings, so there is no type
> confusion, and the synthetic request's path is still re-validated by
> Django's resolver — but **field-name typos and unintended filters
> will not be schema-caught** on this tool. Treat the recognised keys
> below as the documented surface; anything else is best-effort
> changelist passthrough.

```jsonc
{ "name": "admin.list",
  "arguments": { "app_label": "auth", "model_name": "user",
                 "page": 1, "page_size": 50, "search": "ada" } }
```

---

## `admin.retrieve`

Return the detail-view payload for one object, including read-only
fields, inline relations, and the boolean permission flags.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/<pk>/`
- **Arguments**: `app_label`, `model_name`, `pk` (all required, all string).

---

## `admin.add_form`

Return the create-page field descriptors for a new object — the
writable fields, their widgets, initial values, choices, and
validators.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/add/`
- **Arguments**: `app_label`, `model_name`.

---

## `admin.create`

Create one object through `ModelAdmin.get_form()`. Validation, save
hooks, and inline-formset handling are owned by rest-api.

- **Forwards to**: `POST /api/v1/<app_label>/<model_name>/`
- **Arguments**:
  - `app_label`, `model_name`
  - `data` (required, object) — field name → value map.

```jsonc
{ "name": "admin.create",
  "arguments": { "app_label": "auth", "model_name": "user",
                 "data": { "username": "ada", "is_staff": true } } }
```

---

## `admin.update`

Partial-update one object through `ModelAdmin.get_form()`. Only
the changed fields need to be in `data`.

- **Forwards to**: `PATCH /api/v1/<app_label>/<model_name>/<pk>/`
- **Arguments**: `app_label`, `model_name`, `pk`, `data`.

Writes to `exclude` or `readonly_fields` are rejected by rest-api
as 400 (the value on the object is unchanged).

---

## `admin.destroy`

Delete one object via `ModelAdmin.delete_model()`. Cascade behaviour
is owned by rest-api.

- **Forwards to**: `DELETE /api/v1/<app_label>/<model_name>/<pk>/`
- **Arguments**: `app_label`, `model_name`, `pk`.

For a preview of what the cascade would touch, use
[`admin.delete_preview`](#admindelete_preview) first.

---

## `admin.bulk_update`

Apply the same field updates to multiple objects in one round-trip.

- **Forwards to**: `PATCH /api/v1/<app_label>/<model_name>/bulk/`
- **Arguments**:
  - `app_label`, `model_name`
  - `pks` (array of strings, minItems 1) — primary keys.
  - `data` (object) — field name → new value map; applied to every pk.

---

## `admin.autocomplete`

Return autocomplete suggestions for a model the consumer's
`ModelAdmin` marks as autocomplete-enabled.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/autocomplete/`
- **Arguments**: `app_label`, `model_name`, `q` (optional search string).

---

## `admin.action`

Run one of the model's `ModelAdmin.actions` callables. The call shape
depends on the action's declared signature — see
[the agent recipe in the README](../README.md#-how-an-agent-uses-adminaction).

- **Forwards to**: `POST /api/v1/<app_label>/<model_name>/actions/<action_name>/`
- **Arguments**:
  - `app_label`, `model_name`
  - `action_name` (`^[a-z][a-z0-9_]*$`) — must be in `ModelAdmin.actions`.
  - `pks` (array of strings, minItems 1) — for `target=batch`
    actions, one or more; for `target=detail`, exactly one.

The action's `target` is discoverable on the descriptor returned by
[`admin.registry`](#adminregistry), [`admin.list`](#adminlist), and
[`admin.retrieve`](#adminretrieve).

---

## `admin.history`

Return the `LogEntry` timeline for one object — the same data the
HTML admin's "History" page renders.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/<pk>/history/`
- **Arguments**: `app_label`, `model_name`, `pk`.

---

## `admin.delete_preview`

Preview the cascade / protected impact of deleting one object before
calling [`admin.destroy`](#admindestroy). Read-only.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/<pk>/delete-preview/`
- **Arguments**: `app_label`, `model_name`, `pk`.

---

## `admin.set_password`

Set / change the password on a model whose admin exposes a
password-change form (typically `User`). 404 for models whose admin
has no `change_password_form` declared.

- **Forwards to**: `POST /api/v1/<app_label>/<model_name>/<pk>/password/`
- **Arguments**:
  - `app_label`, `model_name`, `pk`
  - `password` (string, minLength 1).

The password is hashed and stored by rest-api via the consumer's
admin set-password form. The MCP layer **never** logs the password
value, only the structural fields of the call.

---

## `admin.panel`

Read a custom panel for one object. The consumer declares panels
directly on their `ModelAdmin` as `panels = {"name": "method_name"}` —
no rest-api mixin or subclass is required (rest-api ≥1.0.8; earlier
versions used `PanelEndpointsMixin`, now a deprecated no-op shim).
404 unless the admin has registered the named panel.

- **Forwards to**: `GET /api/v1/<app_label>/<model_name>/<pk>/panel/<panel_name>/`
- **Arguments**: `app_label`, `model_name`, `pk`, `panel_name`.

---

## Errors

Every tool can return three classes of failure inside the MCP
envelope:

| Source | Shape | Cause |
| --- | --- | --- |
| **Wire layer** | JSON-RPC `error` with `code` from `errors.py` | Bad envelope, unknown method, unknown tool, schema violation, oversized body, auth failure. The call did not reach rest-api. |
| **Upstream non-2xx** | JSON-RPC `result` with `isError: true` and `status >= 400` | rest-api returned a 4xx — typically a permission denial or a model not registered. The call reached rest-api; rest-api decided. |
| **Upstream exception** | JSON-RPC `error` with `code = SERVER_ERROR_UPSTREAM (-32099)` | The dispatcher raised `NotImplementedError` / `UnknownRestApiPath` / `UnsupportedDispatchMethod`. Indicates misconfiguration, not user input. |

See [`api-contract.md`](api-contract.md) §6 for the full error
code vocabulary.
