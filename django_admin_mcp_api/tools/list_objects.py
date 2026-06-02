"""`admin.list` — list-view objects for one model."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    app = arguments["app_label"]
    model = arguments["model_name"]
    query = {
        k: str(v)
        for k, v in arguments.items()
        if k not in {"app_label", "model_name"} and v is not None
    }
    return DispatchTarget(method="GET", path=f"/{app}/{model}/", query=query or None)


TOOL = Tool(
    name="admin.list",
    description=(
        "Return one page of list-view results for a model, honouring the consumer's "
        "ModelAdmin queryset, list_display, list_filter, ordering and search. "
        "Mirrors GET /api/v1/<app_label>/<model_name>/ in django-admin-rest-api.\n\n"
        "This tool is an intentional changelist passthrough: unlike every other tool, "
        "its schema is open (additionalProperties), so any extra key is forwarded "
        "verbatim as a query parameter to match arbitrary ModelAdmin.list_filter "
        "fields. Consequently a typo'd filter key is NOT schema-caught here — it is "
        "forwarded and silently ignored by rest-api if unrecognised."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "page": {"type": "integer", "minimum": 1, "description": "1-indexed page number."},
            "page_size": {"type": "integer", "minimum": 1, "maximum": 200},
            "search": {"type": "string", "description": "Free-text search query."},
            "ordering": {
                "type": "string",
                "description": "Comma-separated field names; leading '-' for descending.",
            },
        },
        "required": ["app_label", "model_name"],
        "additionalProperties": True,
    },
    build_target=_build_target,
)
