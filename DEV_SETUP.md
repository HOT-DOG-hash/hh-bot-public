# Dev/Test Setup Snapshot

## Tooling
- Python: python3 -V → Python 3.12.3
- uv: uv --version → uv 0.9.4

## Dependency bootstrap
Commands:
  uv venv
  source .venv/bin/activate
  uv pip install -r requirements.txt -r requirements-dev.txt

## Alembic smoke (temp Postgres postgres:16-alpine @ 127.0.0.1:54329)
Commands:
  alembic downgrade base
  alembic upgrade head
  alembic downgrade base
  alembic upgrade head
  alembic heads
  alembic history --verbose | tail -n 20
Result: ✅ — single head p0_4_user_applications after round-trip.

## Pytest status
Commands:
  source .venv/bin/activate
  pytest -q
Result: ❌ — sqlite metadata & legacy relationships still block full suite (needs Postgres fixtures).

## Notes
- Added scripts/smoke_alembic.sh for CI smoke run.
- requirements*.txt, pytest.ini capture canonical dev/test baseline.
- Pending: wire Postgres fixtures or relax sqlite metadata to make pytest green.
