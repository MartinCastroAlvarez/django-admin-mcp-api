"""HTTP-level view tests against the test project."""

from __future__ import annotations

import json

import pytest

from django_admin_mcp_api.server import errors
from tests.helpers import jsonrpc_call

MCP = "/mcp/"
MANIFEST = "/mcp/manifest/"


def _decode(response):
    return json.loads(response.content.decode("utf-8"))


# -- manifest endpoint -----------------------------------------------------


@pytest.mark.django_db
def test_manifest_anonymous_is_401(anon_client):
    response = anon_client.get(MANIFEST)
    assert response.status_code == 401


@pytest.mark.django_db
def test_manifest_non_staff_is_403(regular_client):
    response = regular_client.get(MANIFEST)
    assert response.status_code == 403


@pytest.mark.django_db
def test_manifest_staff_returns_catalogue(staff_client):
    response = staff_client.get(MANIFEST)
    assert response.status_code == 200
    body = _decode(response)
    assert body["server"]["name"] == "django-admin"
    assert any(t["name"] == "admin.list" for t in body["tools"])


@pytest.mark.django_db
def test_manifest_post_returns_405(staff_client):
    response = staff_client.post(MANIFEST)
    assert response.status_code == 405


# -- MCP endpoint: auth gates ---------------------------------------------


@pytest.mark.django_db
def test_mcp_anonymous_is_401(anon_client):
    response = anon_client.post(
        MCP,
        data=jsonrpc_call("initialize"),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_mcp_non_staff_is_403(regular_client):
    response = regular_client.post(
        MCP,
        data=jsonrpc_call("initialize"),
        content_type="application/json",
    )
    assert response.status_code == 403


# -- MCP endpoint: protocol -----------------------------------------------


@pytest.mark.django_db
def test_initialize_returns_server_info(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call("initialize"),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = _decode(response)
    assert body["result"]["protocolVersion"] == "2024-11-05"
    assert body["result"]["serverInfo"]["name"] == "django-admin"


@pytest.mark.django_db
def test_tools_list_returns_all_tools(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call("tools/list"),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = _decode(response)
    names = {t["name"] for t in body["result"]["tools"]}
    assert "admin.registry" in names
    assert "admin.panel" in names
    assert len(names) == 16


@pytest.mark.django_db
def test_unknown_method_is_method_not_found(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call("not_a_method"),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.METHOD_NOT_FOUND


@pytest.mark.django_db
def test_unknown_tool_is_method_not_found(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call("tools/call", {"name": "admin.does_not_exist", "arguments": {}}),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.METHOD_NOT_FOUND


@pytest.mark.django_db
def test_tools_call_missing_required_arg_is_invalid_params(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call("tools/call", {"name": "admin.retrieve", "arguments": {}}),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.INVALID_PARAMS
    # Error message names the first missing field (json-schema 'required' check).
    assert "app_label" in body["error"]["message"]


@pytest.mark.django_db
def test_tools_call_wrong_type_is_invalid_params(staff_client):
    """A value with the wrong JSON type fails at the schema layer, not rest-api."""
    response = staff_client.post(
        MCP,
        data=jsonrpc_call(
            "tools/call",
            {
                "name": "admin.list",
                "arguments": {
                    "app_label": "auth",
                    "model_name": "user",
                    "page": "not-an-int",  # schema says integer
                },
            },
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.INVALID_PARAMS
    assert "/page" in body["error"]["message"]


@pytest.mark.django_db
def test_tools_call_additional_property_rejected(staff_client):
    """A tool whose schema is closed (additionalProperties: false) rejects extras.

    admin.retrieve's schema has `additionalProperties: false`, so a stray
    ``"extra"`` key must be flagged here rather than silently forwarded.
    """
    response = staff_client.post(
        MCP,
        data=jsonrpc_call(
            "tools/call",
            {
                "name": "admin.retrieve",
                "arguments": {
                    "app_label": "auth",
                    "model_name": "user",
                    "pk": "1",
                    "extra": "should-be-rejected",
                },
            },
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.INVALID_PARAMS
    assert "extra" in body["error"]["message"]


@pytest.mark.django_db
def test_tools_call_pattern_violation_is_invalid_params(staff_client):
    """app_label must match ``^[a-z][a-z0-9_]*$`` — uppercase rejected."""
    response = staff_client.post(
        MCP,
        data=jsonrpc_call(
            "tools/call",
            {
                "name": "admin.retrieve",
                "arguments": {"app_label": "Auth", "model_name": "user", "pk": "1"},
            },
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.INVALID_PARAMS
    assert "/app_label" in body["error"]["message"]


@pytest.mark.django_db
def test_tools_call_forwards_to_dispatcher(staff_client):
    response = staff_client.post(
        MCP,
        data=jsonrpc_call(
            "tools/call",
            {
                "name": "admin.retrieve",
                "arguments": {"app_label": "auth", "model_name": "user", "pk": "1"},
            },
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = _decode(response)
    echoed = body["result"]["content"][0]["json"]
    assert echoed["method"] == "GET"
    assert echoed["path"] == "/auth/user/1/"
    assert echoed["user"] == "staff"


@pytest.mark.django_db
def test_parse_error_on_bad_json(staff_client):
    response = staff_client.post(MCP, data=b"not-json", content_type="application/json")
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.PARSE_ERROR


@pytest.mark.django_db
def test_get_returns_landing_json(staff_client):
    """Closes #39 — GET / returns a JSON landing summarising the server."""
    response = staff_client.get(MCP, HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    body = _decode(response)
    assert body["server"]["name"] == "django-admin"
    assert body["protocolVersion"] == "2024-11-05"
    assert isinstance(body["tools_count"], int)
    assert body["manifest_url"].endswith("/manifest/")


@pytest.mark.django_db
def test_get_returns_landing_html_for_browsers(staff_client):
    """Closes #39 — Accept: text/html returns a small HTML page."""
    response = staff_client.get(MCP, HTTP_ACCEPT="text/html")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    html = response.content.decode("utf-8")
    assert "MCP server" in html
    # frame-busting header inside the HTML — protects against clickjacking
    # if the consumer doesn't already set X-Frame-Options at the proxy.
    assert "X-Frame-Options" in html
    assert "manifest/" in html


@pytest.mark.django_db
def test_get_landing_anonymous_is_401(anon_client):
    response = anon_client.get(MCP)
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_landing_non_staff_is_403(regular_client):
    response = regular_client.get(MCP)
    assert response.status_code == 403


@pytest.mark.django_db
def test_oversized_body_returns_413(staff_client):
    """Closes #46 — bodies above the MCP envelope limit are rejected.

    The default limit is 256 KiB; we send 300 KiB of zeroes (which
    parses as one JSON-RPC envelope wrapping a giant string).
    """
    huge = (
        b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"junk":"'
        + b"x" * (300 * 1024)
        + b'"}}'
    )
    response = staff_client.post(MCP, data=huge, content_type="application/json")
    assert response.status_code == 413
    body = _decode(response)
    assert body["error"]["code"] == errors.INVALID_REQUEST


@pytest.mark.django_db
def test_dispatcher_upstream_exceptions_caught_into_jsonrpc_envelope(staff_client):
    """Closes #45 — UnknownRestApiPath / UnsupportedDispatchMethod don't 500.

    A dispatcher that raises any of the documented exception types
    should surface as a JSON-RPC envelope error, not a Django 500.
    """
    from unittest.mock import patch

    from django_admin_mcp_api.server.dispatch import UnknownRestApiPath

    with patch("django_admin_mcp_api.server.views.get_dispatcher") as gd:
        gd.return_value.dispatch.side_effect = UnknownRestApiPath("/some-path/")
        response = staff_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.retrieve",
                    "arguments": {"app_label": "auth", "model_name": "user", "pk": "1"},
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.SERVER_ERROR_UPSTREAM


@pytest.mark.django_db
def test_novel_dispatch_error_subclass_caught_into_jsonrpc_envelope(staff_client):
    """Closes #67 — a brand-new DispatchError subclass still maps to UPSTREAM.

    The view catches the shared :class:`DispatchError` base, so a
    dispatcher exception type that did not exist when the view was
    written is handled the same way (no Django 500).
    """
    from unittest.mock import patch

    from django_admin_mcp_api.server.dispatch import DispatchError

    class NovelDispatchError(DispatchError):
        """A subclass the view has never seen before."""

    with patch("django_admin_mcp_api.server.views.get_dispatcher") as gd:
        gd.return_value.dispatch.side_effect = NovelDispatchError("boom")
        response = staff_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.retrieve",
                    "arguments": {"app_label": "auth", "model_name": "user", "pk": "1"},
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"]["code"] == errors.SERVER_ERROR_UPSTREAM


@pytest.mark.django_db
def test_tools_call_emits_structured_log(staff_client, caplog):
    """Closes #47 — every tools/call emits a structured INFO log."""
    import logging

    with caplog.at_level(logging.INFO, logger="django_admin_mcp_api.server.views"):
        response = staff_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.retrieve",
                    "arguments": {"app_label": "auth", "model_name": "user", "pk": "1"},
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 200
    # exactly one mcp.tools_call record per request
    records = [r for r in caplog.records if r.message == "mcp.tools_call"]
    assert len(records) == 1
    record = records[0]
    assert getattr(record, "tool", None) == "admin.retrieve"
    assert getattr(record, "user", None) == "staff"
    assert getattr(record, "status", None) == 200
