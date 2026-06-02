"""Django views — the MCP HTTP entry points.

Two views:

* :class:`McpEndpointView` (POST) — single JSON-RPC entry point that
  handles ``initialize``, ``tools/list``, and ``tools/call``. CSRF is
  enforced by Django middleware; no view bypasses it.
* :class:`ManifestView` (GET) — read-only catalogue document for curl/
  dashboards. Same auth gate as the JSON-RPC endpoint.

Both views are intentionally tiny. They do exactly three things:

1. Apply the auth gate. The authoritative per-tool permission check
   is django-admin-rest-api's (it owns permissions); the
   :func:`_auth_gate` here is the staff-only baseline that fails fast
   before a forward is built.
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
from django.views.generic import View

from django_admin_mcp_api import conf
from django_admin_mcp_api import tools
from django_admin_mcp_api.server import errors
from django_admin_mcp_api.server import jsonrpc
from django_admin_mcp_api.server import manifest
from django_admin_mcp_api.server.dispatch import Dispatcher
from django_admin_mcp_api.server.dispatch import DispatchError
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


def _username(request: HttpRequest) -> str | None:
    """Best-effort username for log records; never raises."""
    return getattr(getattr(request, "user", None), "username", None)


def _log_method(request: HttpRequest, method: str, status: Any) -> None:
    """Emit one structured INFO log per JSON-RPC method / manifest access.

    Closes #80: discovery-side calls (``initialize``, ``tools/list``, the
    GET landing, and GET ``/manifest/``) previously produced no forensic
    record, so a caller could enumerate the full capability surface and
    server metadata invisibly. We log a single ``{user, method, status}``
    line — never the request body (could carry PII / passwords).
    """
    _logger.info(
        "mcp.method",
        extra={"user": _username(request), "method": method, "status": status},
    )


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
        # #81 — read the client's requested protocolVersion and negotiate.
        # We support exactly one version; if the client asked for a
        # different one we log the mismatch and still return ours (the MCP
        # client decides whether the returned version is acceptable).
        requested = rpc.params.get("protocolVersion")
        supported = conf.get("PROTOCOL_VERSION")
        if isinstance(requested, str) and requested != supported:
            _logger.info(
                "mcp.initialize.protocol_mismatch",
                extra={
                    "user": _username(request),
                    "requested": requested,
                    "supported": supported,
                },
            )
        result = manifest.initialize_result(
            requested_protocol=requested if isinstance(requested, str) else None
        )
        _log_method(request, "initialize", 200)
        return jsonrpc.success(rpc.id, result)

    if rpc.method == "tools/list":
        result = {"tools": manifest.tools_catalogue()}
        _log_method(request, "tools/list", 200)
        return jsonrpc.success(rpc.id, result)

    if rpc.method == "tools/call":
        return _handle_tools_call(request, rpc, dispatcher)

    _log_method(request, rpc.method, errors.METHOD_NOT_FOUND)
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
    except (DispatchError, NotImplementedError) as exc:
        # Catch every dispatcher failure via the shared DispatchError
        # base (UnknownRestApiPath, UnsupportedDispatchMethod, and any
        # future subclass) so new failure modes can't regress to a
        # Django 500 (#67). NotImplementedError stays in the tuple to
        # cover a custom DISPATCHER_FACTORY that raises the plain
        # builtin without subclassing DispatchError. Before #45 only
        # NotImplementedError was caught, so path/method mismatches
        # escaped to Django's 500 handler.
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


def _landing_html(payload: dict[str, Any]) -> str:
    """Render the GET / landing as a minimal HTML page.

    No template engine — one f-string. Kept deliberately tiny so the
    landing isn't a maintenance burden. Browsers hitting ``/mcp/``
    see a recognisable page; agents getting Accept: application/json
    get JSON instead (handled by the caller).
    """
    name = payload["server"]["name"]
    version = payload["server"]["version"]
    protocol = payload["protocolVersion"]
    count = payload["tools_count"]
    manifest_url = payload["manifest_url"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-Frame-Options" content="DENY">
<title>{name} — MCP server</title>
<style>
  body {{ font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
         max-width: 42rem; margin: 4rem auto; padding: 0 1rem;
         color: #111; line-height: 1.5; }}
  h1 {{ font-size: 1.25rem; margin-bottom: 0.25rem; }}
  .tag {{ color: #666; font-size: 0.9rem; }}
  dl {{ display: grid; grid-template-columns: 10rem 1fr; gap: 0.25rem 1rem;
        margin-top: 1.5rem; }}
  dt {{ font-weight: 600; color: #444; }}
  dd {{ margin: 0; }}
  a {{ color: #2563eb; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          background: #f4f4f5; padding: 0 0.25rem; border-radius: 3px; }}
</style>
</head>
<body>
<h1>{name}</h1>
<div class="tag">MCP server — JSON-RPC entry point at this URL.</div>
<dl>
  <dt>Version</dt><dd><code>{version}</code></dd>
  <dt>Protocol</dt><dd><code>{protocol}</code></dd>
  <dt>Tools available</dt><dd>{count}</dd>
  <dt>Catalogue</dt><dd><a href="{manifest_url}">manifest/</a></dd>
</dl>
<p>POST a JSON-RPC <code>initialize</code>, <code>tools/list</code>,
or <code>tools/call</code> envelope to this URL.
See <code>docs/api-contract.md</code> in the package for the wire spec.</p>
</body>
</html>
"""


class McpEndpointView(View):
    """The MCP JSON-RPC endpoint.

    - ``POST /`` runs the JSON-RPC protocol (``initialize``,
      ``tools/list``, ``tools/call``).
    - ``GET /`` returns a small landing — JSON for API callers, HTML
      for browsers — that summarises the server (name, version, tool
      count) and points at the full manifest. Same staff-only auth
      gate. Closes #39.
    """

    http_method_names = ["get", "post"]

    def get(self, request: HttpRequest) -> HttpResponse:
        gate = _auth_gate(request)
        if gate is not None:
            return gate
        payload = {
            "server": manifest.server_info(),
            "protocolVersion": conf.get("PROTOCOL_VERSION"),
            "tools_count": len(manifest.tools_catalogue()),
            "manifest_url": request.build_absolute_uri("manifest/"),
            "endpoint": request.build_absolute_uri(),
        }
        _log_method(request, "GET /", 200)
        accept = request.headers.get("Accept", "")
        if "text/html" in accept and "application/json" not in accept:
            return HttpResponse(_landing_html(payload), content_type="text/html; charset=utf-8")
        return JsonResponse(payload)

    def post(self, request: HttpRequest) -> HttpResponse:  # Django view name.
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
        _log_method(request, "GET /manifest/", 200)
        return JsonResponse(manifest.manifest())
