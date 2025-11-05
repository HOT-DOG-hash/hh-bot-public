# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Telegram-based job application automation bot** with integrated subscription and payment management. Users interact with a Telegram bot to create job application campaigns, which are automated according to quota and subscription plans.

**Technology Stack:**
- **Backend**: FastAPI 0.111.0 + Uvicorn 0.30.1
- **Database**: PostgreSQL 16 (prod) / SQLite (dev) via SQLAlchemy 2.0.32 + asyncpg
- **Cache**: Redis 7 (redis 5.0.6)
- **Telegram Bot**: python-telegram-bot 20.8 with httpx 0.26.0 (version pinned for PTB compatibility)
- **Admin Frontend**: Vite + React + TypeScript + Tailwind + shadcn/ui
- **Infrastructure**: Docker multi-stage builds, nginx reverse proxy, optional Cloudflare tunnel
- **Migrations**: Alembic 1.13.2
- **Testing**: pytest 8.3.2 with async support
- **Monitoring**: prometheus-client 0.20.0

## Development Commands

### Local Development Setup
```bash
# Install dependencies (from hh-bot-public/)
pip install -r requirements.txt
# or use uv for faster installation
uv pip install -r requirements.txt

# Run backend locally
uvicorn backend.app.main:app --reload

# Docker stack (recommended)
docker compose --env-file .env.local up -d db cache
docker compose --env-file .env.local up -d web front nginx
```

### Database Migrations
```bash
# Run migrations
docker compose exec -T web alembic upgrade head

# Check current revision
docker compose exec -T web alembic current

# Generate new migration
docker compose exec -T web alembic revision --autogenerate -m "description"

# Or locally
alembic upgrade head
alembic current
alembic revision --autogenerate -m "description"
```

### Testing
```bash
# Fast unit tests (SQLite, no PostgreSQL required)
pytest -q -m "not pg"

# Full test suite including PostgreSQL tests
pytest

# With coverage
pytest --cov

# Run specific test file
pytest backend/tests/billing/test_billing_service.py -v
```

### Development Checks
```bash
# Comprehensive checks (ruff, mypy, alembic smoke, pytest)
./scripts/dev_check.sh
```

### Key Makefile Targets
```bash
make up          # Start all services
make down        # Stop all services
make logs        # Tail all logs
make logs-web    # Tail web service logs
make logs-bot    # Tail bot service logs
make bash-web    # Shell into web container
make bash-bot    # Shell into bot container
make health      # Health check via nginx
make admin-sync  # Sync admin credentials to nginx
make nginx:test  # Test nginx config
make nginx:reload # Reload nginx
```

### Environment Setup Sequence
1. Copy `.env.local.sample` to `.env.local` and configure
2. Generate dev certificates (if needed): `pwsh tools\dev-cert-gen.ps1`
3. Check/set nginx ports: `pwsh tools\set-nginx-ports.ps1`
4. Start services in order: db/cache first, then web/front/nginx

## High-Level Architecture

### Three-Tier Architecture

```
Telegram Users → Telegram Bot (front_bot/) → FastAPI Backend (backend/app/) → PostgreSQL + Redis
                                          ↘
                                           Admin SPA (admin_front/) → nginx BasicAuth
```

**Critical Design Principle**: The Telegram bot acts as an **HTTP client** to the FastAPI backend. It does NOT have direct database access. Communication uses `httpx.AsyncClient` with `ASGITransport` for in-process requests during development, and HTTP for production.

### Main Components

#### 1. Backend API (FastAPI)
- **Entry point**: `backend/app/main.py`
- **Router structure** (`backend/app/routers/`):
  - `admin.py`, `admin_api/*` - Admin dashboard API
  - `billing.py` - Subscription lifecycle operations
  - `payments.py` - YooMoney payment integration
  - `quota.py` - Usage quota management and consumption
  - `auto_campaigns.py` - Job application campaign orchestration
  - `resumes.py`, `search_query.py` - Resume and search management
  - `bot_api/*` - Bot-specific endpoints
  - `health.py`, `readyz.py`, `metrics.py` - Observability

#### 2. Telegram Bot Frontend
- **Location**: `front_bot/` directory
- **Integration**: Calls backend via HTTP, never touches database directly
- **Handlers**: `front_bot/routers/start.py` implements 10-step campaign creation wizard
- **Commands**: `/start`, `/campaign`, `/plans`, `/quota`

#### 3. Data Layer
- **Models** in `backend/app/models/`:
  - `user.py` - User accounts
  - `plan.py`, `subscription.py`, `payments.py` - Billing system
  - `quota.py` - Usage tracking
  - `auto_campaigns.py` - Campaign automation
  - `resume.py`, `search_query.py`, `settings.py`, `blacklist.py`
- **Base model**: `TimestampMixin` adds `created_at`/`updated_at` to all models
- **Migrations**: `backend/migrations/versions/` with P0.x/P1.x naming for feature phases

#### 4. Services Layer
- **Location**: `backend/app/services/`
- **Key services**:
  - `billing.py` - FSM-based payment and subscription logic (14KB, complex state machine)
  - `auto_campaigns.py` - Campaign orchestration with frequency caps and cooldown policies (28KB)
  - `health_checks.py` - Readiness probes for dependencies
  - `analytics.py`, `users.py` - Supporting services

#### 5. Integration Pipeline
- **Location**: `integration/` directory
- **4-stage pipeline**: ingest → normalize → validate → store
- **Partner connectors**: hh.ru OAuth, Habr Career API
- **Idempotency**: Redis + hash-based deduplication
- **Data flow**: Parquet intermediates → JSONB storage in PostgreSQL
- **Documentation**: `integration/PIPELINE.md`, `integration/SCHEMAS.md`

### Key Architecture Patterns

#### FSM-Based Billing System
The payment and subscription logic uses finite state machines:

**Payment States**: `initiated → pending → succeeded/failed`
**Subscription States**: `trial → active → grace_period → expired → canceled`

- Idempotent payment initiation via `idempotency_key`
- All state transitions logged for audit
- YooMoney webhook integration updates payment states
- See `backend/app/services/billing.py` for FSM implementation

#### Dual Authentication Pattern
1. **nginx BasicAuth**: Protects admin routes at reverse proxy level
   - Credentials in `nginx/.htpasswd` (bcrypt hashed)
   - Sync credentials: `make admin-sync`
2. **Backend Token Auth**: `ADMIN_SECRET_TOKEN` for API endpoint authorization
   - Used in admin API routes
   - Must match between nginx and backend config

#### Money Representation Convention
- **Storage**: Always store money as TWO fields:
  - `amount_minor` (Integer) - Amount in kopecks/cents (integer arithmetic, no floating point errors)
  - `amount` (NUMERIC) - Decimal amount for display/reporting
- **Validation**: Pydantic models enforce consistency between fields
- **Example**: 100.50 RUB → `amount_minor=10050`, `amount=100.50`

#### Migration Strategy
- **Naming**: Prefix with P0.x/P1.x to track feature phase
- **Seed data**: Migrations include default plans (FREE_TRIAL, WEEKLY, MONTHLY)
- **Dual DB support**: SQLite for dev (fast), PostgreSQL for prod
- **Autogenerate caveat**: SQLite has FK constraint limitations in Alembic autogen

#### Observability Pattern
- **/health** - Simple liveness check (no dependencies)
- **/readyz** - Readiness check with DB and Redis connectivity
- **/metrics** - Prometheus metrics (campaigns, payments, quotas, webhooks)
- **Structured logging**: Configurable levels, JSON format for production
- **Alert rules**: Defined in `docs/ops/observability_spec.md`

### Important Directory Structure

```
backend/
  app/
    main.py              # FastAPI app entry point
    routers/             # API route handlers
    models/              # SQLAlchemy ORM models
    services/            # Business logic layer
    schemas/             # Pydantic request/response schemas
  migrations/            # Alembic migration scripts
  tests/                 # Test suite mirroring app structure

front_bot/               # Telegram bot frontend (HTTP client to backend)
  routers/               # Bot command handlers

admin_front/             # React admin SPA
  src/                   # Vite + React + TypeScript

integration/             # Partner data pipeline (P2.2 feature)
  PIPELINE.md            # Pipeline architecture
  SCHEMAS.md             # Storage schemas

docs/
  LOCAL_DEV.md           # Comprehensive local dev guide
  ops/                   # Operational runbooks
    observability_spec.md
  SECRETS_POLICY.md      # Security policy

scripts/
  dev_check.sh           # Lint, type check, test automation

nginx/                   # Reverse proxy configuration
  .htpasswd              # BasicAuth credentials (bcrypt)
```

## Important Development Patterns

### Testing with Database Markers
Tests are marked to support both SQLite (fast) and PostgreSQL (production-like):

```python
@pytest.mark.pg  # Requires PostgreSQL
def test_complex_query():
    ...
```

Run fast tests: `pytest -m "not pg"`
Run all tests: `pytest`

### Idempotency Keys
Payment operations require idempotency keys to prevent duplicate charges:

```python
POST /api/v1/payments/initiate
{
    "idempotency_key": "unique-key-per-user-action",
    "plan_code": "MONTHLY",
    ...
}
```

The backend deduplicates based on this key. Always generate unique keys per user action.

### Identity Object Pattern
API endpoints identify users via identity objects:

```python
{"telegram_id": 123456789}
```

This abstraction allows future support for multiple identity providers.

### Webhook Deduplication
YooMoney webhooks use `provider_event_id` for deduplication:
- Store event IDs in Redis/DB
- Skip processing if ID already seen
- Prevents double-crediting from webhook retries

### Quota Consumption
Quota is consumed per campaign action:

```python
POST /api/v1/quota/consume
{
    "user_identity": {"telegram_id": ...},
    "amount": 1,
    "reason": "campaign_delivery"
}
```

Backend checks active subscription and enforces plan limits.

## Common Development Workflows

### Payment Flow Integration
1. User activates trial → `POST /api/v1/billing/trial/activate`
2. User consumes quota → `POST /api/v1/quota/consume`
3. On quota exhaustion → `POST /api/v1/payments/initiate` (returns `invoice_url`)
4. User pays via YooMoney
5. YooMoney webhook → `POST /api/v1/payments/webhook` updates FSM
6. Subscription activated, quota replenished
7. Metrics tracked via Prometheus counters/gauges at `/metrics`

### Campaign Automation Flow
1. User creates campaign via 10-step Telegram wizard
2. Bot validates inputs and calls `POST /api/v1/auto/campaigns` with idempotency key
3. Backend scheduler runs delivery attempts (respects frequency caps and cooldown policies)
4. Delivery logs track sent/skipped/failed results per vacancy
5. Campaign auto-pauses on error streaks (configurable threshold)
6. User views status via bot commands or admin dashboard

### Partner Data Integration (P2.2)
1. Cron triggers ingest from hh.ru/Habr Career APIs
2. Data normalized (currency conversion, location mapping, PII removal)
3. Validation against schema rules (required fields, enum values)
4. Merge into core tables via `INSERT ... ON CONFLICT DO UPDATE`
5. CDC events to Kafka for data warehousing (future)
6. See `integration/PIPELINE.md` for details

## Important Configuration Notes

### Environment Variables
Multiple `.env` variants exist for different environments:
- `.env.local.sample` - Local development template
- `.env.example` - General example
- Additional variants for prod, Docker, Neon DB

**Critical**: Never commit actual `.env` files or secrets. See `docs/SECRETS_POLICY.md`.

### httpx Version Pinning
httpx is pinned to `==0.26.0` for python-telegram-bot 20.x compatibility. Do NOT upgrade without verifying PTB compatibility.

### Database Timezone Convention
All timestamps use `TIMESTAMPTZ` with UTC timezone. Always use timezone-aware datetime objects in Python.

### Known Issues
- Git pack corruption previously reported (see `ANALYZE.md`) - recommend fresh clone if issues
- Docker Desktop stability issues on Windows noted in documentation
- SQLite FK constraints have limitations with Alembic autogenerate
- Directory path with Cyrillic characters ("HH бот") handled in Dockerfile WORKDIR

## Monitoring and Debugging

### Health Check Endpoints
- `/health`, `/healthz` - Liveness (no dependency checks)
- `/readyz`, `/api/healthz` - Readiness (DB + Redis checks)
- `/api/health` - Detailed health status
- `/metrics` - Prometheus metrics

Access via nginx: `make health` or `curl http://localhost:8080/health`

### Logs
```bash
make logs              # All services
make logs-web          # Backend API
make logs-bot          # Telegram bot
make logs-nginx        # Reverse proxy

# Or directly
docker compose logs -f web
docker compose logs -f bot --tail=100
```

### Metrics
Prometheus metrics available at `/metrics`:
- `campaigns_total`, `campaigns_active` - Campaign counters
- `payments_initiated_total`, `payments_succeeded_total` - Payment tracking
- `quota_consumed_total`, `quota_remaining` - Usage tracking
- `webhook_received_total`, `webhook_processed_total` - Integration health

### Admin Dashboard
Access at `http://localhost:8080/admin` with BasicAuth credentials.
Credentials managed via `make admin-sync` and `make admin-rotate`.

## Documentation References

- **Local Development**: `docs/LOCAL_DEV.md` - Comprehensive Windows/Docker setup
- **Payment System**: `design/PAYMENT_SCHEMA_SPEC.md` - Complete payment schema
- **Integration Pipeline**: `integration/PIPELINE.md` - Partner data architecture
- **Observability**: `docs/ops/observability_spec.md` - Metrics, SLOs, alerts
- **Security**: `docs/SECRETS_POLICY.md` - Secrets management policy
- **Repository Audit**: `ANALYZE.md` - Detailed codebase analysis from 2025-10-12
- **Changelog**: `DEV_CHANGELOG.md` - Development milestone tracking
