#!/usr/bin/env bash
# Clean + build the distribution. Run before `poetry publish`.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "▶ Cleaning dist/"
rm -rf dist/

echo "▶ poetry build"
poetry build

echo
echo "▶ Dist contents:"
ls -la dist/

echo
echo "✓ Build complete. Next step:"
echo "    poetry publish    # uses POETRY_PYPI_TOKEN_PYPI from your env"
