"""`admin.action` — run one of a model's registered admin actions."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="POST",
        path=(
            f"/{arguments['app_label']}/{arguments['model_name']}"
            f"/actions/{arguments['action_name']}/"
        ),
        body={"pks": arguments["pks"]},
    )


TOOL = Tool(
    name="admin.action",
    description=(
        "Run one of the model's admin actions (anything registered via "
        "ModelAdmin.actions) against the given pks. The action callable is "
        "executed by django-admin-rest-api; this layer just forwards.\n\n"
        "Each action carries a `target` of either `batch` or `detail`, derived "
        "by rest-api from the action callable's signature and surfaced on the "
        "action descriptor (visible via admin.registry / admin.list / "
        "admin.retrieve):\n"
        "  - target=`batch` (the stock Django shape): the action receives the "
        "    user-narrowed queryset; pass one or more pks.\n"
        "  - target=`detail`: the action receives a single object id; pass "
        "    exactly one entry in `pks` or rest-api returns 400.\n\n"
        "The same wire endpoint serves both shapes; the dispatch happens "
        "inside rest-api. Mirrors POST /api/v1/<app_label>/<model_name>/"
        "actions/<action_name>/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "action_name": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$",
                "description": "Admin action name (must be in ModelAdmin.actions).",
            },
            "pks": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": (
                    "Primary keys to run the action against. For target=`batch` "
                    "actions, one or more pks; for target=`detail` actions, "
                    "exactly one — check the action descriptor first."
                ),
            },
        },
        "required": ["app_label", "model_name", "action_name", "pks"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
