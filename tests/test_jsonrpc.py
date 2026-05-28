"""JSON-RPC envelope parsing."""

from __future__ import annotations

import pytest

from django_admin_mcp_api.server import errors
from django_admin_mcp_api.server import jsonrpc


def test_parse_minimum_valid_request():
    rpc = jsonrpc.parse_request({"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert rpc.method == "ping"
    assert rpc.id == 1
    assert rpc.params == {}


def test_parse_rejects_wrong_version():
    with pytest.raises(jsonrpc.JsonRpcError) as info:
        jsonrpc.parse_request({"jsonrpc": "1.0", "id": 1, "method": "ping"})
    assert info.value.code == errors.INVALID_REQUEST


def test_parse_rejects_non_object_envelope():
    with pytest.raises(jsonrpc.JsonRpcError) as info:
        jsonrpc.parse_request([])
    assert info.value.code == errors.INVALID_REQUEST


def test_parse_rejects_missing_method():
    with pytest.raises(jsonrpc.JsonRpcError) as info:
        jsonrpc.parse_request({"jsonrpc": "2.0", "id": 1})
    assert info.value.code == errors.INVALID_REQUEST


def test_parse_rejects_non_object_params():
    with pytest.raises(jsonrpc.JsonRpcError) as info:
        jsonrpc.parse_request({"jsonrpc": "2.0", "id": 1, "method": "x", "params": []})
    assert info.value.code == errors.INVALID_PARAMS


def test_success_envelope_shape():
    env = jsonrpc.success(7, {"ok": True})
    assert env == {"jsonrpc": "2.0", "id": 7, "result": {"ok": True}}


def test_failure_envelope_shape():
    env = jsonrpc.failure(7, errors.METHOD_NOT_FOUND)
    assert env["jsonrpc"] == "2.0"
    assert env["id"] == 7
    assert env["error"]["code"] == errors.METHOD_NOT_FOUND
    assert env["error"]["message"] == "Method not found"
