"""Manifest catalogue + initialize result shape."""

from __future__ import annotations

import pytest

from django_admin_mcp_api import tools
from django_admin_mcp_api.server import manifest

EXPECTED_TOOL_NAMES = {
    "admin.registry",
    "admin.schema",
    "admin.recent_actions",
    "admin.list",
    "admin.retrieve",
    "admin.add_form",
    "admin.create",
    "admin.update",
    "admin.destroy",
    "admin.bulk_update",
    "admin.autocomplete",
    "admin.action",
    "admin.history",
    "admin.delete_preview",
    "admin.set_password",
    "admin.panel",
}


def test_initialize_result_shape():
    result = manifest.initialize_result()
    assert result["protocolVersion"] == "2024-11-05"
    assert result["serverInfo"]["name"] == "django-admin"
    assert "version" in result["serverInfo"]
    # We expose tools only — no resources / prompts / sampling.
    assert set(result["capabilities"]) == {"tools"}


def test_manifest_lists_every_tool():
    cat = {entry["name"] for entry in manifest.tools_catalogue()}
    assert cat == EXPECTED_TOOL_NAMES


def test_tool_entries_have_required_fields():
    for entry in manifest.tools_catalogue():
        assert {"name", "description", "inputSchema"} <= set(entry)
        assert entry["inputSchema"]["type"] == "object"


@pytest.mark.parametrize("tool", tools.all_tools(), ids=lambda t: t.name)
def test_each_tool_resolves_by_name(tool):
    assert tools.by_name(tool.name) is tool


def test_by_name_unknown_returns_none():
    assert tools.by_name("admin.does_not_exist") is None
