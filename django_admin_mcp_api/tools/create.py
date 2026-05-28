"""`admin.create` — create one object."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="POST",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/",
        body=arguments.get("data") or {},
    )


TOOL = Tool(
    name="admin.create",
    description=(
        "Create a new object through the consumer's ModelAdmin.get_form(). Validation, "
        "save-model hooks, and inline-formset handling are owned by django-admin-rest-api. "
        "Mirrors POST /api/v1/<app_label>/<model_name>/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "data": {
                "type": "object",
                "description": (
                    "Field name → value map, exactly as POSTed to the rest-api create endpoint."
                ),
            },
        },
        "required": ["app_label", "model_name", "data"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
