#!/usr/bin/env bash
# Dependency audit. CI fails the build on any known vulnerability.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "▶ pip-audit"
poetry run pip-audit

echo "✓ pip-audit clean"
