"""Quickstart Django settings.

Demonstrates the *minimum* changes needed to drop MCP onto an existing
Django admin. Everything outside ``INSTALLED_APPS`` and
``MIDDLEWARE`` is normal Django.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Demo-only key — never used in production. Override via env in real apps.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "demo-only-not-for-production-not-for-real-data",  # noqa: S105
)
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # The two lines that turn an existing Django admin into an
    # agent-reachable MCP server:
    "django_admin_rest_api",
    "django_admin_mcp_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "myproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
# django-admin-mcp-api — optional configuration
# --------------------------------------------------------------------------- #
# Every key below has a sensible default in
# ``django_admin_mcp_api.conf.DEFAULTS``. You only need to set the ones
# you want to override. The block below shows every available key with
# its default value so you can see what is configurable at a glance.
#
# DJANGO_ADMIN_MCP_API = {
#     # MCP protocol version advertised in the `initialize` result.
#     # Bump only when the upstream MCP spec changes and you've verified
#     # the package speaks the new dialect.
#     "PROTOCOL_VERSION": "2024-11-05",
#
#     # The `serverInfo.name` field returned by `initialize`. Useful
#     # when an MCP client lists multiple servers and you want a
#     # human-friendly label per environment (e.g. "acme-prod-admin").
#     "SERVER_NAME": "django-admin",
#
#     # The `serverInfo.version` field. ``None`` (the default) falls
#     # back to the installed package version. Override only if you
#     # need to surface a deployment-specific version string.
#     "SERVER_VERSION": None,
#
#     # Dotted path to the AdminSite the MCP layer introspects. Override
#     # if you've replaced ``django.contrib.admin.site`` with a custom
#     # ``AdminSite`` subclass.
#     "ADMIN_SITE": "django.contrib.admin.site",
#
#     # Test-only escape hatch. MUST stay False in production — flipping
#     # it lets unauthenticated callers reach the MCP endpoint. The
#     # security suite scans for production code paths that read it.
#     "ALLOW_ANONYMOUS": False,
#
#     # Dotted path to a zero-arg callable returning a Dispatcher. The
#     # built-in default forwards to django-admin-rest-api via Django's
#     # URL resolver, which is what 99% of consumers want. Override only
#     # to plug in a custom forwarder (e.g. for cross-process MCP).
#     "DISPATCHER_FACTORY": None,
# }
