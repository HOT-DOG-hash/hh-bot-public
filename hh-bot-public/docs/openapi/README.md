# OpenAPI Tooling — Auto Campaigns

## Lint Commands
Run both tools after editing `auto_campaigns.yaml`:

```bash
npx @redocly/cli lint docs/openapi/auto_campaigns.yaml
npx spectral lint docs/openapi/auto_campaigns.yaml
```

The repo ships `.spectral.yaml` (extends `spectral:oas`). Install the CLIs locally or rely on CI fallbacks.

## Spec Location
- `docs/openapi/auto_campaigns.yaml`
- Update `docs/openapi/CHANGELOG.md` with a short note for each sync.

## Related Docs
- Backend routes: `backend/app/routers/auto_campaigns.py`
- Schemas: `backend/app/schemas/auto_campaigns.py`
- Services: `backend/app/services/auto_campaigns.py`
