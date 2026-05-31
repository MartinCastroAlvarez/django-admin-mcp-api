"""Build the MCP server descriptor + tool catalogue."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api import __version__
from django_admin_mcp_api import conf
from django_admin_mcp_api import tools


def server_info() -> dict[str, str]:
    """Return the MCP ``initialize`` server-info block."""
    return {
        "name": conf.get("SERVER_NAME"),
        "version": conf.get("SERVER_VERSION") or __version__,
    }


def initialize_result() -> dict[str, Any]:
    """Build the result payload for the MCP ``initialize`` method."""
    return {
        "protocolVersion": conf.get("PROTOCOL_VERSION"),
        "serverInfo": server_info(),
        # We expose tools but no resources/prompts/sampling — those are
        # not in scope for this adapter (and would require new code in
        # django-admin-rest-api, which is out of bounds for this package).
        "capabilities": {
            "tools": {"listChanged": False},
        },
    }


def tools_catalogue() -> list[dict[str, Any]]:
    """Build the ``tools/list`` result payload.

    Honours ``DJANGO_ADMIN_MCP_API.DISABLED_TOOLS`` — suppressed tools
    do not appear. (Closes #41 + #48.)
    """
    return [tool.to_manifest_entry() for tool in tools.enabled_tools()]


def manifest() -> dict[str, Any]:
    """Build the read-only GET /manifest/ document.

    This is *not* part of the MCP spec — it's a curl-friendly view of
    the same content for humans and dashboards. The MCP-spec-correct
    catalogue is what ``tools/list`` returns; this endpoint wraps it
    with server metadata so a single GET gives the full picture.
    """
    return {
        "server": server_info(),
        "protocolVersion": conf.get("PROTOCOL_VERSION"),
        "tools": tools_catalogue(),
    }
