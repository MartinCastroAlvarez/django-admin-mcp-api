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


def initialize_result(requested_protocol: str | None = None) -> dict[str, Any]:
    """Build the result payload for the MCP ``initialize`` method.

    ``requested_protocol`` is the client's ``params.protocolVersion`` (#81).
    This server supports exactly one protocol version, so negotiation is
    trivial: we always respond with our configured ``PROTOCOL_VERSION``.
    The requested version is read by the view (which logs a mismatch);
    we keep echoing the single supported version here. When multi-version
    support lands, this is the place to pick a compatible version from the
    requested one rather than always returning the configured default.
    """
    del requested_protocol  # negotiation is logged by the caller; see docstring.
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


# Memoised base catalogue (#82a). The catalogue is immutable for a given
# DISABLED_TOOLS setting — tools are frozen dataclasses registered at
# import time and ``listChanged`` is False. Rebuilding 18 manifest entries
# on every tools/list, GET /, and GET /manifest/ is wasted work, so we
# cache the rendered list keyed on the (sorted, hashable) DISABLED_TOOLS
# tuple. The cache key means an override_settings flip in tests still
# returns the correct (re-rendered) catalogue rather than a stale one.
#
# NOTE: this caches the *base* (per-DISABLED_TOOLS) catalogue, not a
# per-user view. The catalogue is intentionally static and not
# permission-filtered (see #77 / docs/api-contract.md §4.2 + threat-model);
# if per-user filtering is ever introduced it must layer on top of this
# base — the base is what's globally cacheable.
_catalogue_cache: dict[tuple[str, ...], list[dict[str, Any]]] = {}


def tools_catalogue() -> list[dict[str, Any]]:
    """Build the ``tools/list`` result payload.

    Honours ``DJANGO_ADMIN_MCP_API.DISABLED_TOOLS`` — suppressed tools
    do not appear. (Closes #41 + #48.) Memoised per DISABLED_TOOLS (#82a).
    """
    key = tuple(sorted(conf.get("DISABLED_TOOLS") or ()))
    cached = _catalogue_cache.get(key)
    if cached is None:
        cached = [tool.to_manifest_entry() for tool in tools.enabled_tools()]
        _catalogue_cache[key] = cached
    return cached


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
