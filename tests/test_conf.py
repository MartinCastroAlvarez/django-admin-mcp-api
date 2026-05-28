"""``conf.get`` defaults + override semantics."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_admin_mcp_api import conf


def test_defaults_returned_when_unset():
    assert conf.get("PROTOCOL_VERSION") == "2024-11-05"
    assert conf.get("SERVER_NAME") == "django-admin"
    assert conf.get("ALLOW_ANONYMOUS") is False


def test_consumer_override_wins():
    with override_settings(DJANGO_ADMIN_MCP_API={"SERVER_NAME": "custom"}):
        assert conf.get("SERVER_NAME") == "custom"
        # Other keys keep their defaults.
        assert conf.get("PROTOCOL_VERSION") == "2024-11-05"


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        conf.get("DOES_NOT_EXIST")
