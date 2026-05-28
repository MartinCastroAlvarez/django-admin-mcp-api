"""`admin.set_password` — set/change the password on a user-like object."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import PK
from django_admin_mcp_api.tools.base import Tool


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    return DispatchTarget(
        method="POST",
        path=(
            f"/{arguments['app_label']}/{arguments['model_name']}" f"/{arguments['pk']}/password/"
        ),
        body={"password": arguments["password"]},
    )


TOOL = Tool(
    name="admin.set_password",
    description=(
        "Set/change the password on a model whose admin exposes a password-change "
        "form (typically User). 404 for any model whose admin has no such form. "
        "Mirrors POST /api/v1/<app_label>/<model_name>/<pk>/password/."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": PK,
            "password": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "The new password. Hashed and stored by rest-api via the consumer's "
                    "admin set-password form — never logged."
                ),
            },
        },
        "required": ["app_label", "model_name", "pk", "password"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
