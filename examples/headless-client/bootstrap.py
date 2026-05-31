"""Log into a Django site programmatically and dump the session cookies.

This is the standard Django session-auth flow, scripted. Useful for
headless MCP clients (scripts, CI jobs, services) that need to drive
the MCP endpoint without a browser to acquire the session.

Run:

    python bootstrap.py \\
        --base     https://your-host/ \\
        --user     admin \\
        --password "$ADMIN_PASSWORD" \\
        --out      /tmp/cookies.json

The output file is a small JSON document with ``sessionid``,
``csrftoken``, ``base``, and ``captured_at`` — re-use it from
``call.py`` or any other client that can attach a Cookie header.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from getpass import getpass

try:
    import httpx
except ImportError as exc:  # pragma: no cover — friendly error for the example.
    print(
        "This example requires httpx. Install with:\n\n" "    pip install httpx\n",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


def login(base: str, user: str, password: str) -> dict[str, str]:
    """Run the Django session-auth login flow, return the cookies."""
    login_path = base.rstrip("/") + "/admin/login/"
    with httpx.Client(follow_redirects=False, timeout=10.0) as client:
        # 1. GET the login page to receive a CSRF cookie.
        get = client.get(login_path)
        if get.status_code >= 400:
            raise SystemExit(f"GET {login_path} returned {get.status_code}")
        csrf = client.cookies.get("csrftoken")
        if not csrf:
            raise SystemExit("No csrftoken cookie issued — is this a Django admin URL?")

        # 2. POST the login form with the CSRF token.
        post = client.post(
            login_path,
            data={
                "username": user,
                "password": password,
                "csrfmiddlewaretoken": csrf,
                "next": "/admin/",
            },
            headers={"Referer": login_path},
        )
        # Django redirects on success (302 to /admin/); the form re-renders
        # on failure with status 200 and a ``form-errors`` block.
        if post.status_code == 200:
            raise SystemExit(
                "Login form re-rendered — credentials probably wrong. " "Bootstrap failed."
            )
        session = client.cookies.get("sessionid")
        if not session:
            raise SystemExit("No sessionid cookie issued after login.")
        # Django re-issues the CSRF cookie after login.
        csrf = client.cookies.get("csrftoken", csrf)
    return {"sessionid": session, "csrftoken": csrf}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="Django site origin, e.g. https://host/")
    parser.add_argument("--user", required=True)
    parser.add_argument(
        "--password",
        default=None,
        help="Password (prompted on stdin if omitted; never log this value).",
    )
    parser.add_argument(
        "--out",
        default="/tmp/cookies.json",  # noqa: S108 — example default; pass --out for real use.
        help="Path to write the cookies file (default /tmp/cookies.json).",
    )
    args = parser.parse_args()

    password = args.password or getpass("Password: ")
    cookies = login(args.base, args.user, password)
    payload = {
        "base": args.base.rstrip("/"),
        "sessionid": cookies["sessionid"],
        "csrftoken": cookies["csrftoken"],
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {args.out}")
    print(f"  base       : {payload['base']}")
    print(f"  sessionid  : {payload['sessionid'][:8]}…")
    print(f"  csrftoken  : {payload['csrftoken'][:8]}…")
    print(f"  captured_at: {payload['captured_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
