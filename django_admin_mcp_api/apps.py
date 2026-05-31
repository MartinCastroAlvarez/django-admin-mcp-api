"""Django app config for django-admin-mcp-api."""

from __future__ import annotations

from django.apps import AppConfig


class DjangoAdminMcpApiConfig(AppConfig):
    """App config for ``django_admin_mcp_api``.

    Registered via ``INSTALLED_APPS``. We deliberately do not perform any
    side-effects in ``ready()`` other than configuration validation —
    every endpoint is opt-in through the consumer's URL conf.
    """

    name = "django_admin_mcp_api"
    label = "django_admin_mcp_api"
    verbose_name = "Django Admin MCP API"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Validate settings on app startup.

        Kept light to avoid slow Django boot in test suites. Importing
        ``checks`` registers the ``django.core.checks`` hooks so
        ``manage.py check`` and Django's auto-check at runserver boot
        catch misconfiguration before it bites at first request.
        """
        from django_admin_mcp_api import checks  # noqa: F401 — registers hooks
        from django_admin_mcp_api import conf  # noqa: F401
