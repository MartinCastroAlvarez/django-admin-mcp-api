"""JSON-RPC 2.0 envelope helpers.

The MCP spec rides on JSON-RPC 2.0. These helpers parse incoming
envelopes and shape outgoing ones; they do not know anything about MCP
*methods* or *tools* — that's the view's job.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from django_admin_mcp_api.server import errors


class JsonRpcError(Exception):
    """Raised by parse helpers; carries a JSON-RPC error code + data.

    Views catch this and shape the response envelope.
    """

    def __init__(
        self,
        code: int,
        message: str | None = None,
        data: Any | None = None,
        *,
        request_id: Any = None,
    ) -> None:
        self.code = code
        self.message = message or errors.DEFAULT_MESSAGES.get(code, "Error")
        self.data = data
        self.request_id = request_id
        super().__init__(self.message)


@dataclass(frozen=True)
class JsonRpcRequest:
    """A parsed JSON-RPC 2.0 request envelope."""

    method: str
    params: dict[str, Any] = field(default_factory=dict)
    id: Any = None  # noqa: A003 — JSON-RPC field name; not a builtin shadow here.
    jsonrpc: str = "2.0"


def parse_request(payload: Any) -> JsonRpcRequest:
    """Parse and validate a single JSON-RPC 2.0 request envelope.

    Raises :class:`JsonRpcError` on any structural problem.

    Batch requests (a JSON array) are not supported — the MCP spec uses
    one request per HTTP POST. If a batch arrives we reject with
    ``INVALID_REQUEST``.
    """
    if not isinstance(payload, dict):
        raise JsonRpcError(errors.INVALID_REQUEST, "Envelope must be a JSON object")
    if payload.get("jsonrpc") != "2.0":
        raise JsonRpcError(errors.INVALID_REQUEST, 'jsonrpc field must be "2.0"')
    method = payload.get("method")
    if not isinstance(method, str) or not method:
        raise JsonRpcError(
            errors.INVALID_REQUEST,
            "method must be a non-empty string",
            request_id=payload.get("id"),
        )
    params = payload.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise JsonRpcError(
            errors.INVALID_PARAMS,
            "params must be an object",
            request_id=payload.get("id"),
        )
    return JsonRpcRequest(method=method, params=params, id=payload.get("id"))


def success(request_id: Any, result: Any) -> dict[str, Any]:
    """Shape a successful JSON-RPC response envelope."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def failure(
    request_id: Any,
    code: int,
    message: str | None = None,
    data: Any | None = None,
) -> dict[str, Any]:
    """Shape a JSON-RPC error response envelope."""
    err: dict[str, Any] = {
        "code": code,
        "message": message or errors.DEFAULT_MESSAGES.get(code, "Error"),
    }
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}
