"""Issue an MCP JSON-RPC call against a Django admin using saved cookies.

Usage:

    python call.py /tmp/cookies.json initialize
    python call.py /tmp/cookies.json tools/list
    python call.py /tmp/cookies.json tools/call admin.registry
    python call.py /tmp/cookies.json tools/call admin.retrieve \\
        '{"app_label":"auth","model_name":"user","pk":"1"}'

Stdlib-only on purpose — ``bootstrap.py`` uses ``httpx`` for
readability, but the operational client should run anywhere Python
runs.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def call(
    cookies_path: str,
    method: str,
    tool: str | None = None,
    arguments: dict | None = None,
    mcp_path: str = "/mcp/",
) -> dict:
    with open(cookies_path, "r", encoding="utf-8") as f:
        c = json.load(f)
    url = c["base"].rstrip("/") + mcp_path
    params: dict = {}
    if method == "tools/call":
        if not tool:
            raise SystemExit("tools/call requires a tool name.")
        params = {"name": tool, "arguments": arguments or {}}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — demo HTTP call.
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"sessionid={c['sessionid']}; csrftoken={c['csrftoken']}",
            "X-CSRFToken": c["csrftoken"],
            "Referer": c["base"],
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cookies", help="Path to the JSON cookies file from bootstrap.py")
    parser.add_argument("method", help="MCP method: initialize, tools/list, tools/call")
    parser.add_argument("tool", nargs="?", help="Tool name (for tools/call)")
    parser.add_argument("arguments", nargs="?", help="JSON args object (for tools/call)")
    args = parser.parse_args()

    arguments = json.loads(args.arguments) if args.arguments else None
    response = call(args.cookies, args.method, args.tool, arguments)
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
