"""End-to-end integration tests against the real django-admin-rest-api.

These tests swap in :class:`RestApiDispatcher` (the production default)
and exercise a couple of read-only tools to confirm the wire bridges
all the way through to rest-api's view set. They use Django's built-in
``auth`` app — no example models needed.
"""

from __future__ import annotations

import json

import pytest
from django.test import override_settings

from tests.helpers import jsonrpc_call

MCP = "/mcp/"

# Drop the FakeDispatcher override so the default RestApiDispatcher is
# used. Everything else in tests/test_project/settings.py applies.
_REAL_DISPATCHER = override_settings(DJANGO_ADMIN_MCP_API={})


def _decode(response):
    return json.loads(response.content.decode("utf-8"))


@pytest.mark.django_db
def test_registry_tool_reaches_rest_api(staff_client):
    """admin.registry → rest-api RegistryView.

    The default Django admin registers ``auth.User`` and ``auth.Group``
    so we expect at least these two apps in the returned registry.
    """
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": "admin.registry", "arguments": {}}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert "result" in body, body
    content = body["result"]["content"][0]["json"]
    # rest-api returns a registry document; we don't pin the exact shape
    # (that's rest-api's contract), only that it is non-empty JSON.
    assert content, "Registry result was empty — rest-api wiring is broken"


@pytest.mark.django_db
def test_schema_tool_reaches_rest_api(staff_client):
    """admin.schema → rest-api SchemaView."""
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": "admin.schema", "arguments": {}}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert "result" in body, body


@pytest.mark.django_db
def test_form_spec_tool_reaches_rest_api(superuser_client):
    """admin.form_spec → rest-api FormSpecView (#70).

    Confirms the wire bridges through to the 1.4.0 form-spec endpoint and
    the byte-identical payload comes back: the add-view form for
    ``auth.group`` carries ``renderer == "form-spec"`` and a ``name``
    field whose resolved widget exposes the closed ``kind`` enum.
    """
    with _REAL_DISPATCHER:
        response = superuser_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.form_spec",
                    "arguments": {"app_label": "auth", "model_name": "group"},
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    content = _decode(response)["result"]["content"][0]["json"]
    assert content["renderer"] == "form-spec"
    assert "kind" in content["fields"]["name"]["widget"]


@pytest.mark.django_db
def test_form_submit_tool_surfaces_validation_errors(superuser_client):
    """admin.form_submit → rest-api create, re-running is_valid() (#70).

    Creating an ``auth.group`` with no name fails validation; the per-field
    error is surfaced under ``fields[name]`` exactly as the SPA / legacy
    admin would see it.
    """
    with _REAL_DISPATCHER:
        response = superuser_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.form_submit",
                    "arguments": {"app_label": "auth", "model_name": "group", "data": {}},
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    result = _decode(response)["result"]
    assert result["isError"] is True
    assert result["status"] == 400
    # rest-api's create error envelope nests per-field errors under error.fields.
    assert "name" in result["content"][0]["json"]["error"]["fields"]


@pytest.mark.django_db
def test_unknown_app_tool_returns_isError(staff_client):
    """A tool call for a model that doesn't exist surfaces rest-api's 404.

    The MCP envelope is still a JSON-RPC ``result`` (the call itself
    succeeded — we *got* an answer from rest-api). The ``isError`` flag
    inside the result content marks the upstream 4xx for the agent.
    """
    with _REAL_DISPATCHER:
        response = staff_client.post(
            MCP,
            data=jsonrpc_call(
                "tools/call",
                {
                    "name": "admin.retrieve",
                    "arguments": {
                        "app_label": "nonexistent",
                        "model_name": "model",
                        "pk": "1",
                    },
                },
            ),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    body = _decode(response)
    assert body["result"]["isError"] is True
    assert body["result"]["status"] >= 400


# --------------------------------------------------------------------------- #
# Custom request-driven form fixture (Job) — the cross-repo contract (#70).    #
#                                                                              #
# The Job admin overrides change_view to branch on ?run_custom=1 and render a  #
# hand-rolled template (no change_form_template attribute). The MCP wire must  #
# surface rest-api's two answers unchanged: the stock form-spec on Path A, and #
# the renderer=="legacy-iframe" discriminator on Path B — so an agent knows    #
# the form is not machine-driveable instead of inventing field values.         #
# --------------------------------------------------------------------------- #
def _form_spec_call(client, *, pk, query=None):
    args = {"app_label": "jobs", "model_name": "job", "pk": str(pk)}
    if query is not None:
        args["query"] = query
    with _REAL_DISPATCHER:
        response = client.post(
            MCP,
            data=jsonrpc_call("tools/call", {"name": "admin.form_spec", "arguments": args}),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    return _decode(response)["result"]["content"][0]["json"]


@pytest.mark.django_db
def test_form_spec_path_a_surfaces_textarea_metadata(superuser_client):
    """Path A (no query) — the stock change form: ``formfield_for_dbfield``
    surfaces the large-textarea widget on ``metadata``, machine-driveable."""
    from tests.test_project.jobs.models import Job

    job = Job.objects.create(name="nightly", metadata={"k": "v"}, status="idle")
    content = _form_spec_call(superuser_client, pk=job.pk)

    assert content["renderer"] == "form-spec"
    widget = content["fields"]["metadata"]["widget"]
    assert widget["kind"] == "textarea"
    assert widget["attrs"]["class"] == "vLargeTextField"


@pytest.mark.django_db
def test_form_spec_path_b_returns_legacy_iframe_discriminator(superuser_client):
    """Path B (query run_custom=1) — change_view renders a custom template,
    so the MCP wire forwards rest-api's ``legacy-iframe`` discriminator with
    the legacy URL preserved. An agent surfaces this as not-driveable.

    Version coupling (#75): the ``legacy-iframe`` discriminator is emitted by
    rest-api, not by this package — request-driven custom views were detected
    and surfaced starting in django-admin-rest-api 1.5.0. This test therefore
    only passes against a rest-api floor that ships that behaviour; our
    ``pyproject.toml`` floor of ``^1.6.0`` guarantees it on a fresh install.
    If this assertion regresses to ``form-spec``, the cause is almost always a
    rest-api version older than 1.5.0 — not a fixture or MCP-layer bug. The
    fixture ``JobAdmin.change_view`` (tests/test_project/jobs/admin.py) branches
    on ``?run_custom=1`` to a hand-rolled template, which is what makes rest-api
    classify the page as legacy/not-driveable."""
    from tests.test_project.jobs.models import Job

    job = Job.objects.create(name="nightly", status="idle")
    content = _form_spec_call(superuser_client, pk=job.pk, query={"run_custom": "1"})

    assert content["renderer"] == "legacy-iframe"
    assert content["legacy_url"] == f"/admin/jobs/job/{job.pk}/change/?run_custom=1"
