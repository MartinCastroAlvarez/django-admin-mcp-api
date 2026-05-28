"""`admin.retrieve` — detail view for one object."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import PK
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="GET",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/{arguments['pk']}/",
    )


TOOL = Tool(
    name="admin.retrieve",
    description=(
        "Return the detail-view payload for one object, including read-only fields, "
        "inline relations, and the boolean permission flags. Mirrors "
        "GET /api/v1/<app_label>/<model_name>/<pk>/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": PK,
        },
        "required": ["app_label", "model_name", "pk"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
