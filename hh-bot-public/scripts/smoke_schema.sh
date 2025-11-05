#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

echo ">>> Alembic smoke #1"
uvx alembic downgrade base
uvx alembic upgrade head

echo ">>> Alembic smoke #2"
uvx alembic downgrade base
uvx alembic upgrade head

echo ">>> OK"
