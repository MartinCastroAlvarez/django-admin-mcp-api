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

# Defense-in-depth bounds (#79). ``pk`` is interpolated raw into the
# rest-api dispatch path; an unbounded value buys nothing (the 256 KiB
# envelope cap already bounds the worst case) but a tight ``maxLength``
# plus a ``/``- and ``?``-excluding ``pattern`` gives clearer agent
# errors than a downstream resolver miss, and forbids a pk that could
# reshape the resolved path. The path is still re-validated by Django's
# resolver in the dispatcher, so this is belt-and-suspenders.
PK_MAX_LENGTH = 256
# Cap the number of pks a single ``admin.action`` / ``admin.bulk_update``
# envelope may carry (#79). The envelope byte cap bounds amplification,
# but an explicit array cap gives an actionable INVALID_PARAMS instead
# of forwarding an oversized batch to rest-api.
PKS_MAX_ITEMS = 1000

PK = {
    "type": "string",
    "minLength": 1,
    "maxLength": PK_MAX_LENGTH,
    # Exclude path-structural characters so a pk can never reshape the
    # rest-api dispatch path it is interpolated into.
    "pattern": "^[^/?#]+$",
    "description": "Primary key of the model instance (always serialised as a string on the wire).",
}

# Schema fragment for a ``pks`` array shared by admin.action / admin.bulk_update.
PK_ITEM = {
    "type": "string",
    "minLength": 1,
    "maxLength": PK_MAX_LENGTH,
    "pattern": "^[^/?#]+$",
}
