"""`admin.registry` — list every registered model the user can see."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    del arguments  # no inputs.
    return DispatchTarget(method="GET", path="/registry/")


TOOL = Tool(
    name="admin.registry",
    description=(
        "List every model registered on the AdminSite that the authenticated user "
        "is allowed to see. Mirrors GET /api/v1/registry/ in django-admin-rest-api."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    build_target=_build_target,
)
