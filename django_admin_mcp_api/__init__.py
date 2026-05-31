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

__version__ = "1.0.4"

# Default Django app config — consumers add ``"django_admin_mcp_api"`` to
# INSTALLED_APPS and Django picks this up automatically.
default_app_config = "django_admin_mcp_api.apps.DjangoAdminMcpApiConfig"

__all__ = ["__version__", "default_app_config"]
