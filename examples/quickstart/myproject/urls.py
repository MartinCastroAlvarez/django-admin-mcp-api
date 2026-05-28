"""Quickstart URL conf.

Two ``include`` lines turn the admin into an agent-reachable surface.
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # The REST API — owns all admin behaviour, permissions, validation.
    path("", include("django_admin_rest_api.urls")),
    # The MCP adapter — wire-protocol-only layer over the REST API above.
    path("mcp/", include("django_admin_mcp_api.urls")),
]
