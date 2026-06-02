"""`admin.form_submit` — submit a form-spec's data through the same resolved form."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.tools import custom_template
from django_admin_mcp_api.tools.base import APP_LABEL
from django_admin_mcp_api.tools.base import MODEL_NAME
from django_admin_mcp_api.tools.base import Tool
from django_admin_mcp_api.tools.form_spec import _build_target as _form_spec_target
from django_admin_mcp_api.tools.form_spec import _query

if TYPE_CHECKING:
    from django.http import HttpRequest

    from django_admin_mcp_api.server.dispatch import Dispatcher
    from django_admin_mcp_api.tools.base import InterceptResult


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


def _resolves_to_custom_template(
    arguments: dict[str, Any],
    request: HttpRequest,
    dispatcher: Dispatcher,
) -> bool:
    """Pre-flight the *same* form-spec resolution this submit would target.

    We forward a GET form-spec (identical app/model/pk/query) through the
    shared resolver and inspect the renderer. This is the single source of
    truth for "is this a custom template" — we never re-detect locally. A
    resolution error (4xx/5xx, non-JSON) is treated as "not custom-template"
    so the normal forward path runs and surfaces rest-api's real error.
    """
    spec_target = _form_spec_target(arguments)
    response = dispatcher.dispatch(request=request, target=spec_target)
    body = getattr(response, "content", b"")
    if not body:
        return False
    try:
        decoded = json.loads(body)
    except (TypeError, ValueError):
        return False
    return custom_template.is_custom_template(decoded)


def _intercept(
    arguments: dict[str, Any],
    request: HttpRequest,
    dispatcher: Dispatcher,
) -> InterceptResult | None:
    """Refuse to submit a custom-template form *before* forwarding a POST (#84).

    A ``change_form_template`` / custom ``change_view`` page is opaque HTML the
    MCP client can't introspect; any field values we synthesised and POSTed
    would be wrong and the legacy view would reject them. So we resolve the
    form-spec first and, if it is a custom template, return the refusal
    discriminator with a 422 status (the request was well-formed but the target
    is not driveable) instead of building/forwarding the create/update POST.
    Every other form returns ``None`` here and follows the normal path.
    """
    if _resolves_to_custom_template(arguments, request, dispatcher):
        return custom_template.refusal(), 422
    return None


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
    intercept=_intercept,
)
