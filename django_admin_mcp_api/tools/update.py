"""`admin.update` — partial update for one object."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import PK
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="PATCH",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/{arguments['pk']}/",
        body=arguments.get("data") or {},
    )


TOOL = Tool(
    name="admin.update",
    description=(
        "Partial-update one object through the consumer's ModelAdmin.get_form(). "
        "Mirrors PATCH /api/v1/<app_label>/<model_name>/<pk>/. Writes to "
        "exclude/readonly fields are rejected by rest-api as 400."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": PK,
            "data": {
                "type": "object",
                "description": "Field name → new value map. Only changed fields need be present.",
            },
        },
        "required": ["app_label", "model_name", "pk", "data"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
