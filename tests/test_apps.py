"""App config is wired correctly."""

from __future__ import annotations

from django.apps import apps


def test_app_config_is_registered():
    cfg = apps.get_app_config("django_admin_mcp_api")
    assert cfg.name == "django_admin_mcp_api"
    assert cfg.label == "django_admin_mcp_api"
    assert cfg.verbose_name == "Django Admin MCP API"
