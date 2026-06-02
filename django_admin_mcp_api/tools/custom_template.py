"""The ``custom-template`` discriminator (#84).

rest-api 1.7.0's form-spec resolver returns ``renderer: "html-fragment"``
for any ModelAdmin whose form-spec resolution renders a custom template —
a declared ``change_form_template`` / ``add_form_template`` or a
``change_view`` / ``add_view`` override that renders a hand-rolled page
for *this* request. The SPA can render that server-rendered HTML; an MCP
client cannot. There is no field map to inspect, and any POST a client
synthesised would be guaranteed wrong, so the honest answer is "this view
isn't programmatically driveable".

This module renames that single upstream signal into the MCP discriminator
and never re-detects it — detection stays the rest-api resolver's job
(single source of truth, see CLAUDE.md §2 rule 1). We only:

* read the upstream ``renderer == "html-fragment"`` marker and its
  ``submit_url`` (the legacy admin URL), and
* derive ``spa_url`` from it by reusing rest-api's ``map_redirect_to_spa``
  (the ``/admin/`` → ``conf.SPA_URL_PREFIX`` swap, default ``/admin2/``),
  falling back to mirroring that swap only if the helper isn't importable.

The pre-1.7.0 ``legacy-iframe`` branch is intentionally dropped: MCP
clients never iframed anything, so that discriminator was never meaningful
here.
"""

from __future__ import annotations

import re
from typing import Any
from typing import cast

# The upstream marker (rest-api) and the MCP-facing discriminator.
UPSTREAM_RENDERER = "html-fragment"
RENDERER = "custom-template"
REASON = "ModelAdmin override: change_form_template"
REFUSAL_MESSAGE = (
    "This admin view uses a custom template and is not programmatically "
    "driveable — open it in the SPA or legacy admin."
)

# Fallback SPA prefix swap, used only if rest-api's helper can't be imported.
# Mirrors django_admin_rest_api.api.form_spec.map_redirect_to_spa with the
# default SPA_URL_PREFIX of ``/admin2/``.
_LEGACY_ADMIN_PREFIX_RE = re.compile(r"^/[^/]+/")
_FALLBACK_SPA_PREFIX = "/admin2/"


def _map_to_spa(legacy_url: str) -> str:
    """Rewrite a legacy admin URL onto the SPA prefix.

    Reuses rest-api's ``map_redirect_to_spa`` (which honours the consumer's
    ``SPA_URL_PREFIX`` setting) so MCP and the SPA never drift. If rest-api
    isn't importable — e.g. the :class:`PendingDispatcher` fallback — we
    mirror its default ``/admin/`` → ``/admin2/`` swap rather than fail.
    """
    try:
        from django_admin_rest_api.api.form_spec import map_redirect_to_spa
    except ImportError:
        if not legacy_url.startswith("/"):
            return legacy_url
        return _LEGACY_ADMIN_PREFIX_RE.sub(_FALLBACK_SPA_PREFIX, legacy_url, count=1)
    # rest-api ships no type stubs (ignore_missing_imports), so the helper is
    # typed ``Any``; it returns a ``str``. Cast to keep mypy --strict honest.
    return cast(str, map_redirect_to_spa(legacy_url))


def is_custom_template(body: Any) -> bool:
    """True when a decoded form-spec body is the upstream html-fragment."""
    return isinstance(body, dict) and body.get("renderer") == UPSTREAM_RENDERER


def discriminator(body: dict[str, Any]) -> dict[str, Any]:
    """Build the MCP ``custom-template`` discriminator from an html-fragment.

    The upstream payload carries ``submit_url`` — the legacy admin change/add
    URL (plus the original querystring) the SPA would POST back to. That is
    our ``legacy_url``; ``spa_url`` is the same URL mapped onto the SPA prefix.
    """
    legacy_url = body.get("submit_url", "")
    return {
        "renderer": RENDERER,
        "reason": REASON,
        "legacy_url": legacy_url,
        "spa_url": _map_to_spa(legacy_url),
        "machine_driveable": False,
    }


def refusal() -> dict[str, Any]:
    """The ``admin.form_submit`` refusal body for a custom-template form."""
    return {
        "ok": False,
        "reason": RENDERER,
        "message": REFUSAL_MESSAGE,
    }
