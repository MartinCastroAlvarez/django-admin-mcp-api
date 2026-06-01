"""The single forward point into django-admin-rest-api.

``Dispatcher`` is the only seam between this package and the underlying
REST API. Everything else in ``django_admin_mcp_api`` — views, manifest,
tools — talks to the dispatcher and nothing else. That keeps the
"protocol-only, no admin logic" invariant easy to enforce: this file is
the *only* place where the integration shape lives.

## The shape

Each MCP tool call carries ``(tool_name, arguments)``. The dispatcher
translates that into a ``DispatchTarget`` (HTTP method + path + body)
against django-admin-rest-api, forwards it through the rest-api view
matching that path, and returns the ``HttpResponseBase`` for the view
layer to shape back into a JSON-RPC envelope.

The default implementation is :class:`RestApiDispatcher`, which uses
Django's URL resolver against ``django_admin_rest_api.api.urls`` to
find the target view and calls it with a synthetic request that carries
the original session, user, cookies, and CSRF state.

Consumers can override the dispatcher via the
``DJANGO_ADMIN_MCP_API["DISPATCHER_FACTORY"]`` setting (a dotted path
to a zero-arg callable that returns a :class:`Dispatcher`). Tests use
this seam to swap in a :class:`FakeDispatcher` that records the
forwards instead of executing them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any
from typing import Protocol
from typing import cast
from typing import runtime_checkable
from urllib.parse import urlencode

from django.http import HttpRequest
from django.http import HttpResponseBase
from django.test import RequestFactory
from django.urls import Resolver404
from django.urls import resolve

from django_admin_mcp_api import conf


@dataclass(frozen=True)
class DispatchTarget:
    """A translated MCP tool call, ready to forward to rest-api.

    ``path`` is rooted at the rest-api API root (e.g.
    ``/<app>/<model>/<pk>/`` — *not* including the ``api/v1/`` prefix or
    the consumer's mount point; those are handled by the dispatcher).
    ``body`` is a JSON-serialisable object; the dispatcher encodes it.
    """

    method: str  # "GET", "POST", "PATCH", "DELETE"
    path: str
    body: dict[str, Any] | None = None
    query: dict[str, str] | None = None


@runtime_checkable
class Dispatcher(Protocol):
    """The seam to django-admin-rest-api.

    Implementations forward ``target`` against the rest-api views,
    propagating the consumer's authenticated ``HttpRequest`` (session +
    CSRF) untouched. They must not mutate the original ``request``.
    """

    def dispatch(
        self,
        *,
        request: HttpRequest,
        target: DispatchTarget,
    ) -> HttpResponseBase: ...


class RestApiDispatcher:
    """Forward a :class:`DispatchTarget` to django-admin-rest-api views.

    Resolves the target's path against ``django_admin_rest_api.api.urls``
    to find the view function, then constructs a synthetic
    :class:`HttpRequest` that carries the original request's
    ``user``, ``session``, cookies, messages backend, and CSRF state.
    The synthetic request is what rest-api's view sees — auth therefore
    matches the MCP caller exactly, and rest-api's permission +
    queryset checks run unchanged.

    The dispatcher does not mutate ``request`` or query the database.
    """

    URLCONF = "django_admin_rest_api.api.urls"

    def dispatch(
        self,
        *,
        request: HttpRequest,
        target: DispatchTarget,
    ) -> HttpResponseBase:
        synthetic = self._build_synthetic_request(request, target)
        try:
            match = resolve(target.path, urlconf=self.URLCONF)
        except Resolver404 as exc:
            raise UnknownRestApiPath(target.path) from exc
        # ``match.func`` is the resolver's view callable, typed ``Any`` by
        # Django. rest-api views return an ``HttpResponseBase``; cast so
        # the seam's return type is honest under ``mypy --strict``.
        response = match.func(synthetic, *match.args, **match.kwargs)
        return cast(HttpResponseBase, response)

    def _build_synthetic_request(
        self,
        request: HttpRequest,
        target: DispatchTarget,
    ) -> HttpRequest:
        factory = RequestFactory()
        method = target.method.lower()
        builder = getattr(factory, method, None)
        if builder is None:
            raise UnsupportedDispatchMethod(target.method)

        path = target.path
        if target.query:
            path = f"{path}?{urlencode(target.query, doseq=True)}"

        kwargs: dict[str, Any] = {}
        if target.body is not None and target.method.upper() in {"POST", "PATCH", "PUT", "DELETE"}:
            kwargs["data"] = json.dumps(target.body)
            kwargs["content_type"] = "application/json"

        # ``builder`` is a dynamically-resolved ``RequestFactory`` method
        # (typed ``Any`` after the ``getattr``); it returns a synthetic
        # ``HttpRequest``. Cast so the builder's return type is explicit
        # under ``mypy --strict``.
        synthetic = cast(HttpRequest, builder(path, **kwargs))

        # Carry over auth-bearing attributes so rest-api sees the same
        # caller that the MCP endpoint saw. We do not mutate the
        # original ``request`` — the synthetic gets its own attributes.
        synthetic.user = request.user
        if hasattr(request, "session"):
            synthetic.session = request.session
        synthetic.COOKIES = request.COOKIES
        if hasattr(request, "_messages"):
            # ``_messages`` is Django's private messages backend, absent
            # from the type stubs. Copy it so rest-api's views can emit
            # admin messages exactly as the outer request would. The
            # ``type: ignore`` flags this as the one private-API touch.
            synthetic._messages = request._messages  # type: ignore[attr-defined]
        # Deliberately NOT forwarded:
        #   * ``_dont_enforce_csrf_checks`` — the per-request CSRF
        #     bypass flag. CSRF was already verified at the outer MCP
        #     view; the synthetic forward runs in-process and does not
        #     go through middleware, so copying the flag would only
        #     carry a future bypass risk. (Closes #44.)
        return synthetic


class PendingDispatcher:
    """Fallback used when the consumer has not installed rest-api.

    Every call raises :class:`DispatcherNotInstalled` with a pointer to
    the rest-api install step. The :func:`get_dispatcher` factory only
    falls back to this if importing rest-api fails, so a normal install
    never sees it — :class:`RestApiDispatcher` is the live default.
    """

    REASON = (
        "django-admin-rest-api is required at runtime. "
        "Install it (``pip install django-admin-rest-api``) and add "
        '"django_admin_rest_api" to INSTALLED_APPS.'
    )

    def dispatch(
        self,
        *,
        request: HttpRequest,
        target: DispatchTarget,
    ) -> HttpResponseBase:
        del request, target
        raise DispatcherNotInstalled(self.REASON)


class DispatchError(Exception):
    """Base class for every error the dispatch seam can raise.

    The view layer catches :class:`DispatchError` and maps it to a
    JSON-RPC ``SERVER_ERROR_UPSTREAM`` envelope rather than letting it
    escape to Django's 500 handler. Any new dispatcher failure mode
    should subclass this so the catch stays future-proof (see #67).
    """


class UnknownRestApiPath(DispatchError):
    """Raised when a tool's path does not resolve against rest-api's URL conf."""

    def __init__(self, path: str) -> None:
        super().__init__(f"No rest-api view matches {path!r}")
        self.path = path


class UnsupportedDispatchMethod(DispatchError):
    """Raised when the target HTTP method is not supported by RequestFactory."""

    def __init__(self, method: str) -> None:
        super().__init__(f"Unsupported HTTP method {method!r}")
        self.method = method


class DispatcherNotInstalled(DispatchError, NotImplementedError):
    """Raised by :class:`PendingDispatcher` when rest-api is not installed.

    Subclasses both :class:`DispatchError` (so the view's upstream-error
    catch handles it) and :class:`NotImplementedError` (preserving the
    historical contract that the unconfigured dispatcher raises
    ``NotImplementedError``).
    """


class ImproperConfiguredDispatcher(Exception):
    """Raised when ``DISPATCHER_FACTORY`` resolves to something invalid."""


def get_dispatcher() -> Dispatcher:
    """Return the active dispatcher.

    Resolution order:

    1. ``DJANGO_ADMIN_MCP_API["DISPATCHER_FACTORY"]`` — dotted path to
       a zero-arg callable. Used by tests and by consumers who want to
       swap in their own forwarder.
    2. The built-in :class:`RestApiDispatcher` — the live default,
       provided ``django_admin_rest_api`` is importable (it is a hard
       runtime dependency, so a normal install always reaches here).
    3. :class:`PendingDispatcher` — only reached if rest-api is not
       installed; every call raises :class:`DispatcherNotInstalled`.
    """
    dotted = conf.get("DISPATCHER_FACTORY")
    if dotted:
        module_name, _, attr = dotted.rpartition(".")
        if not module_name:
            raise ImproperConfiguredDispatcher(
                f"DISPATCHER_FACTORY must be a dotted path, got {dotted!r}"
            )
        factory = getattr(import_module(module_name), attr)
        instance = factory()
        if not isinstance(instance, Dispatcher):
            raise ImproperConfiguredDispatcher(
                f"DISPATCHER_FACTORY {dotted!r} returned {type(instance).__name__}, "
                "which does not satisfy the Dispatcher protocol"
            )
        return instance
    try:
        import_module("django_admin_rest_api.api.urls")
    except ImportError:
        return PendingDispatcher()
    return RestApiDispatcher()
