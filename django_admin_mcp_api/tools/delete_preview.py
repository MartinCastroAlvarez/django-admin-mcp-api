"""`admin.delete_preview` — cascade preview before a DELETE."""

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
            f"/{arguments['pk']}/delete-preview/"
        ),
    )


TOOL = Tool(
    name="admin.delete_preview",
    description=(
        "Preview the cascade / protected impact of deleting one object before "
        "actually calling admin.destroy. Read-only. Mirrors "
        "GET /api/v1/<app_label>/<model_name>/<pk>/delete-preview/."
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
