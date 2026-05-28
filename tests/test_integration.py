"""End-to-end integration tests against the real django-admin-rest-api.

These tests swap in :class:`RestApiDispatcher` (the production default)
and exercise a couple of read-only tools to confirm the wire bridges
all the way through to rest-api's view set. They use Django's built-in
``auth`` app — no example models needed.
"""

from __future__ import annotations

import json

import pytest
from django.test import override_settings

from tests.helpers import jsonrpc_call

MCP = "/mcp/"

# Drop the FakeDispatcher override so the default RestApiDispatcher is
# used. Everything else in tests/test_project/settings.py applies.
_REAL_DISPATCHER = override_settings(DJANGO_ADMIN_MCP_API={})


def _decode(response):
    return json.loads(response.content.decode("utf-8"))


@pytest.mark.django_db
def test_registry_tool_reaches_rest_api(staff_client):
    """admin.registry → rest-api RegistryView.

    The default Django admin registers ``auth.User`` and ``auth.Group``
    so we expect at least these two apps in the returned registry.
    """
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": "admin.registry", "arguments": {}}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert "result" in body, body
    content = body["result"]["content"][0]["json"]
    # rest-api returns a registry document; we don't pin the exact shape
    # (that's rest-api's contract), only that it is non-empty JSON.
    assert content, "Registry result was empty — rest-api wiring is broken"


@pytest.mark.django_db
def test_schema_tool_reaches_rest_api(staff_client):
    """admin.schema → rest-api SchemaView."""
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": "admin.schema", "arguments": {}}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert "result" in body, body


@pytest.mark.django_db
def test_unknown_app_tool_returns_isError(staff_client):
    """A tool call for a model that doesn't exist surfaces rest-api's 404.

    The MCP envelope is still a JSON-RPC ``result`` (the call itself
    succeeded — we *got* an answer from rest-api). The ``isError`` flag
    inside the result content marks the upstream 4xx for the agent.
    """
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.retrieve",
                    "arguments": {
                        "app_label": "nonexistent",
                        "model_name": "model",
                        "pk": "1",
                    },
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert body["result"]["isError"] is True
    assert body["result"]["status"] >= 400
