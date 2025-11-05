# ML Ranking Experiment — A/B Test Plan

## 1. Summary
- **Goal:** измерить uplift Accept Rate и CTR от ML-ранжирования.
- **Feature flag:** `ENABLE_ML_RANKING` (control → False, treatment → True).
- **Traffic allocation:** 50/50 после ramp-up.

## 2. Ramp-up Strategy
| Stage | Traffic | Duration | Exit criteria |
| --- | --- | --- | --- |
| Stage 1 | 10% treatment | ≥ 48h | guardrails ok, p95 latency < 3s |
| Stage 2 | 25% treatment | ≥ 48h | guardrails ok |
| Stage 3 | 50% treatment | until stop | follow decision framework |

## 3. Stratification
- Hash by `owner_id` (deterministic assignment).
- Ensure balanced segments: `plan_code` (WEEKLY/MONTHLY), geo (RU/CIS/Other), channel.
- Exclude opt-out users and manual overrides.

## 4. Metrics
- **Primary:** Accept Rate (7d rolling), CTR (daily).
- **Secondary:** time-to-respond, auto-pause rate, error burst rate.
- **Guard rails:** Opt-out spike > 5%, payments failed > baseline, partner ingest errors > threshold.

## 5. Sample Size & Duration
- Target uplift: +2 p.p. Accept Rate, +5% CTR.
- α = 0.05, power = 0.8 ⇒ ~13k owners per variant (≥26k total) с ≥1 run.
- Minimum duration: 14 days (cover weekly patterns) или до достижения объёма.

## 6. Stop Criteria
- **Positive:** uplift по обеим primary метрикам, p-value < 0.05, guard rails green ≥ 3 дня.
- **Negative:** CTR ↓ >3 п.п. или Accept Rate ↓ >1.5 п.п. ≥ 2 дня; latency/alert breaches → rollback.
- **Scheduled:** 28 дней максимум; если эффект незначим, решаем iterate/no-go.

## 7. Ethics & Safety
- сохраняем опцию «вернуть старый ранж» для пользователей;
- не показывать низкокачественные вакансии (фильтры baseline остаются);
- конфиденциальность соблюдается, PII не выводим в отчётах.

## 8. Reporting & Ownership
- Weekly status → product/analytics.
- Final report using `research/ml_ranking_report_TEMPLATE.md`.
- Owner: Experimentation team; SRE на дежурстве для guard rails.
