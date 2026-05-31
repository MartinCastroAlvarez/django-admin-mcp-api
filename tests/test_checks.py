"""Tests for the ``django.core.checks`` hooks. Closes #34."""

from __future__ import annotations

from django.test import override_settings

from django_admin_mcp_api import checks


def test_rest_api_missing_emits_error():
    with override_settings(INSTALLED_APPS=["django.contrib.contenttypes"]):
        errs = checks.check_rest_api_installed(app_configs=None)
    assert len(errs) == 1
    assert errs[0].id == "django_admin_mcp_api.E001"


def test_rest_api_installed_emits_nothing():
    with override_settings(INSTALLED_APPS=["django.contrib.contenttypes", "django_admin_rest_api"]):
        errs = checks.check_rest_api_installed(app_configs=None)
    assert errs == []


def test_admin_site_resolves_default():
    errs = checks.check_admin_site_resolves(app_configs=None)
    assert errs == []


def test_admin_site_bad_dotted_path():
    with override_settings(DJANGO_ADMIN_MCP_API={"ADMIN_SITE": "no_dot"}):
        errs = checks.check_admin_site_resolves(app_configs=None)
    assert len(errs) == 1
    assert errs[0].id == "django_admin_mcp_api.E002"


def test_admin_site_unimportable():
    with override_settings(DJANGO_ADMIN_MCP_API={"ADMIN_SITE": "no.such.module.attr"}):
        errs = checks.check_admin_site_resolves(app_configs=None)
    assert len(errs) == 1
    assert errs[0].id == "django_admin_mcp_api.E002"


def test_disabled_tools_unknown_name_warns():
    with override_settings(DJANGO_ADMIN_MCP_API={"DISABLED_TOOLS": ("admin.does_not_exist",)}):
        errs = checks.check_disabled_tools_known(app_configs=None)
    assert len(errs) == 1
    assert errs[0].id == "django_admin_mcp_api.W001"


def test_disabled_tools_empty_emits_nothing():
    with override_settings(DJANGO_ADMIN_MCP_API={}):
        errs = checks.check_disabled_tools_known(app_configs=None)
    assert errs == []


def test_disabled_tools_real_names_emit_nothing():
    with override_settings(
        DJANGO_ADMIN_MCP_API={"DISABLED_TOOLS": ("admin.destroy", "admin.bulk_update")}
    ):
        errs = checks.check_disabled_tools_known(app_configs=None)
    assert errs == []
