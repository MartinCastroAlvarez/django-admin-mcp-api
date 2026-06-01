"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def staff_user(db):  # noqa: PT004 — fixture name is the API.
    """A signed-in staff user, as the typical caller of the MCP endpoint."""
    User = get_user_model()  # noqa: N806 — Django idiom.
    return User.objects.create_user(
        username="staff",
        password="pw-not-real-not-for-prod",  # noqa: S106 — test password.
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):  # noqa: PT004
    """A signed-in non-staff user — should be rejected with 403."""
    User = get_user_model()  # noqa: N806
    return User.objects.create_user(
        username="regular",
        password="pw-not-real-not-for-prod",  # noqa: S106
        is_staff=False,
    )


@pytest.fixture
def superuser(db):  # noqa: PT004
    """A superuser — has every per-model permission (add/change/view/delete).

    Needed by integration tests that exercise permission-gated rest-api
    endpoints (e.g. the form-spec add view gates on has_add_permission).
    """
    User = get_user_model()  # noqa: N806
    return User.objects.create_superuser(
        username="root",
        password="pw-not-real-not-for-prod",  # noqa: S106
    )


@pytest.fixture
def superuser_client(superuser):
    """Logged-in superuser Django test client."""
    c = Client()
    c.force_login(superuser)
    return c


@pytest.fixture
def anon_client():
    """Anonymous Django test client — should hit the 401 path."""
    return Client()


@pytest.fixture
def staff_client(staff_user):
    """Logged-in staff Django test client."""
    c = Client()
    c.force_login(staff_user)
    return c


@pytest.fixture
def regular_client(regular_user):
    """Logged-in non-staff Django test client."""
    c = Client()
    c.force_login(regular_user)
    return c
