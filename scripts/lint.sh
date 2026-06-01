#!/usr/bin/env bash
# Full lint gate. CI runs the same set.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "▶ ruff (lint + isort)"
poetry run ruff check django_admin_mcp_api tests

echo "▶ ruff (format check)"
poetry run ruff format --check django_admin_mcp_api tests

echo "▶ mypy"
poetry run mypy django_admin_mcp_api

echo "▶ bandit"
poetry run bandit -c pyproject.toml -q -r django_admin_mcp_api

echo "✓ Lint gate passed"
