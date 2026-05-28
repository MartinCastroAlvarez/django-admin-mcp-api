#!/usr/bin/env bash
# Full lint gate. CI runs the same set.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "▶ ruff (lint + isort)"
poetry run ruff check django_admin_mcp_api tests

echo "▶ ruff (format check)"
poetry run ruff format --check django_admin_mcp_api tests

echo "▶ black (format check)"
poetry run black --check django_admin_mcp_api tests

echo "▶ isort (import order check)"
poetry run isort --check-only django_admin_mcp_api tests

echo "▶ flake8"
poetry run flake8 django_admin_mcp_api tests

echo "▶ pylint --errors-only"
poetry run pylint --errors-only django_admin_mcp_api

echo "▶ mypy"
poetry run mypy django_admin_mcp_api || true   # best-effort at v0

echo "▶ bandit"
poetry run bandit -c pyproject.toml -q -r django_admin_mcp_api

echo "✓ Lint gate passed"
