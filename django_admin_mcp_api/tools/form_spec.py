"""`admin.form_spec` — the ModelAdmin-resolved form for a row or the add page."""

from __future__ import annotations

from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool


def _query(arguments: dict[str, Any]) -> dict[str, str] | None:
    """Coerce the optional ``query`` arg into a ``{str: str}`` querystring.

    Forwarded into the rest-api request so a request-aware
    ``ModelAdmin.get_form(request, obj)`` (e.g. one branching on
    ``?variant=…``) resolves the same form the SPA / legacy admin would.
    """
    raw = arguments.get("query")
    if not isinstance(raw, dict) or not raw:
        return None
    return {str(k): str(v) for k, v in raw.items() if v is not None} or None


def _build_target(arguments: dict[str, Any]) -> DispatchTarget:
    app = arguments["app_label"]
    model = arguments["model_name"]
    pk = arguments.get("pk")
    # ``pk`` omitted / null / "add" → the add-view form; otherwise the
    # change-view form for that row. Same two routes as the rest-api
    # endpoint (`…/<pk>/form-spec/` and `…/add/form-spec/`).
    if pk is None or pk == "add":
        path = f"/{app}/{model}/add/form-spec/"
    else:
        path = f"/{app}/{model}/{pk}/form-spec/"
    return DispatchTarget(method="GET", path=path, query=_query(arguments))


TOOL = Tool(
    name="admin.form_spec",
    description=(
        "Return the ModelAdmin-resolved form spec for a row (or the add page when "
        "`pk` is omitted): request-aware get_form / get_fieldsets / get_readonly_fields, "
        "with each field's resolved widget mapped to a closed `widget.kind` enum and a "
        "`custom` fallback carrying the widget's dotted class path. Identical payload to "
        "the rest-api endpoint — both share one resolver, so MCP and the SPA never drift. "
        "Mirrors GET /api/v1/<app_label>/<model_name>/<pk>/form-spec/ (or /add/form-spec/)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": APP_LABEL,
            "model_name": MODEL_NAME,
            "pk": {
                "type": ["string", "null"],
                "description": (
                    'Primary key of the row to edit. Omit (or pass null / "add") for the '
                    "add-view form."
                ),
            },
            "query": {
                "type": "object",
                "description": (
                    "Querystring forwarded into the request so a request-aware get_form "
                    "(e.g. ?variant=…) resolves the matching form."
                ),
            },
        },
        "required": ["app_label", "model_name"],
        "additionalProperties": False,
    },
    build_target=_build_target,
)
