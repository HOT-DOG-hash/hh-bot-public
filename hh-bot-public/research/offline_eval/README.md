# Offline Evaluation — How to Reproduce

## Каталоги
```
research/offline_eval/
├─ experiments/
│  └─ exp-YYYYMMDD-<tag>/
│     ├─ configs/
│     ├─ logs/
│     ├─ metrics_summary.csv
│     ├─ metrics_by_segment.csv
│     └─ plots/
├─ notebooks/
└─ scripts/
```

## Нейминг
- Эксперимент: `exp-20251104-bm25-baseline` (дата + короткий тег).
- Модели: `model_bm25_prod`, `model_tfidf_rules`, `model_ml_candidate`.
- Файлы отчетов: `metrics_summary.csv`, `metrics_by_segment.csv`, `bootstrap_stats.json`.

## Входы
- `research/datasets/cleaned/` (vacancies_clean, interactions, labels).
- `research/datasets/features/` (bm25_index, tfidf_vectors и др.).
- Конфиг эксперимента (`experiments/<exp>/configs/config.yaml`).

## Выходы
- CSV с метриками и CI.
- Папка `plots/` (Precision@K, nDCG@K, gain chart).
- Логи (bootstrap результаты, параметры запуска).
- Черновик отчёта (ссылка на `ml_ranking_report_TEMPLATE.md`).

## Процедура без тяжёлого кода
1. Скопировать шаблон конфига (sample TBD) в `experiments/<exp>/configs/`.
2. Подготовить baseline/candidate данные (вручную или простым скриптом).
3. Использовать существующие инструменты (например, pandas/py scripts) — TODO дополнить.
4. Сохранить результаты в `metrics_summary.csv` и обновить отчёт.

## Отчётность
- Минимально: summary таблица, сегментная таблица, визуализации.
- Использовать `ml_ranking_report_TEMPLATE.md` для финального документа.
