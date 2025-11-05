# Datasets Overview — Ranking Spike (P2.1)

Каталог `research/datasets/` хранит данные для экспериментов по ранжированию (P2.1).

## Структура каталогов
```
research/datasets/
├─ raw/
│  ├─ vacancies_YYYYMMDD.jsonl
│  ├─ responses_YYYYMMDD.jsonl
│  └─ clicks_YYYYMMDD.parquet
├─ cleaned/
│  ├─ vacancies_clean.parquet
│  ├─ interactions.parquet
│  └─ labels.parquet
├─ features/
│  ├─ bm25_index/
│  ├─ tfidf_vectors/
│  └─ cooccurrence/
├─ quality_logs/
└─ README.md (этот файл)
```

## Политика именования и версионирования
- **Сырые снапшоты**: `vacancies_YYYYMMDD.jsonl` (дата выгрузки в UTC). Если требуется обновление — добавляем вторую выгрузку с суффиксом `_v2`.
- **Cleaned**: одиночные файлы, версионирование через Git + метаданные в `quality_logs/<timestamp>_quality.json`.
- **Features**: директории `bm25_index/<exp-tag>/`, `tfidf_vectors/<exp-tag>/`.
- **Архивы**: ежемесячно архивировать в S3 `ml-ranking/raw/archive/YYYYMM/`.

## Базовый срез и окна времени
- **Baseline (prod parity)**: данные за последние 30 календарных дней (rolling, UTC) с референсом `baseline_YYYYMMDD`. Используется для повторяемости оффлайн-оценки и сравнения с текущей выдачей BM25.
- **Train/Validation**: первые 20 дней baseline окна → train, следующие 7 дней → validation.
- **Holdout/Test**: финальные 3 дня baseline окна. Для онлайн decision framework используется как sanity check перед запуском A/B.
- Все даты и границы окон фиксируются в `quality_logs/<timestamp>_quality.json` (`window_start`, `window_end`, `baseline_tag`).

## Анонимизация и PII
- `email` / `phone` / `user_id` → `SHA-256(salt + value)` (соль в Vault, доступ ML/SRE lead).
- Timestamp → округление до часа (UTC).
- Свободный текст → NER-маска (фамилии/контакты заменяются на токены `<MASK_NAME>`).
- Проверка необратимости: скрипт `privacy_check.py` (планируется) сравнивает выборки хэшей.

## Ретеншн и доступы
| Слой | TTL | Доступ |
| --- | --- | --- |
| `raw/` | 60 дней | data-engineering (RW), ml-team (read on demand) |
| `cleaned/` | 180 дней | ml-team (RW), analytics (read) |
| `features/` | 90 дней | ml-team (RW) |
| `quality_logs/` | 365 дней | ml-team (read) |

## Чек-лист качества
1. Coverage: обязательные поля заполнены ≥95% (см. `SAMPLE_SCHEMA.md`).
2. Duplicate rate <1% за 7 дней (`owner_id_hashed + vacancy_id`).
3. Timestamps в окне 30 дней (±1 час).
4. Количество записей соответствует ожиданиям (vacancies ~120K, responses ~1.5M).
5. Лог проверки сохранён в `quality_logs/<timestamp>_quality.json`.

## Процедура обновления
1. Скопировать свежие сырые файлы в `raw/`.
2. Запустить пайплайн анонимизации → обновить `cleaned/`.
3. Генерировать признаки (BM25/TF-IDF) → `features/`.
4. Прогнать чек-лист качества и зафиксировать результат.
5. Обновить `RUN_LOG`.
