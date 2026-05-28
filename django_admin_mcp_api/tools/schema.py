"""`admin.schema` — return the full admin metadata schema."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    del arguments
    return DispatchTarget(method="GET", path="/schema/")


TOOL = Tool(
    name="admin.schema",
    description=(
        "Return the full schema document describing every model the user can see "
        "and the field/list/filter metadata for each. Mirrors GET /api/v1/schema/."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    build_target=_build_target,
)
