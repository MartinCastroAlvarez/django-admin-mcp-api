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
    "admin.form_spec",
    "admin.create",
    "admin.update",
    "admin.form_submit",
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


def test_disabled_tools_filters_catalogue():
    """Closes #41 + #48 — DISABLED_TOOLS suppresses tools from the manifest."""
    from django.test import override_settings

    with override_settings(
        DJANGO_ADMIN_MCP_API={"DISABLED_TOOLS": ("admin.destroy", "admin.bulk_update")}
    ):
        names = {t.name for t in tools.enabled_tools()}
        catalogue = {entry["name"] for entry in manifest.tools_catalogue()}
    assert "admin.destroy" not in names
    assert "admin.bulk_update" not in names
    assert "admin.destroy" not in catalogue
    assert "admin.bulk_update" not in catalogue
    # Non-suppressed tools still present.
    assert "admin.list" in names


def test_disabled_tools_by_name_returns_none():
    """A disabled tool is unknown — by_name returns None so tools/call 404s."""
    from django.test import override_settings

    with override_settings(DJANGO_ADMIN_MCP_API={"DISABLED_TOOLS": ("admin.destroy",)}):
        assert tools.by_name("admin.destroy") is None
        # Sibling tool unaffected.
        assert tools.by_name("admin.list") is not None


def test_all_tools_bypasses_disabled_filter():
    """all_tools() returns the raw set — used by checks + tests."""
    from django.test import override_settings

    with override_settings(DJANGO_ADMIN_MCP_API={"DISABLED_TOOLS": ("admin.destroy",)}):
        raw = {t.name for t in tools.all_tools()}
    assert "admin.destroy" in raw


def test_readme_documents_correct_tool_count():
    """Closes #76 — the README "The N tools" heading must match all_tools().

    The heading hard-codes a count; the #70 form_spec/form_submit additions
    bumped it from 16 to 18. This test pins the documented number to
    ``len(tools.all_tools())`` so the heading can't silently drift again.
    """
    import pathlib
    import re

    readme = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text(encoding="utf-8")
    match = re.search(r"^##\s+.*?The (\d+) tools", text, flags=re.MULTILINE)
    assert match is not None, "Could not find 'The N tools' heading in README.md"
    documented = int(match.group(1))
    assert documented == len(tools.all_tools())


def test_pk_schema_is_bounded():
    """Closes #79 — the shared PK string schema carries length + pattern bounds."""
    from django_admin_mcp_api.tools.base import PK

    assert PK["maxLength"] == 256
    assert PK["minLength"] == 1
    # The pattern forbids path-structural characters so a pk cannot reshape
    # the rest-api dispatch path it is interpolated into.
    assert PK["pattern"] == "^[^/?#]+$"


def test_bulk_pks_arrays_are_bounded():
    """Closes #79 — admin.action / admin.bulk_update cap the pks array size."""
    from django_admin_mcp_api.tools import action
    from django_admin_mcp_api.tools import bulk_update

    for tool in (action.TOOL, bulk_update.TOOL):
        pks = tool.input_schema["properties"]["pks"]
        assert pks["minItems"] == 1
        assert pks["maxItems"] == 1000
        # Items are bounded strings, not free strings.
        assert pks["items"]["maxLength"] == 256
        assert pks["items"]["pattern"] == "^[^/?#]+$"
