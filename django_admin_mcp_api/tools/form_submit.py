"""`admin.form_submit` — submit a form-spec's data through the same resolved form."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool
from django_admin_mcp_api.tools.form_spec import _query


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    app = arguments["app_label"]
    model = arguments["model_name"]
    pk = arguments.get("pk")
    data = arguments.get("data") or {}
    # The companion to `admin.form_spec`: re-runs the SAME resolved
    # get_form(request, obj) through is_valid() server-side. `pk` omitted
    # → create (POST collection); `pk` given → update (PATCH instance).
    # Both already run the form through is_valid() and return per-field
    # errors under `fields[<name>]` on a 400 — request-aware validation
    # identical to the SPA and the legacy admin. The `query` is forwarded
    # so a request-aware get_form validates with the same form the
    # matching form_spec was built from.
    if pk is None or pk == "add":
        return DispatchTarget(
            method="POST", path=f"/{app}/{model}/", body=data, query=_query(arguments)
        )
    return DispatchTarget(
        method="PATCH", path=f"/{app}/{model}/{pk}/", body=data, query=_query(arguments)
    )


TOOL = Tool(
    name="admin.form_submit",
    description=(
        "Submit a form's data through the consumer's ModelAdmin.get_form(), re-running "
        "is_valid() server-side using the SAME request-aware resolution as `admin.form_spec` "
        "(pass the matching `query`). Omit `pk` to create, or give `pk` to update. On "
        "validation failure the response carries per-field errors under `fields[<name>]`. "
        "Mirrors POST /api/v1/<app_label>/<model_name>/ (create) or "
        "PATCH /api/v1/<app_label>/<model_name>/<pk>/ (update)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": {
                "type": ["string", "null"],
                "description": 'Row to update. Omit (or null / "add") to create a new object.',
            },
            "data": {
                "type": "object",
                "description": "Field name → value map, exactly as the form-spec fields expect.",
            },
            "query": {
                "type": "object",
                "description": (
                    "Querystring forwarded into the request so a request-aware get_form "
                    "validates with the same form `admin.form_spec` was built from."
                ),
            },
        },
        "required": ["app_label", "model_name", "data"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
