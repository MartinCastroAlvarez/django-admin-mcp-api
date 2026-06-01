"""URL conf for the test project."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    # The legacy admin is mounted so the form-spec resolver can reverse the
    # ``admin:<app>_<model>_change`` URL for the legacy-iframe escape hatch
    # (the Job fixture's Path B). reverse() falls back to ROOT_URLCONF.
    path("admin/", admin.site.urls),
    path("mcp/", include("django_admin_mcp_api.urls")),
]
