"""Test helpers shared across the suite.

The :class:`FakeDispatcher` echoes the inbound :class:`DispatchTarget`
back as a JSON ``HttpResponse``. That lets tests assert the *exact*
HTTP shape we would have forwarded to django-admin-rest-api, without
needing rest-api to be installed.

Important: nothing here should be imported from the shipped package
other than the dispatcher protocol — tests are not allowed to teach
the production code about themselves.
"""

from __future__ import annotations

import json

from django.http import HttpRequest
from django.http import HttpResponseBase
from django.http import JsonResponse

from django_admin_mcp_api.server.dispatch import DispatchTarget


class FakeDispatcher:
    """Echo-back dispatcher used by the test suite."""

    def dispatch(
        self,
        *,
        request: HttpRequest,
        target: DispatchTarget,
    ) -> HttpResponseBase:
        return JsonResponse(
            {
                "echoed": True,
                "user": getattr(request.user, "username", None),
                "method": target.method,
                "path": target.path,
                "body": target.body,
                "query": target.query,
            }
        )


def make_fake_dispatcher() -> FakeDispatcher:
    """Factory used by ``DJANGO_ADMIN_MCP_API['DISPATCHER_FACTORY']``."""
    return FakeDispatcher()


def jsonrpc_call(method: str, params: dict | None = None, request_id: int = 1) -> bytes:
    """Build a JSON-RPC 2.0 request body for the test client."""
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
    ).encode("utf-8")
