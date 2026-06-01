"""Settings accessors for django-admin-mcp-api.

Every consumer-tunable knob is read through this module, never directly
from ``django.conf.settings``. That keeps defaults and validation in one
place and makes the surface easy to enumerate in docs.

Public settings live under the ``DJANGO_ADMIN_MCP_API`` namespace:

.. code-block:: python

    DJANGO_ADMIN_MCP_API = {
        "PROTOCOL_VERSION": "2024-11-05",   # MCP spec version we speak
        "SERVER_NAME": "django-admin",     # advertised via initialize
        "ADMIN_SITE": "django.contrib.admin.site",  # dotted path
    }

Anything not present in the consumer's settings falls back to the
defaults in :data:`DEFAULTS` below. ``ALLOW_ANONYMOUS`` is an
**internal** test-only knob that is deliberately undocumented in the
public README and the quickstart example — there is no legitimate
production use case for setting it, so it is not advertised. Do not
add it to any user-facing doc.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

# Public settings namespace.
NAMESPACE = "DJANGO_ADMIN_MCP_API"

# Defaults — the one place to read these from.
DEFAULTS: dict[str, Any] = {
    "PROTOCOL_VERSION": "2024-11-05",
    "SERVER_NAME": "django-admin",
    "SERVER_VERSION": None,  # falls back to the package __version__
    "ADMIN_SITE": "django.contrib.admin.site",
    # Internal: must remain undocumented in user-facing docs. The only
    # caller is the test suite (which flips it via ``override_settings``
    # to exercise paths that would otherwise need a full Django auth
    # setup). Setting this to True in production disables the staff
    # gate — never do that.
    "ALLOW_ANONYMOUS": False,
    # Maximum request body size for the MCP endpoint, in bytes. A
    # JSON-RPC envelope rarely exceeds a few KiB — keep this lower
    # than Django's project-wide ``DATA_UPLOAD_MAX_MEMORY_SIZE`` (which
    # defaults to 2.5 MiB and is designed for HTML form uploads, an
    # entirely different threat profile). Closes #46.
    "MAX_REQUEST_BYTES": 256 * 1024,  # 256 KiB
    # Tool names to omit from the catalogue and refuse in ``tools/call``.
    # Read-only deployments typically set ``["admin.destroy",
    # "admin.bulk_update", "admin.set_password"]``. The MCP endpoint
    # behaves as if those tools do not exist — they don't appear in
    # ``tools/list``, the read-only manifest, or the GET landing, and
    # calling them returns METHOD_NOT_FOUND. Closes #41 + #48.
    "DISABLED_TOOLS": (),
    # The dotted path to a callable returning a Dispatcher. ``None``
    # means use the built-in default, ``RestApiDispatcher``, which
    # forwards to django-admin-rest-api (a hard runtime dependency).
    # Override this to swap in a custom forwarder (tests use it to
    # record dispatches instead of executing them).
    "DISPATCHER_FACTORY": None,
}


def get(key: str) -> Any:
    """Return the value for ``key``, falling back to :data:`DEFAULTS`.

    Unknown keys raise :class:`KeyError` rather than silently returning
    ``None`` — that catches typos in consumer settings during startup.
    """
    if key not in DEFAULTS:
        raise KeyError(f"Unknown {NAMESPACE} setting: {key!r}")
    bag = getattr(settings, NAMESPACE, {}) or {}
    if key in bag:
        return bag[key]
    return DEFAULTS[key]
