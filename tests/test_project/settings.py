"""Test Django project settings.

A minimal Django project that mounts django-admin-mcp-api at ``/mcp/`` so
the test suite can drive it via the test client. No real database
content is needed because the FakeDispatcher (tests/helpers.py) short-
circuits forwarding; SQLite is configured purely to keep
``manage.py`` / ``django.setup()`` happy.
"""

from __future__ import annotations

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False
# Deterministic test-only key — never used outside the test suite.
# Bandit B105 is fine here: the value is constant, public, and only
# loaded when DJANGO_SETTINGS_MODULE=tests.test_project.settings.
SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django_admin_rest_api",
    "django_admin_mcp_api",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "tests.test_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Default dispatcher factory used in tests — returns the FakeDispatcher
# defined in tests/helpers.py. Production deployments must NOT set
# ALLOW_ANONYMOUS to True. The fake dispatcher echoes the target back so
# tests can assert on the translation without standing up rest-api.
DJANGO_ADMIN_MCP_API = {
    "DISPATCHER_FACTORY": "tests.helpers.make_fake_dispatcher",
}
