"""The MCP tool catalogue.

Each module under this package declares one MCP tool. A tool is a tiny
declarative object: its name, its description, its JSON-Schema input,
and a ``build_target`` method that translates MCP arguments into a
:class:`~django_admin_mcp_api.server.dispatch.DispatchTarget` (an HTTP
shape the rest-api understands).

There is no admin logic here either — the tool's job is to validate the
arguments against the input schema and produce the dispatch target.
Everything else (auth, permissions, query, serialization) happens
inside django-admin-rest-api when the dispatcher forwards.

The exported :func:`all_tools` returns the registered tool instances in
a stable order (used by both the manifest endpoint and the MCP
``tools/list`` method).
"""

from __future__ import annotations

from django_admin_mcp_api.tools import action
from django_admin_mcp_api.tools import add_form
from django_admin_mcp_api.tools import autocomplete
from django_admin_mcp_api.tools import bulk_update
from django_admin_mcp_api.tools import create
from django_admin_mcp_api.tools import delete_preview
from django_admin_mcp_api.tools import destroy
from django_admin_mcp_api.tools import history
from django_admin_mcp_api.tools import list_objects
from django_admin_mcp_api.tools import panel
from django_admin_mcp_api.tools import recent_actions
from django_admin_mcp_api.tools import registry
from django_admin_mcp_api.tools import retrieve
from django_admin_mcp_api.tools import schema
from django_admin_mcp_api.tools import set_password
from django_admin_mcp_api.tools import update
from django_admin_mcp_api.tools.base import Tool

# Stable ordering — the manifest is a public contract; tools are listed
# in the order below regardless of import order.
_TOOLS: tuple[Tool, ...] = (
    registry.TOOL,
    schema.TOOL,
    recent_actions.TOOL,
    list_objects.TOOL,
    retrieve.TOOL,
    add_form.TOOL,
    create.TOOL,
    update.TOOL,
    destroy.TOOL,
    bulk_update.TOOL,
    autocomplete.TOOL,
    action.TOOL,
    history.TOOL,
    delete_preview.TOOL,
    set_password.TOOL,
    panel.TOOL,
)


def all_tools() -> tuple[Tool, ...]:
    """Return the registered MCP tools in stable order."""
    return _TOOLS


def by_name(name: str) -> Tool | None:
    """Look up a tool by its public MCP name. ``None`` if unknown."""
    for tool in _TOOLS:
        if tool.name == name:
            return tool
    return None
