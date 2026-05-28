"""End-to-end smoke test — call the running quickstart server.

Run:

    python smoke.py [--user USERNAME] [--password PASSWORD]

It logs in via Django's session-auth form, fetches a CSRF token, then
exercises both the read-only ``GET /mcp/manifest/`` endpoint and the
JSON-RPC ``POST /mcp/`` endpoint. The output is exactly what an MCP
agent would see — copy/paste-able into Claude Desktop bug reports.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any

DEFAULT_BASE = "http://127.0.0.1:8000"


def build_opener() -> urllib.request.OpenerDirector:
    jar = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def login(opener: urllib.request.OpenerDirector, user: str, password: str, base: str) -> str:
    """Log into the Django admin and return the CSRF token cookie."""
    # First GET sets the CSRF cookie. The body is discarded — we only
    # need the cookie jar to be populated.
    opener.open(f"{base}/admin/login/").close()  # noqa: S310 — demo HTTP only.
    csrftoken = _extract_cookie(opener, "csrftoken")
    payload = urllib.parse.urlencode(
        {
            "username": user,
            "password": password,
            "csrfmiddlewaretoken": csrftoken,
            "next": "/admin/",
        }
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — demo HTTP only.
        f"{base}/admin/login/",
        data=payload,
        headers={
            "Referer": f"{base}/admin/login/",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        opener.open(req)  # noqa: S310 — demo HTTP only.
    except urllib.error.HTTPError as exc:
        # Django returns 200 on bad creds with the form re-rendered, and
        # 302 to /admin/ on success — both reach this path. Only re-raise
        # on real server errors.
        if exc.code >= 500:
            raise
    return _extract_cookie(opener, "csrftoken")


def _extract_cookie(opener: urllib.request.OpenerDirector, name: str) -> str:
    for handler in opener.handlers:
        if isinstance(handler, urllib.request.HTTPCookieProcessor):
            for cookie in handler.cookiejar:
                if cookie.name == name:
                    return cookie.value
    raise SystemExit(f"Could not find cookie {name!r} — login failed?")


def get_json(opener: urllib.request.OpenerDirector, base: str, path: str) -> Any:
    with opener.open(f"{base}{path}") as r:  # noqa: S310 — demo HTTP only.
        return json.loads(r.read())


def jsonrpc(
    opener: urllib.request.OpenerDirector,
    base: str,
    csrftoken: str,
    method: str,
    params: dict[str, Any] | None = None,
) -> Any:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — demo HTTP only.
        f"{base}/mcp/",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
            "Referer": f"{base}/",
        },
    )
    try:
        with opener.open(req) as r:  # noqa: S310 — demo HTTP only.
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()

    opener = build_opener()
    csrftoken = login(opener, args.user, args.password, args.base)

    print("=" * 60)
    print(" GET /mcp/manifest/")
    print("=" * 60)
    manifest = get_json(opener, args.base, "/mcp/manifest/")
    print(json.dumps(manifest, indent=2)[:1200])
    print("    ...")
    print()

    print("=" * 60)
    print(" POST /mcp/  method=initialize")
    print("=" * 60)
    print(json.dumps(jsonrpc(opener, args.base, csrftoken, "initialize"), indent=2))
    print()

    print("=" * 60)
    print(" POST /mcp/  method=tools/list (first 3 tools)")
    print("=" * 60)
    result = jsonrpc(opener, args.base, csrftoken, "tools/list")
    result["result"]["tools"] = result["result"]["tools"][:3]
    print(json.dumps(result, indent=2))
    print("    ...")
    print()

    print("=" * 60)
    print(" POST /mcp/  method=tools/call  name=admin.registry")
    print("=" * 60)
    call = jsonrpc(
        opener,
        args.base,
        csrftoken,
        "tools/call",
        {"name": "admin.registry", "arguments": {}},
    )
    print(json.dumps(call, indent=2)[:1500])
    print("    ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
