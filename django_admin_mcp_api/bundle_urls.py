"""One-include URL conf that auto-mounts rest-api alongside MCP.

Consumers can swap the two-line URL setup:

.. code-block:: python

    # urls.py — explicit form (default; gives you control over the prefix)
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("",       include("django_admin_rest_api.urls")),   # /api/v1/...
        path("mcp/",   include("django_admin_mcp_api.urls")),    # /mcp/
    ]

for the one-include form below:

.. code-block:: python

    # urls.py — bundled form (one include; rest-api auto-mounted at root)
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("",       include("django_admin_mcp_api.bundle_urls")),
    ]

The bundle mounts rest-api at the same prefix the consumer used for
``bundle_urls`` (so ``api/v1/...`` lives under that prefix) and MCP at
``mcp/`` underneath. It is a convenience layer; you still need
``django_admin_rest_api`` in ``INSTALLED_APPS`` — that's a Django app
registration concern that can't be hidden inside a URL conf.

Closes the "why two URL includes?" half of #33. The "why two
``INSTALLED_APPS`` entries?" half is a Django app-loading question
covered by the README callout and by the ``E001`` system check.
"""

from __future__ import annotations

from django.urls import include
from django.urls import path

app_name = "django_admin_mcp_api_bundle"

urlpatterns = [
    # rest-api lives at the consumer's mount prefix, so its
    # ``api/v1/...`` paths sit alongside the MCP endpoint.
    path("", include("django_admin_rest_api.urls")),
    # MCP at ``<prefix>/mcp/`` under the same mount.
    path("mcp/", include("django_admin_mcp_api.urls")),
]
