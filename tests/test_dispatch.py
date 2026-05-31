"""Dispatcher resolution + the default RestApiDispatcher behaviour."""

from __future__ import annotations

import pytest
from django.http import HttpRequest
from django.test import override_settings

from django_admin_mcp_api.server.dispatch import DispatchTarget
from django_admin_mcp_api.server.dispatch import ImproperConfiguredDispatcher
from django_admin_mcp_api.server.dispatch import PendingDispatcher
from django_admin_mcp_api.server.dispatch import RestApiDispatcher
from django_admin_mcp_api.server.dispatch import get_dispatcher


def test_default_is_rest_api_dispatcher_when_rest_api_installed():
    # django-admin-rest-api is a declared runtime dep in pyproject.toml,
    # so this is the normal path: the factory returns RestApiDispatcher.
    with override_settings(DJANGO_ADMIN_MCP_API={}):
        assert isinstance(get_dispatcher(), RestApiDispatcher)


def test_pending_dispatcher_raises_with_install_hint():
    target = DispatchTarget(method="GET", path="/registry/")
    with pytest.raises(NotImplementedError) as info:
        PendingDispatcher().dispatch(request=HttpRequest(), target=target)
    assert "pip install django-admin-rest-api" in str(info.value)


def test_factory_dotted_path_is_loaded():
    with override_settings(
        DJANGO_ADMIN_MCP_API={"DISPATCHER_FACTORY": "tests.helpers.make_fake_dispatcher"}
    ):
        d = get_dispatcher()
        assert d.__class__.__name__ == "FakeDispatcher"


def test_factory_rejects_invalid_dotted_path():
    with (
        override_settings(DJANGO_ADMIN_MCP_API={"DISPATCHER_FACTORY": "no_dot_here"}),
        pytest.raises(ImproperConfiguredDispatcher),
    ):
        get_dispatcher()


def test_rest_api_dispatcher_does_not_forward_csrf_bypass_flag():
    """Regression guard for #44.

    ``_dont_enforce_csrf_checks`` is the per-request CSRF bypass flag.
    Even if the outer request has it set (e.g. via a test fixture or a
    misbehaving middleware), the synthetic forward must NOT inherit it
    — otherwise a future code path that re-checks CSRF in rest-api
    inherits the bypass.
    """
    from django.test import RequestFactory

    outer = RequestFactory().post("/mcp/")
    outer.user = type("U", (), {"is_authenticated": True, "is_staff": True})()
    outer._dont_enforce_csrf_checks = True

    dispatcher = RestApiDispatcher()
    synthetic = dispatcher._build_synthetic_request(
        outer, DispatchTarget(method="GET", path="/registry/")
    )
    assert not hasattr(synthetic, "_dont_enforce_csrf_checks"), (
        "synthetic must not inherit the per-request CSRF bypass flag"
    )
