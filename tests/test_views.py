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
def test_get_method_is_rejected(staff_client):
    response = staff_client.get(MCP)
    assert response.status_code == 405
