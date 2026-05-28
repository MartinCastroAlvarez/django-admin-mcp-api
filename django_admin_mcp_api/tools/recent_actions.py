"""`admin.recent_actions` — the signed-in user's own LogEntry feed."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    del arguments
    return DispatchTarget(method="GET", path="/recent-actions/")


TOOL = Tool(
    name="admin.recent_actions",
    description=(
        "Return the signed-in user's own admin LogEntry history (the 'Recent actions' panel). "
        "Mirrors GET /api/v1/recent-actions/ in django-admin-rest-api."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    build_target=_build_target,
)
