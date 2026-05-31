"""App config + bundle URL conf wiring."""

from __future__ import annotations

import pytest
from django.apps import apps
from django.urls import resolve


def test_app_config_is_registered():
    cfg = apps.get_app_config("django_admin_mcp_api")
    assert cfg.name == "django_admin_mcp_api"
    assert cfg.label == "django_admin_mcp_api"
    assert cfg.verbose_name == "Django Admin MCP API"


@pytest.mark.django_db
def test_bundle_urls_exposes_mcp_and_rest_api():
    """Closes the URL half of #33 — one include() reaches both apps."""
    # Resolve a path through the bundle's URL conf — both rest-api's
    # /api/v1/registry/ and the MCP /mcp/ should be reachable.
    match_mcp = resolve("/mcp/", urlconf="django_admin_mcp_api.bundle_urls")
    assert match_mcp.func.__name__ == "McpEndpointView" or match_mcp.url_name == "mcp"
    # The rest-api `api/v1/registry/` resolves under the bundle's root.
    match_rest = resolve("/api/v1/registry/", urlconf="django_admin_mcp_api.bundle_urls")
    assert match_rest.url_name == "registry"
