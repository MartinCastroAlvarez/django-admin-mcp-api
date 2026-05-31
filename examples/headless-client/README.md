# `examples/headless-client/`

> A programmatic login recipe — log into the Django admin, capture
> the session cookie, and use it from anything that can speak HTTP.

The MCP endpoint requires Django session + CSRF auth — the same gate
the HTML admin uses. Browser clients (and Cursor / Claude with
recent HTTP-transport support) get this for free; headless clients
(Python scripts, Node services, CI jobs) need to do the cookie
acquisition explicitly.

This is **the standard Django session-auth flow over HTTP** — nothing
MCP-specific. If you've ever programmatically logged into a Django
admin you've already done this.

Closes #37 (option A — the bootstrap recipe). A `TOKEN_AUTH_BACKEND`
opt-in for clients that can't acquire a session is tracked as a
separate enhancement.

## Run it

```bash
cd examples/headless-client
python -m venv .venv && . .venv/bin/activate
pip install httpx                                     # only stdlib + httpx
python bootstrap.py \
  --base     https://your-django-host/ \
  --user     admin \
  --password "$ADMIN_PASSWORD" \
  --out      /tmp/cookies.json
```

The script writes a JSON file with the two cookies the MCP endpoint
needs:

```json
{
  "sessionid":  "abc123…",
  "csrftoken":  "def456…",
  "base":       "https://your-django-host/",
  "captured_at": "2026-05-31T10:30:00Z"
}
```

Then re-use those cookies for any MCP call:

```bash
python call.py /tmp/cookies.json initialize
python call.py /tmp/cookies.json tools/list
python call.py /tmp/cookies.json tools/call admin.registry
```

## Files

| File             | What it does                                                       |
| ---------------- | ------------------------------------------------------------------ |
| [`bootstrap.py`](bootstrap.py) | Programmatic login. Writes a cookies file.                         |
| [`call.py`](call.py)           | Stdlib-only MCP client. Reads the cookies file, POSTs JSON-RPC.   |

## Security notes

- The cookies file contains a live session — treat it like a
  credential. Don't commit it; don't paste it into chat.
- Rotate it when the session expires (Django default: 2 weeks
  inactivity, or `SESSION_COOKIE_AGE` if you've set it).
- For long-lived headless clients in production, prefer a dedicated
  service account with `is_staff=True` and the minimum per-model
  permissions it needs. Audit log entries will carry that account
  name so you can tell programmatic traffic from human traffic.
- For multi-process clients, bootstrap once and reuse the cookies
  file — login is cheap but rate-limited at the auth layer.

## What does NOT belong here

- **Production-grade token vending.** This is a recipe, not an
  identity broker. For real headless auth see the future
  `TOKEN_AUTH_BACKEND` setting (deferred to a follow-up PR after
  #37 — open an issue if it's blocking you).
- **A long-running daemon.** Same logic, but with a refresh loop
  and a keychain integration — beyond the scope of an example.
