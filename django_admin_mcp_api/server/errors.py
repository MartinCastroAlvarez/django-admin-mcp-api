"""JSON-RPC 2.0 + MCP error code constants.

Reference: https://www.jsonrpc.org/specification#error_object and the
MCP spec error vocabulary. Keeping these in one place means views and
the dispatcher emit identical codes for identical conditions.
"""

from __future__ import annotations

# JSON-RPC 2.0 reserved codes (-32768 to -32000).
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Implementation-defined server errors (-32000 to -32099). We use a few
# of these to carry rest-api-layer signals out to the MCP client.
SERVER_ERROR_UNAUTHENTICATED = -32001
SERVER_ERROR_FORBIDDEN = -32002
SERVER_ERROR_NOT_FOUND = -32003
SERVER_ERROR_CSRF = -32004
SERVER_ERROR_VALIDATION = -32005
SERVER_ERROR_UPSTREAM = -32099


# Human-readable defaults paired with each code; senders can override the
# ``message`` field when they have a more specific signal to surface.
DEFAULT_MESSAGES: dict[int, str] = {
    PARSE_ERROR: "Parse error",
    INVALID_REQUEST: "Invalid Request",
    METHOD_NOT_FOUND: "Method not found",
    INVALID_PARAMS: "Invalid params",
    INTERNAL_ERROR: "Internal error",
    SERVER_ERROR_UNAUTHENTICATED: "Authentication required",
    SERVER_ERROR_FORBIDDEN: "Permission denied",
    SERVER_ERROR_NOT_FOUND: "Not found",
    SERVER_ERROR_CSRF: "CSRF verification failed",
    SERVER_ERROR_VALIDATION: "Validation error",
    SERVER_ERROR_UPSTREAM: "Upstream rest-api error",
}
