# Threat model — `django-admin-mcp-api`

This is the MCP layer's threat model. It is intentionally narrow:
`django-admin-mcp-api` is a wire-protocol adapter over
[`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).
The upstream REST API owns admin behaviour — querysets, permissions,
forms, serialization — so most of the "what could go wrong with the
admin" surface is **out of scope here** and lives in
[rest-api's threat model](https://github.com/MartinCastroAlvarez/django-admin-rest-api).

This document covers the bits the MCP layer adds on top.

## 1. Assets

| Asset                                | Held by                              | Notes |
| ------------------------------------ | ------------------------------------ | ----- |
| Django session ID + CSRF token       | The consumer's existing middleware   | Read but never logged or persisted by this package. |
| The JSON-RPC envelope                | This package, in-memory only         | Never written to disk; never echoed in error logs. |
| The tool catalogue (read-only)       | This package, served as JSON         | Public to any authenticated staff user; same as `tools/list`. |
| The dispatched `DispatchTarget`      | This package, in-memory only         | Built from the tool's input schema; forwarded to rest-api. |
| The rest-api response body           | Forwarded verbatim, in-memory only   | This package decodes JSON for the MCP envelope but does not transform. |

## 2. Trust boundaries

```
┌─────────────┐  HTTPS + session  ┌──────────────────────────┐  in-process  ┌──────────────────────────┐
│ MCP client  │ ────────────────▶ │  django-admin-mcp-api    │ ───────────▶ │  django-admin-rest-api   │
│ (untrusted) │                   │  (this package)          │              │  (admin authority)       │
└─────────────┘                   └──────────────────────────┘              └──────────────────────────┘
```

Two boundaries:

1. **HTTP boundary** — between the MCP client and Django. Crossed by
   the consumer's existing middleware: TLS, sessions, CSRF, host
   validation. Not added or modified by this package.
2. **In-process boundary** — between this package and rest-api. The
   dispatcher (`server/dispatch.py::RestApiDispatcher`) is the *only*
   thing that crosses it.

## 3. What the MCP layer protects against

| Threat                                                          | Mitigation                                                                                 |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Unauthenticated client reaches a tool                           | `_auth_gate` rejects with 401 before parsing the envelope. (`server/views.py`)              |
| Non-staff client reaches a tool                                 | `_auth_gate` rejects with 403. The real per-tool permission check still runs in rest-api.   |
| Cross-site request forgery from a logged-in user's browser      | Django `CsrfViewMiddleware` is enforced; no view in the package is exempt. Pre-commit hook + test enforce this. |
| Malformed JSON-RPC envelope                                     | `jsonrpc.parse_request` validates `jsonrpc`/`method`/`params`; bad shape → INVALID_REQUEST. |
| Malformed tool arguments (missing required, wrong type, extra)  | JSON Schema validation runs before `build_target`; failures return INVALID_PARAMS with a json-pointer path. |
| Unknown method or tool name                                     | Both surface as METHOD_NOT_FOUND with the offending name, never as 5xx.                     |
| Token-shaped strings entering the repo                          | Pre-commit `gitleaks` + `no-partial-tokens` pygrep hook + `tests/test_security.py` triple-check. |
| `@csrf_exempt` sneaking into the package                        | Pre-commit `no-csrf-exempt` pygrep + `test_no_csrf_exempt_in_package` test.                 |
| Direct DB access in the dispatch layer                          | Pre-commit `no-objects-all-in-server` pygrep + `test_no_direct_objects_queries_in_server`.  |
| `user.has_perm` calls reintroducing a parallel permission system | `test_no_user_has_perm_in_package`.                                                         |

## 4. What the MCP layer does NOT protect against (by design)

These belong to rest-api, the consumer, or the deployment platform.
Trying to protect against them here would create a parallel security
system — the exact failure mode the project rules forbid.

| Out of scope here                                       | Where it lives                                |
| ------------------------------------------------------- | --------------------------------------------- |
| Per-tool permission decisions                           | `ModelAdmin.has_*_permission` via rest-api    |
| Field-level read/write authorization                    | `ModelAdmin.get_form` / `readonly_fields` via rest-api |
| Queryset construction                                   | `ModelAdmin.get_queryset` via rest-api        |
| Field serialization safety + denylist                   | rest-api's serializer                         |
| Cascade preview for destructive actions                 | rest-api's `delete_preview` view              |
| TLS, host headers, secure cookies                       | Consumer's Django settings + reverse proxy    |
| Rate limiting                                           | Consumer's middleware (e.g. `django-ratelimit`) |
| WAF / IP allowlists                                     | Consumer's infra                               |
| Password storage / rotation                             | Django auth + rest-api's set-password view    |

If a CVE arrives in any of the rows above, file it on the right repo:
- Admin behaviour / rest-api → file there.
- Consumer's middleware → file with that maintainer.
- This adapter (MCP wire, dispatch, auth gate, validation) → file
  here via a [private security advisory](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/security/advisories/new).

## 5. Attacker model

We assume the attacker may be:

- An unauthenticated network caller (handled by the 401 gate).
- An authenticated **non-staff** user with valid session + CSRF token
  (handled by the 403 gate; the real per-tool check is in rest-api).
- A compromised **staff** session whose owner is acting in good faith
  (any abuse from this caller is rest-api's problem and Django's
  audit-log problem — `LogEntry` writes happen there).

We do **not** assume:

- Network-level adversaries who can strip TLS (consumer's deployment).
- A malicious operator with code-deploy access (out of scope for any
  Django package's threat model).

## 6. Review checklist for PRs that touch security-relevant code

Anything that modifies `server/views.py`, `server/dispatch.py`,
`server/jsonrpc.py`, or `tools/*.py` should answer all of:

1. Does it add a new auth path, or change the 401/403 behaviour?
2. Does it change the CSRF posture?
3. Does it change what gets logged?
4. Does it widen the trust boundary into rest-api (e.g. forwarding new
   request attributes)?
5. Does it modify a JSON Schema (potentially loosening input
   validation)?

If any answer is yes, link the answer in the PR body. CODEOWNERS will
route the review to the security-aware reviewer automatically.
