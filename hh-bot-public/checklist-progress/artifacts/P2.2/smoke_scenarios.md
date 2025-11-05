# Smoke Scenarios — Partner Pipeline

1. **Happy path (hh.ru)**
   - Использовать `integration/mocks/hh_sample.json`.
   - Expect: ingest ok, normalize OK, stored in staging/core.

2. **Rate limit (hh.ru)**
   - Использовать `integration/mocks/hh_errors.json` 429.
   - Expect: retry per policy, log entry, alert triggered if persistent.

3. **Server error (Habr)**
   - Использовать `habr_errors` (TODO) -> simulate 5xx.
   - Expect: retries 5 times, final alert.

4. **Empty salary**
   - Variant of mock with missing salary: pipeline flags warning.

5. **Broken encoding**
   - Inject malformed JSON to ensure validation catches it.

6. **Idempotent re-run**
   - Re-submit same `external_id`, expect dedupe (no duplicate insert).
