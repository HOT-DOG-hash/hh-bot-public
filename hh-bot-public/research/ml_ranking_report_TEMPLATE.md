# ML Ranking Experiment Report — Template

## 1. Executive Summary
- **Experiment ID**: exp-YYYYMMDD-<tag>
- **Period**: YYYY-MM-DD – YYYY-MM-DD
- **Primary metric (Accept Rate)**: treatment vs control (+/- p.p., p-value, CI)
- **Decision**: Go / No-Go / Continue

## 2. Data Sources
- Offline baseline: `research/datasets/cleaned/` (`baseline_YYYYMMDD`, 30-дневное окно)
- Features: `research/datasets/features/bm25_index/<tag>`, `tfidf_vectors/<tag>`
- Online logs: ClickHouse (`ranking_impressions`, `ranking_interactions`, `ranking_accepts`)
- Feature flags & exposure: `ENABLE_ML_RANKING` (control=0, treatment=1)

## 3. Methodology
### 3.1 Offline evaluation
- Baseline(s) vs candidate(s), окна train/val/test (20/7/3 дня)
- Splits и bootstrap (K-fold time-based, 1 000 bootstrap итераций по owner_id)
- Metrics (Precision@K, nDCG@K, MAP) with mean ± CI

### 3.2 Online experiment
- Traffic allocation & ramp-up (10% → 50% → 100% при зелёных guard rails)
- Primary metric, secondary metrics, guard rails (CTR, opt-out, payments)
- Statistical tests (z-test / bootstrap) и уровень значимости (α = 0.05)

## 4. Results
### 4.1 Offline
| Model | Precision@10 | nDCG@10 | MAP@100 | CI |
| --- | --- | --- | --- | --- |

### 4.2 Online
| Metric | Control | Treatment | Δ | p-value | CI |
| --- | --- | --- | --- | --- | --- |

- Графики: Precision@K, nDCG@K, CTR timeline, Accept Rate timeline

## 5. Risks & Observations
- Data bias / shift (новые сегменты, холодный старт)
- Latency impact (SLA 60с p95)
- Opt-out / guard rails (OptOutSpike)
- Ethical considerations (fairness по льготным вакансиям)

## 6. Recommendations
- Suggested rollout (100%, staged, no-go) с обоснованием
- Follow-up tasks (model retraining cadence, monitoring improvements)
- Owner & timeline, ticket references

## 7. Appendix
- Experiment configuration
- Links to dashboards, Alertmanager, notebooks
- Raw metrics files: `experiments/<id>/metrics_summary.csv`
- Baseline snapshot metadata: `quality_logs/<timestamp>_quality.json`
