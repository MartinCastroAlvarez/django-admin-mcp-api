"""URL conf for the test project."""

from __future__ import annotations

from django.urls import include
from django.urls import path

urlpatterns = [
    path("mcp/", include("django_admin_mcp_api.urls")),
]
