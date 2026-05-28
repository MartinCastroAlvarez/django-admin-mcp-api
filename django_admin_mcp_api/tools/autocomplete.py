"""`admin.autocomplete` — autocomplete suggestions for a related model."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    query: dict[str, str] = {}
    if "q" in arguments and arguments["q"] is not None:
        query["q"] = str(arguments["q"])
    return DispatchTarget(
        method="GET",
        path=f"/{arguments['app_label']}/{arguments['model_name']}/autocomplete/",
        query=query or None,
    )


TOOL = Tool(
    name="admin.autocomplete",
    description=(
        "Return autocomplete suggestions for a model the consumer's ModelAdmin marks "
        "as autocomplete-enabled. Mirrors "
        "GET /api/v1/<app_label>/<model_name>/autocomplete/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "q": {"type": "string", "description": "Search query."},
        },
        "required": ["app_label", "model_name"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
