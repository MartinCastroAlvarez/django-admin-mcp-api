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
    # The dotted path to a callable returning a Dispatcher. ``None``
    # means use the built-in default (which raises NotImplementedError
    # until django-admin-rest-api is wired — tracked in the integration
    # issue).
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
