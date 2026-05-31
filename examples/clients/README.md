# `examples/clients/`

> Drop-in configuration snippets for major MCP clients. Each file is
> a working template — replace the placeholder URL + cookie/token
> with your deployment's values and the client can drive your admin.

Closes #38.

## Files

| File                                                            | Client       |
| --------------------------------------------------------------- | ------------ |
| [`claude-desktop.json`](claude-desktop.json)                    | Anthropic Claude Desktop |
| [`cursor.json`](cursor.json)                                    | Cursor       |
| [`vscode-mcp.json`](vscode-mcp.json)                            | VS Code MCP extensions (generic) |

## Auth — read this first

The MCP endpoint requires Django session auth (the same cookie the
HTML admin uses). Clients that can't drive a browser need a
session cookie out-of-band:

1. Log into the admin in a browser at `/admin/login/`.
2. Open DevTools → Application → Cookies. Copy `sessionid` and
   `csrftoken` for the domain.
3. Paste those values into the client config below.

For programmatic clients (Python scripts, CI jobs), see
[`../headless-client/`](../headless-client/) for a bootstrap
recipe — `examples/headless-client/bootstrap.py` does the login
flow against the quickstart project and produces a reusable cookie
jar.

A token-auth fallback (configured via
`DJANGO_ADMIN_MCP_API["TOKEN_AUTH_BACKEND"]`) is documented in the
README "Configuration" section and is the recommended path for
long-lived headless clients in production.

## What does NOT belong here

- **Working credentials.** These are templates — every cookie /
  token value is a placeholder.
- **Per-client implementation guides.** Linking to each client's
  upstream docs is enough; their UX changes faster than this repo.
