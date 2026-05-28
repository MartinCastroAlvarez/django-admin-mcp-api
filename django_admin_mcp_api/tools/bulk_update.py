"""`admin.bulk_update` — apply the same patch to multiple objects."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="PATCH",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/bulk/",
        body={"pks": arguments["pks"], "data": arguments["data"]},
    )


TOOL = Tool(
    name="admin.bulk_update",
    description=(
        "Apply the same field updates to multiple objects in one round-trip. "
        "Mirrors PATCH /api/v1/<app_label>/<model_name>/bulk/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pks": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Primary keys of the target objects.",
            },
            "data": {
                "type": "object",
                "description": "Field name → new value map; applied to every pk.",
            },
        },
        "required": ["app_label", "model_name", "pks", "data"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
