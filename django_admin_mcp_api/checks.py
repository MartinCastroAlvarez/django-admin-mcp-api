"""Django system checks for django-admin-mcp-api.

Registered from ``apps.py::ready()``. Run at ``manage.py check`` time
and at server boot to catch misconfiguration before it bites at first
request.

Closes #34.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from django.conf import settings
from django.core.checks import Error
from django.core.checks import Warning as ChecksWarning
from django.core.checks import register


@register()
def check_rest_api_installed(app_configs: Any, **kwargs: Any) -> list[Any]:
    """``django_admin_rest_api`` must be in ``INSTALLED_APPS``.

    Without it, the dispatcher cannot import the upstream URL conf and
    every ``tools/call`` fails at request time.
    """
    if "django_admin_rest_api" in settings.INSTALLED_APPS:
        return []
    return [
        Error(
            "django_admin_rest_api must be in INSTALLED_APPS.",
            hint=(
                "Add 'django_admin_rest_api' to INSTALLED_APPS before "
                "'django_admin_mcp_api'. The MCP adapter forwards every "
                "tools/call to the REST API's view set; without it the "
                "package has nothing to dispatch to."
            ),
            obj=None,
            id="django_admin_mcp_api.E001",
        )
    ]


@register()
def check_admin_site_resolves(app_configs: Any, **kwargs: Any) -> list[Any]:
    """``DJANGO_ADMIN_MCP_API["ADMIN_SITE"]`` must be a dotted path
    that resolves to an importable object.

    The default ``django.contrib.admin.site`` resolves out of the box.
    A consumer who set a custom ``AdminSite`` subclass without updating
    the import path discovers it here, not at first request.
    """
    bag = getattr(settings, "DJANGO_ADMIN_MCP_API", {}) or {}
    dotted = bag.get("ADMIN_SITE", "django.contrib.admin.site")
    module_name, _, attr = dotted.rpartition(".")
    if not module_name:
        return [
            Error(
                f"DJANGO_ADMIN_MCP_API['ADMIN_SITE'] = {dotted!r} is not a dotted path.",
                hint="Use 'pkg.module.attr' form, e.g. 'django.contrib.admin.site'.",
                id="django_admin_mcp_api.E002",
            )
        ]
    try:
        mod = import_module(module_name)
        getattr(mod, attr)
    except (ImportError, AttributeError) as exc:
        return [
            Error(
                f"DJANGO_ADMIN_MCP_API['ADMIN_SITE'] = {dotted!r} could not be resolved.",
                hint=f"{type(exc).__name__}: {exc}. Confirm the path imports cleanly.",
                id="django_admin_mcp_api.E002",
            )
        ]
    return []


@register()
def check_disabled_tools_known(app_configs: Any, **kwargs: Any) -> list[Any]:
    """Names in ``DISABLED_TOOLS`` must match existing tool names.

    Typos in a deployment's ``DISABLED_TOOLS`` config produce a silent
    no-op: the tool isn't disabled because the name was wrong. The
    check surfaces the mismatch as a warning so the operator notices.
    """
    bag = getattr(settings, "DJANGO_ADMIN_MCP_API", {}) or {}
    disabled = bag.get("DISABLED_TOOLS", ())
    if not disabled:
        return []
    # Lazy import to avoid a circular import at app-loading time.
    from django_admin_mcp_api import tools

    known = {t.name for t in tools.all_tools()}
    unknown = [name for name in disabled if name not in known]
    if not unknown:
        return []
    return [
        ChecksWarning(
            f"DJANGO_ADMIN_MCP_API['DISABLED_TOOLS'] lists unknown tool name(s): {unknown!r}.",
            hint=(
                "These entries do nothing. The known tool names are: "
                + ", ".join(sorted(known))
                + "."
            ),
            id="django_admin_mcp_api.W001",
        )
    ]
