"""Per-tool ``build_target`` translation tests.

Asserts the exact HTTP shape each MCP tool forwards to
django-admin-rest-api. These tests are the contract that protects the
1:1 mapping between MCP tools and rest-api endpoints.
"""

from __future__ import annotations

import pytest

from django_admin_mcp_api import tools

# (tool_name, valid_arguments, expected_method, expected_path,
#  expected_body, expected_query)
CASES = [
    (
        "admin.registry",
        {},
        "GET",
        "/registry/",
        None,
        None,
    ),
    (
        "admin.schema",
        {},
        "GET",
        "/schema/",
        None,
        None,
    ),
    (
        "admin.recent_actions",
        {},
        "GET",
        "/recent-actions/",
        None,
        None,
    ),
    (
        "admin.list",
        {"app_label": "auth", "model_name": "user", "page": 1, "search": "ada"},
        "GET",
        "/auth/user/",
        None,
        {"page": "1", "search": "ada"},
    ),
    (
        "admin.retrieve",
        {"app_label": "auth", "model_name": "user", "pk": "7"},
        "GET",
        "/auth/user/7/",
        None,
        None,
    ),
    (
        "admin.add_form",
        {"app_label": "auth", "model_name": "user"},
        "GET",
        "/auth/user/add/",
        None,
        None,
    ),
    (
        "admin.create",
        {"app_label": "auth", "model_name": "user", "data": {"username": "ada"}},
        "POST",
        "/auth/user/",
        {"username": "ada"},
        None,
    ),
    (
        "admin.update",
        {"app_label": "auth", "model_name": "user", "pk": "7", "data": {"is_active": False}},
        "PATCH",
        "/auth/user/7/",
        {"is_active": False},
        None,
    ),
    (
        "admin.destroy",
        {"app_label": "auth", "model_name": "user", "pk": "7"},
        "DELETE",
        "/auth/user/7/",
        None,
        None,
    ),
    (
        "admin.bulk_update",
        {
            "app_label": "auth",
            "model_name": "user",
            "pks": ["1", "2"],
            "data": {"is_active": True},
        },
        "PATCH",
        "/auth/user/bulk/",
        {"pks": ["1", "2"], "data": {"is_active": True}},
        None,
    ),
    (
        "admin.autocomplete",
        {"app_label": "auth", "model_name": "user", "q": "ad"},
        "GET",
        "/auth/user/autocomplete/",
        None,
        {"q": "ad"},
    ),
    (
        "admin.action",
        {
            "app_label": "auth",
            "model_name": "user",
            "action_name": "deactivate",
            "pks": ["1"],
        },
        "POST",
        "/auth/user/actions/deactivate/",
        {"pks": ["1"]},
        None,
    ),
    (
        "admin.history",
        {"app_label": "auth", "model_name": "user", "pk": "7"},
        "GET",
        "/auth/user/7/history/",
        None,
        None,
    ),
    (
        "admin.delete_preview",
        {"app_label": "auth", "model_name": "user", "pk": "7"},
        "GET",
        "/auth/user/7/delete-preview/",
        None,
        None,
    ),
    (
        "admin.set_password",
        {"app_label": "auth", "model_name": "user", "pk": "7", "password": "x"},
        "POST",
        "/auth/user/7/password/",
        {"password": "x"},
        None,
    ),
    (
        "admin.panel",
        {"app_label": "auth", "model_name": "user", "pk": "7", "panel_name": "audit"},
        "GET",
        "/auth/user/7/panel/audit/",
        None,
        None,
    ),
]


@pytest.mark.parametrize(
    ("name", "args", "method", "path", "body", "query"),
    CASES,
    ids=[c[0] for c in CASES],
)
def test_build_target(name, args, method, path, body, query):
    tool = tools.by_name(name)
    assert tool is not None, f"Tool {name!r} not registered"
    target = tool.build_target(args)
    assert target.method == method
    assert target.path == path
    assert target.body == body
    assert target.query == query


def test_every_tool_covered_by_cases():
    catalogued = {t.name for t in tools.all_tools()}
    covered = {c[0] for c in CASES}
    assert (
        catalogued == covered
    ), f"Tool coverage drift — missing: {catalogued - covered}, extra: {covered - catalogued}"
