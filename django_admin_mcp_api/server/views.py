"""Django views — the MCP HTTP entry points.

Two views:

* :class:`McpEndpointView` (POST) — single JSON-RPC entry point that
  handles ``initialize``, ``tools/list``, and ``tools/call``. CSRF is
  enforced by Django middleware; no view bypasses it.
* :class:`ManifestView` (GET) — read-only catalogue document for curl/
  dashboards. Same auth gate as the JSON-RPC endpoint.

Both views are intentionally tiny. They do exactly three things:

1. Apply the auth gate (delegated to django-admin-rest-api once it
   ships; until then, ``staff_required_or_403`` here is the minimum
   placeholder so the gate exists from day one).
2. Parse the request envelope.
3. Hand off to :func:`~django_admin_mcp_api.server.dispatch.get_dispatcher`.

They do *not* serialise models, query the database, or evaluate
permissions beyond the staff gate. All of that is rest-api's job.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import jsonschema
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic import View

from django_admin_mcp_api import conf
from django_admin_mcp_api import tools
from django_admin_mcp_api.server import errors
from django_admin_mcp_api.server import jsonrpc
from django_admin_mcp_api.server import manifest
from django_admin_mcp_api.server.dispatch import Dispatcher
from django_admin_mcp_api.server.dispatch import UnknownRestApiPath
from django_admin_mcp_api.server.dispatch import UnsupportedDispatchMethod
from django_admin_mcp_api.server.dispatch import get_dispatcher

# One module-level logger; consumers wire it into their log aggregation
# under the name ``django_admin_mcp_api.server.views``. We never log
# request bodies (could contain passwords / PII) — only the structural
# fields ``user``, ``tool``, ``status``, ``error_code``. Closes #47.
_logger = logging.getLogger(__name__)


def _auth_gate(request: HttpRequest) -> HttpResponse | None:
    """Minimum auth gate.

    Returns a 401/403 :class:`HttpResponse` if the request is not
    allowed; ``None`` if the dispatch should proceed. The *real* gate
    is in django-admin-rest-api — this is only the "is the user even
    signed in as staff" baseline that lets us fail fast before
    constructing a forward.
    """
    if conf.get("ALLOW_ANONYMOUS"):
        # Internal test-only escape hatch — NOT documented in any
        # user-facing doc on purpose. The only caller flipping this is
        # the test suite via ``override_settings``. Setting it True in
        # production removes the staff gate entirely; SECURITY.md §2
        # rule 4 forbids it.
        return None
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        _logger.warning("mcp.auth.unauthenticated", extra={"path": request.path})
        return JsonResponse(
            jsonrpc.failure(None, errors.SERVER_ERROR_UNAUTHENTICATED),
            status=401,
        )
    if not getattr(user, "is_staff", False):
        _logger.warning(
            "mcp.auth.forbidden",
            extra={"path": request.path, "user": getattr(user, "username", None)},
        )
        return JsonResponse(
            jsonrpc.failure(None, errors.SERVER_ERROR_FORBIDDEN),
            status=403,
        )
    return None


def _handle_jsonrpc(
    request: HttpRequest,
    payload: dict[str, Any],
    dispatcher: Dispatcher,
) -> dict[str, Any]:
    """Run one parsed JSON-RPC payload, return the envelope to send back."""
    try:
        rpc = jsonrpc.parse_request(payload)
    except jsonrpc.JsonRpcError as exc:
        return jsonrpc.failure(exc.request_id, exc.code, exc.message, exc.data)

    if rpc.method == "initialize":
        return jsonrpc.success(rpc.id, manifest.initialize_result())

    if rpc.method == "tools/list":
        return jsonrpc.success(rpc.id, {"tools": manifest.tools_catalogue()})

    if rpc.method == "tools/call":
        return _handle_tools_call(request, rpc, dispatcher)

    return jsonrpc.failure(rpc.id, errors.METHOD_NOT_FOUND, f"Unknown method {rpc.method!r}")


def _handle_tools_call(
    request: HttpRequest,
    rpc: jsonrpc.JsonRpcRequest,
    dispatcher: Dispatcher,
) -> dict[str, Any]:
    """Handle the ``tools/call`` MCP method."""
    name = rpc.params.get("name")
    if not isinstance(name, str):
        return jsonrpc.failure(rpc.id, errors.INVALID_PARAMS, "params.name must be a string")
    arguments = rpc.params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return jsonrpc.failure(rpc.id, errors.INVALID_PARAMS, "params.arguments must be an object")
    tool = tools.by_name(name)
    if tool is None:
        return jsonrpc.failure(rpc.id, errors.METHOD_NOT_FOUND, f"Unknown tool {name!r}")

    # Validate the arguments against the tool's declared JSON Schema
    # *before* we ask the tool to build a DispatchTarget. That lets us
    # return INVALID_PARAMS with the precise json-pointer path of the
    # failing field, instead of bubbling up rest-api's generic 400.
    schema_error = _validate_arguments(arguments, tool.input_schema)
    if schema_error is not None:
        return jsonrpc.failure(rpc.id, errors.INVALID_PARAMS, schema_error)

    try:
        target = tool.build_target(arguments)
    except KeyError as exc:
        return jsonrpc.failure(
            rpc.id,
            errors.INVALID_PARAMS,
            f"Missing required argument: {exc.args[0] if exc.args else exc!r}",
        )
    except (TypeError, ValueError) as exc:
        return jsonrpc.failure(rpc.id, errors.INVALID_PARAMS, str(exc))

    try:
        response = dispatcher.dispatch(request=request, target=target)
    except (NotImplementedError, UnknownRestApiPath, UnsupportedDispatchMethod) as exc:
        # Catch the full set of exception types the dispatcher can
        # raise. Before #45 only NotImplementedError was caught, so
        # path/method mismatches escaped to Django's 500 handler.
        _logger.warning(
            "mcp.tools_call.upstream_error",
            extra={
                "user": getattr(request.user, "username", None),
                "tool": name,
                "exc_type": type(exc).__name__,
            },
        )
        return jsonrpc.failure(rpc.id, errors.SERVER_ERROR_UPSTREAM, str(exc))

    status_code = getattr(response, "status_code", 200)
    _logger.info(
        "mcp.tools_call",
        extra={
            "user": getattr(request.user, "username", None),
            "tool": name,
            "status": status_code,
        },
    )
    return jsonrpc.success(
        rpc.id,
        {
            "content": [{"type": "json", "json": _decode_response_body(response)}],
            "isError": _is_error_response(response),
            "status": status_code,
        },
    )


def _validate_arguments(arguments: dict[str, Any], schema: dict[str, Any]) -> str | None:
    """Return ``None`` if ``arguments`` validates against ``schema``.

    Otherwise return a human-readable message that names the field that
    failed. The message is what we surface in the JSON-RPC ``error.message``
    body, so it has to be short, deterministic, and not leak server-side
    detail.
    """
    try:
        jsonschema.validate(
            instance=arguments,
            schema=schema,
            cls=jsonschema.Draft202012Validator,
        )
    except jsonschema.ValidationError as exc:
        # ``absolute_path`` is the deque of keys/indices into ``arguments``
        # at the point of failure. Render as a json-pointer-ish path so a
        # caller can locate the field at a glance.
        path = "/" + "/".join(str(p) for p in exc.absolute_path) if exc.absolute_path else "/"
        return f"{path}: {exc.message}"
    return None


def _decode_response_body(response: Any) -> Any:
    """Decode a Django HttpResponse body as JSON when possible."""
    body = getattr(response, "content", b"")
    if not body:
        return None
    try:
        return json.loads(body)
    except (TypeError, ValueError):
        # Non-JSON bodies are passed through as a string. We do not try
        # to parse them further — rest-api owns the wire format.
        try:
            return body.decode("utf-8")
        except AttributeError:
            return None


def _is_error_response(response: Any) -> bool:
    status = getattr(response, "status_code", 200)
    return status >= 400


@method_decorator(require_POST, name="dispatch")
class McpEndpointView(View):
    """POST handler for the MCP JSON-RPC endpoint."""

    def post(self, request: HttpRequest) -> HttpResponse:  # noqa: D401 — Django view name.
        gate = _auth_gate(request)
        if gate is not None:
            return gate
        # Reject oversized envelopes before parsing. A well-formed
        # JSON-RPC request is kilobytes; Django's
        # DATA_UPLOAD_MAX_MEMORY_SIZE default of 2.5 MiB is designed
        # for form uploads, not RPC envelopes. Closes #46.
        max_bytes = conf.get("MAX_REQUEST_BYTES")
        body = request.body
        if max_bytes and len(body) > max_bytes:
            _logger.warning(
                "mcp.request.too_large",
                extra={
                    "user": getattr(request.user, "username", None),
                    "size": len(body),
                    "limit": max_bytes,
                },
            )
            return JsonResponse(
                jsonrpc.failure(
                    None,
                    errors.INVALID_REQUEST,
                    f"Request body exceeds the {max_bytes}-byte MCP envelope limit.",
                ),
                status=413,
            )
        try:
            payload = json.loads(body.decode("utf-8") or "null")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return JsonResponse(
                jsonrpc.failure(None, errors.PARSE_ERROR, str(exc)),
                status=400,
            )
        if payload is None:
            return JsonResponse(
                jsonrpc.failure(None, errors.INVALID_REQUEST, "Empty body"),
                status=400,
            )
        envelope = _handle_jsonrpc(request, payload, get_dispatcher())
        status = 400 if "error" in envelope else 200
        return JsonResponse(envelope, status=status)


@method_decorator(require_GET, name="dispatch")
class ManifestView(View):
    """GET handler for the read-only manifest document."""

    def get(self, request: HttpRequest) -> HttpResponse:
        gate = _auth_gate(request)
        if gate is not None:
            return gate
        return JsonResponse(manifest.manifest())
