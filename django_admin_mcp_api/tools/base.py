"""Tool ABC + shared helpers.

A :class:`Tool` is the smallest unit the MCP layer exposes. It carries
the MCP-spec descriptor fields (``name``, ``description``,
``input_schema``) and a single behaviour: translate validated arguments
into a :class:`~django_admin_mcp_api.server.dispatch.DispatchTarget`.

Tools are deliberately *not* responsible for executing the call. The
view layer takes the target, hands it to the dispatcher, and shapes the
response. That keeps each tool tiny and easy to audit — they are pure
functions from arguments to a path/method/body.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from django_admin_mcp_api.server.dispatch import DispatchTarget


@dataclass(frozen=True)
class Tool:
    """A single MCP tool descriptor + argument translator."""

    name: str
    description: str
    input_schema: dict[str, Any]
    build_target: Callable[[dict[str, Any]], DispatchTarget]
    output_schema: dict[str, Any] | None = field(default=None)

    def to_manifest_entry(self) -> dict[str, Any]:
        """Render this tool for ``tools/list`` and the GET manifest."""
        entry: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
        if self.output_schema is not None:
            entry["outputSchema"] = self.output_schema
        return entry


# A few schema fragments reused across tools. JSON Schema keeps the
# wire contract self-describing — agents can introspect the catalogue
# without reading our docs.

APP_LABEL = {
    "type": "string",
    "pattern": "^[a-z][a-z0-9_]*$",
    "description": "Django app label (e.g. 'auth').",
}

MODEL_NAME = {
    "type": "string",
    "pattern": "^[a-z][a-z0-9_]*$",
    "description": "Django model name in lower-case (e.g. 'user').",
}

PK = {
    "type": "string",
    "description": "Primary key of the model instance (always serialised as a string on the wire).",
}
