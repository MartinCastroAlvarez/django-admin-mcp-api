"""`admin.panel` — opt-in custom panel data for one object."""

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
        path=(
            f"/{arguments['app_label']}/{arguments['model_name']}"
            f"/{arguments['pk']}/panel/{arguments['panel_name']}/"
        ),
    )


TOOL = Tool(
    name="admin.panel",
    description=(
        "Read a custom panel for one object. The consumer declares panels "
        "directly on their ``ModelAdmin`` — ``panels = {'name': 'method_name'}`` "
        "— no rest-api mixin or subclass is required (rest-api ≥1.0.8). 404 "
        "if the admin has no panel registered under the given name. Mirrors "
        "GET /api/v1/<app_label>/<model_name>/<pk>/panel/<panel_name>/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": PK,
            "panel_name": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$",
                "description": "Name of the panel registered on the ModelAdmin.",
            },
        },
        "required": ["app_label", "model_name", "pk", "panel_name"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
