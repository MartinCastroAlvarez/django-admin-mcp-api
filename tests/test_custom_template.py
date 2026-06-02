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
