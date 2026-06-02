# API contract — `django-admin-mcp-api`

The MCP wire contract this package speaks. Stable across patch
versions; any breaking change is a major version bump and listed in
`CHANGELOG.md`.

The contract has two layers:

1. **JSON-RPC 2.0** — the envelope shape every request and response
   wears.
2. **MCP methods on top of JSON-RPC** — `initialize`, `tools/list`,
   `tools/call`. Plus the optional read-only `GET /manifest/`.

## 1. Endpoints

| URL (relative to your mount point) | Method | Purpose                                                          |
| ---------------------------------- | ------ | ---------------------------------------------------------------- |
| `/`                                | POST   | The MCP JSON-RPC entry point. All MCP methods go through here.    |
| `/manifest/`                       | GET    | Read-only catalogue document for humans and dashboards.           |

Both endpoints enforce Django's session + CSRF auth and require an
authenticated staff user. Per the SECURITY rules, no endpoint is
CSRF-exempt.

## 2. Auth response codes

| Caller                          | Code | Body                                                          |
| ------------------------------- | ---- | ------------------------------------------------------------- |
| Anonymous (no session)          | 401  | JSON-RPC error with code `SERVER_ERROR_UNAUTHENTICATED` (-32001). |
| Authenticated, non-staff        | 403  | JSON-RPC error with code `SERVER_ERROR_FORBIDDEN` (-32002).      |
| Authenticated staff             | 200  | Normal flow; per-tool permission check still happens in rest-api. |
| Authenticated, no CSRF on POST  | 403  | Django CSRF middleware response (HTML).                          |

## 3. JSON-RPC envelope

Every request is a single JSON object (batch requests are **not**
supported):

```json
{
  "jsonrpc": "2.0",
  "id":      <number | string | null>,
  "method":  "<method name>",
  "params":  { ... }
}
```

A successful response:

```json
{
  "jsonrpc": "2.0",
  "id":      <echoed request id>,
  "result":  { ... }
}
```

A failure response:

```json
{
  "jsonrpc": "2.0",
  "id":      <echoed request id or null>,
  "error": {
    "code":    <integer>,
    "message": "<string>",
    "data":    <optional, free-form>
  }
}
```

Failure responses use HTTP 400 (or 401 / 403 for the auth gate); the
`error.code` carries the precise signal.

## 4. MCP methods

### 4.1 `initialize`

Negotiates the protocol version and reports server capabilities.

**Request params**: none (any params are ignored).

**Result**:

```json
{
  "protocolVersion": "2024-11-05",
  "serverInfo":      { "name": "django-admin", "version": "<pkg version>" },
  "capabilities":    { "tools": { "listChanged": false } }
}
```

`protocolVersion` and `serverInfo.name` are configurable via
`DJANGO_ADMIN_MCP_API` settings. `capabilities.tools.listChanged` is
`false` because the tool set is static (registered at import time).

### 4.2 `tools/list`

Returns the same catalogue `GET /manifest/` returns, in the
MCP-spec-correct shape.

**The catalogue is static and not permission-filtered.** Every
authenticated staff caller receives the identical tool list (the full
registered set minus `DISABLED_TOOLS`); it is *not* narrowed by the
caller's per-model `ModelAdmin.has_*_permission`. This is intentional
(#77):

- The catalogue lists **capabilities** (verbs like `admin.list`,
  `admin.destroy`), not **model instances**. A single `admin.destroy`
  tool applies to whatever model the caller has delete permission on;
  there is no per-model tool variant to hide. rest-api's per-user
  registry (`GET /registry/`, surfaced as `admin.registry`) answers the
  *which models can I touch?* question on the correct axis.
- Filtering the tool list against the registry would not produce a
  meaningful narrowing (a verb either applies to all of a user's models
  or none), and doing it any other way would mean re-deriving
  permissions inside this layer — forbidden by the prime directive
  (rest-api owns authorization; this package never calls `has_perm`).

**Presence in the catalogue is therefore not authorization.** A tool
appearing in `tools/list` only means the server *exposes* that verb —
the actual permission check runs per call inside rest-api, which returns
the appropriate 4xx (surfaced as `isError: true` content) if the caller
lacks permission on the target model. Agents must not treat catalogue
presence as a grant. See `threat-model.md` for the security framing.

**Request params**: none.

**Result**:

```json
{
  "tools": [
    {
      "name":        "admin.<verb>",
      "description": "<one-line summary>",
      "inputSchema": { "type": "object", ... }
    },
    ...
  ]
}
```

### 4.3 `tools/call`

Invoke a tool. The tool's arguments are validated against its
`inputSchema` *before* forwarding to rest-api.

**Request params**:

```json
{
  "name":      "<tool name>",
  "arguments": { ... }
}
```

**Result on success**:

```json
{
  "content": [
    { "type": "json", "json": <rest-api response body> }
  ],
  "isError": false,
  "status":  <upstream HTTP status, usually 200>
}
```

**Result on upstream 4xx** (e.g. rest-api 404 because the
`app_label`/`model_name` does not exist): the call still succeeds —
the agent *got* an answer — but the result content flags the upstream
failure:

```json
{
  "content": [{ "type": "json", "json": <rest-api error body> }],
  "isError": true,
  "status":  <upstream HTTP status, 4xx>
}
```

This distinction matters: a JSON-RPC `error` envelope means *we* could
not run the call (bad envelope, unknown method, schema violation). An
`isError: true` result content means *rest-api* ran the call and
returned a 4xx — the wire layer did its job.

## 5. Tool catalogue

The catalogue is exposed via `tools/list` and `GET /manifest/`. The
mapping from MCP tool to rest-api endpoint is one-to-one and listed in
[`../django_admin_mcp_api/tools/README.md`](../django_admin_mcp_api/tools/README.md).

Every tool's `inputSchema` is a JSON Schema document; agents can read
the catalogue and self-correct their arguments without consulting the
docs. Schema dialect is Draft 2020-12.

## 6. Error code vocabulary

Constants live in
[`../django_admin_mcp_api/server/errors.py`](../django_admin_mcp_api/server/errors.py).

| Code   | Name                            | When                                                    |
| ------ | ------------------------------- | ------------------------------------------------------- |
| -32700 | `PARSE_ERROR`                   | Request body is not valid JSON.                          |
| -32600 | `INVALID_REQUEST`               | Envelope shape is wrong (missing `method`, non-object, batch). |
| -32601 | `METHOD_NOT_FOUND`              | Unknown JSON-RPC method, or unknown tool in `tools/call`. |
| -32602 | `INVALID_PARAMS`                | Schema validation failed, or required argument missing.   |
| -32603 | `INTERNAL_ERROR`                | Unhandled exception (should never happen — file a bug). |
| -32001 | `SERVER_ERROR_UNAUTHENTICATED`  | Caller is anonymous.                                     |
| -32002 | `SERVER_ERROR_FORBIDDEN`        | Caller is authenticated but not staff.                   |
| -32003 | `SERVER_ERROR_NOT_FOUND`        | Reserved for future use.                                 |
| -32004 | `SERVER_ERROR_CSRF`             | Reserved (Django middleware returns 403 first today).    |
| -32005 | `SERVER_ERROR_VALIDATION`       | Reserved for future use.                                 |
| -32099 | `SERVER_ERROR_UPSTREAM`         | `NotImplementedError` from the dispatcher (e.g. rest-api not installed). |

## 7. Stability

The contract follows semver:

- **Patch** (`0.1.x`): bug fixes, doc tweaks, no surface changes.
- **Minor** (`0.x.0`): new tools, new optional fields on existing
  responses, new optional input fields. Backwards-compatible.
- **Major** (`x.0.0`): renaming or removing tools, changing the
  envelope shape, changing error code meanings, adding required
  arguments to existing tools.

Any breaking change is announced in `CHANGELOG.md`, paired with a
migration paragraph, and lands in a single PR labelled `breaking`.
