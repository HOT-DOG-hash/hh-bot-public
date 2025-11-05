# Auto Campaigns OpenAPI Changelog

## 2025-11-04 (code sync)

- Aligned `/api/v1/auto/campaigns/{id}/start` responses with backend NotFound handling (adds explicit 404 mapping).
- Reconfirmed health/readyz/metrics coverage and kept lint commands up to date.

## 2025-11-04

- Added first code-synced contract `auto_campaigns.yaml` (v1.0.0) covering write operations, blacklist flows, and support probes.
- Documented `Idempotency-Key` requirements, error envelopes, and readiness/metrics endpoints.
- Added Spectral lint configuration `.spectral.yaml` and captured lint commands for local validation.

### Linting & Validation

Run both linters whenever the specification changes:

```bash
npx @redocly/cli lint docs/openapi/auto_campaigns.yaml
npx spectral lint docs/openapi/auto_campaigns.yaml
```

Both commands read `.spectral.yaml` in repo root and emit violations without failing if the tools are missing (CI handles graceful degradation).
