"""`admin.add_form` — field descriptors for the create page."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="GET",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/add/",
    )


TOOL = Tool(
    name="admin.add_form",
    description=(
        "Return the create-page field descriptors for a new object: which fields are "
        "writable, their widgets, initial values, choices, and validators. Mirrors "
        "GET /api/v1/<app_label>/<model_name>/add/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
        },
        "required": ["app_label", "model_name"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
