"""django-admin-mcp-api: an MCP (Model Context Protocol) server for the Django admin.

The package exposes every operation of a consumer's ``ModelAdmin`` as an MCP
tool, reusing Django's session + CSRF auth and the consumer's existing
``AdminSite`` registry. See ``ARCHITECTURE.md`` for the full design and
``SECURITY.md`` for the non-negotiable security rules.

This is the public surface; everything else under ``server/`` and
``tools/`` is implementation. The Django app config is auto-discovered
via ``apps.py`` once ``"django_admin_mcp_api"`` is added to
``INSTALLED_APPS``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

# Derive the version from the installed package metadata so it can never
# drift from ``pyproject.toml``. The fallback only applies when the
# package is run from a source tree that was never installed (e.g. a
# bare ``PYTHONPATH`` import); a normal ``pip install`` always has
# metadata. ``manifest.server_info()`` advertises this to MCP clients.
try:
    __version__ = _pkg_version("django-admin-mcp-api")
except PackageNotFoundError:  # pragma: no cover - source-tree fallback
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
