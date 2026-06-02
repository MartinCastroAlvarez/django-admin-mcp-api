"""Contract tests for the ``custom-template`` discriminator (#84).

rest-api 1.7.0 returns ``renderer: "html-fragment"`` for any ModelAdmin
whose form-spec resolution renders a custom template (a declared
``change_form_template`` or a ``change_view`` override that renders a
hand-rolled page for *this* request). MCP clients cannot drive opaque
HTML, so the MCP wire maps that single upstream signal to a clear,
non-driveable discriminator:

    {
        "renderer": "custom-template",
        "reason": "ModelAdmin override: change_form_template",
        "legacy_url": "/admin/jobs/job/<pk>/change/?run_custom=1",
        "spa_url":    "/admin2/jobs/job/<pk>/change/?run_custom=1",
        "machine_driveable": false,
    }

``admin.form_submit`` against such a form refuses to submit rather than
fabricating field values the legacy view would reject anyway.

These exercise the *real* :class:`RestApiDispatcher` (production default)
so the detection stays a single source of truth shared with rest-api —
the MCP layer only renames the discriminator, it never re-detects.
"""

from __future__ import annotations

import json

import pytest
from django.test import override_settings

from tests.helpers import jsonrpc_call

MCP = "/mcp/"

# Drop the FakeDispatcher override so the live RestApiDispatcher is used.
_REAL_DISPATCHER = override_settings(DJANGO_ADMIN_MCP_API={})


def _decode(response):
    return json.loads(response.content.decode("utf-8"))


def _call(client, name, arguments):
    with _REAL_DISPATCHER:
        response = client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": name, "arguments": arguments}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    return _decode(response)["result"]


@pytest.mark.django_db
def test_form_spec_returns_custom_template_discriminator(superuser_client):
    """Path B (``?run_custom=1``) → ``html-fragment`` upstream → the MCP
    ``custom-template`` discriminator with both legacy and SPA URLs set."""
    from tests.test_project.jobs.models import Job

    job = Job.objects.create(name="nightly", status="idle")
    spec = _call(
        superuser_client,
        "admin.form_spec",
        {
            "app_label": "jobs",
            "model_name": "job",
            "pk": str(job.pk),
            "query": {"run_custom": "1"},
        },
    )["content"][0]["json"]

    assert spec["renderer"] == "custom-template"
    assert spec["machine_driveable"] is False
    assert spec["reason"] == "ModelAdmin override: change_form_template"
    assert spec["legacy_url"].endswith(f"/admin/jobs/job/{job.pk}/change/?run_custom=1")
    assert spec["spa_url"].endswith(f"/admin2/jobs/job/{job.pk}/change/?run_custom=1")
    # No leaked html-fragment internals.
    assert "html" not in spec


@pytest.mark.django_db
def test_form_submit_refuses_custom_template(superuser_client):
    """``admin.form_submit`` against a custom-template form refuses to submit
    and returns the discriminator instead of fabricating/forwarding a POST."""
    from tests.test_project.jobs.models import Job

    job = Job.objects.create(name="nightly", status="idle")
    result = _call(
        superuser_client,
        "admin.form_submit",
        {
            "app_label": "jobs",
            "model_name": "job",
            "pk": str(job.pk),
            "data": {"selected_steps": ["step-1"]},
            "query": {"run_custom": "1"},
        },
    )
    payload = result["content"][0]["json"]
    assert result["isError"] is True
    assert payload["ok"] is False
    assert payload["reason"] == "custom-template"
    assert "not programmatically driveable" in payload["message"].lower()


@pytest.mark.django_db
def test_form_spec_no_custom_template_returns_field_map(superuser_client):
    """Path A (no query) → the stock change form → MCP returns the field map,
    unchanged: ``renderer != "custom-template"`` and ``fields`` present."""
    from tests.test_project.jobs.models import Job

    job = Job.objects.create(name="nightly", metadata={"k": "v"}, status="idle")
    spec = _call(
        superuser_client,
        "admin.form_spec",
        {"app_label": "jobs", "model_name": "job", "pk": str(job.pk)},
    )["content"][0]["json"]

    assert spec["renderer"] != "custom-template"
    assert "fields" in spec


# --------------------------------------------------------------------------- #
# Unit-level coverage of the discriminator helpers (no rest-api round trip).   #
# --------------------------------------------------------------------------- #
from django.http import HttpResponse  # noqa: E402

from django_admin_mcp_api.tools import custom_template  # noqa: E402
from django_admin_mcp_api.tools import form_submit  # noqa: E402


def test_discriminator_maps_submit_url_to_legacy_and_spa():
    body = {"renderer": "html-fragment", "submit_url": "/admin/jobs/job/7/change/?run_custom=1"}
    out = custom_template.discriminator(body)
    assert out["renderer"] == "custom-template"
    assert out["machine_driveable"] is False
    assert out["reason"] == "ModelAdmin override: change_form_template"
    assert out["legacy_url"] == "/admin/jobs/job/7/change/?run_custom=1"
    assert out["spa_url"] == "/admin2/jobs/job/7/change/?run_custom=1"


def test_is_custom_template_only_for_html_fragment():
    assert custom_template.is_custom_template({"renderer": "html-fragment"}) is True
    assert custom_template.is_custom_template({"renderer": "form-spec"}) is False
    assert custom_template.is_custom_template("not-a-dict") is False


def test_refusal_message_says_not_programmatically_driveable():
    refusal = custom_template.refusal()
    assert refusal["ok"] is False
    assert refusal["reason"] == "custom-template"
    assert "not programmatically driveable" in refusal["message"].lower()


class _StubDispatcher:
    """Returns a fixed HttpResponse body regardless of target — used to drive
    the form_submit intercept's resolution branch without rest-api."""

    def __init__(self, body):
        self._body = body

    def dispatch(self, *, request, target):  # noqa: ANN001, ARG002
        return HttpResponse(self._body, content_type="application/json")


def test_intercept_refuses_when_resolution_is_html_fragment(rf):
    request = rf.post("/mcp/")
    dispatcher = _StubDispatcher(
        b'{"renderer": "html-fragment", "submit_url": "/admin/x/y/1/change/"}'
    )
    result = form_submit._intercept(
        {"app_label": "x", "model_name": "y", "pk": "1", "data": {}}, request, dispatcher
    )
    assert result is not None
    body, status = result
    assert status == 422
    assert body == custom_template.refusal()


def test_intercept_passes_through_for_normal_form_spec(rf):
    request = rf.post("/mcp/")
    dispatcher = _StubDispatcher(b'{"renderer": "form-spec", "fields": {}}')
    result = form_submit._intercept(
        {"app_label": "x", "model_name": "y", "pk": "1", "data": {}}, request, dispatcher
    )
    assert result is None


def test_intercept_passes_through_on_unparseable_resolution(rf):
    request = rf.post("/mcp/")
    # Empty + non-JSON bodies both fall through to the normal forward path.
    assert (
        form_submit._intercept(
            {"app_label": "x", "model_name": "y", "data": {}}, request, _StubDispatcher(b"")
        )
        is None
    )
    assert (
        form_submit._intercept(
            {"app_label": "x", "model_name": "y", "data": {}},
            request,
            _StubDispatcher(b"<html>not json</html>"),
        )
        is None
    )
