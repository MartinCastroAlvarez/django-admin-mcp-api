"""URL patterns for django-admin-mcp-api.

Mounted under the consumer's chosen prefix, e.g.::

    # myproject/urls.py
    from django.urls import include, path

    urlpatterns = [
        path("admin/", admin.site.urls),
        path("mcp/", include("django_admin_mcp_api.urls")),
    ]

Two endpoints today:

- ``/`` (POST) — the MCP JSON-RPC entry point. Speaks ``initialize``,
  ``tools/list`` and ``tools/call``. CSRF is enforced via Django's
  default middleware; no view here bypasses it.
- ``/manifest/`` (GET) — a read-only convenience endpoint that returns
  the same tool catalogue ``tools/list`` returns, for humans poking the
  server with curl.
"""

from __future__ import annotations

from django.urls import path

from django_admin_mcp_api.server.views import ManifestView
from django_admin_mcp_api.server.views import McpEndpointView

app_name = "django_admin_mcp_api"

urlpatterns = [
    path("", McpEndpointView.as_view(), name="mcp"),
    path("manifest/", ManifestView.as_view(), name="manifest"),
]
