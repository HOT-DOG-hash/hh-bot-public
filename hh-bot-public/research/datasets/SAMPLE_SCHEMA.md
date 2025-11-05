# Sample Schemas — Ranking Spike Datasets

## Vacancies (raw)
| Поле | Тип | Описание |
| --- | --- | --- |
| vacancy_id | string | UUID вакансии |
| employer_id | string | ID работодателя |
| title | string | Заголовок вакансии |
| description | string | Полный текст |
| skills | array[string] | Массив навыков |
| salary_from | integer | Нижняя граница |
| salary_to | integer | Верхняя граница |
| currency | string | Код валюты |
| created_at | string (datetime) | Время создания |

## Responses (raw)
| Поле | Тип | Описание |
| --- | --- | --- |
| response_id | string | UUID отклика |
| vacancy_id | string | Связь с вакансией |
| owner_id | string | Пользователь (PII) |
| outcome | string | `accepted`, `rejected`, `pending` |
| responded_at | string (datetime) | Время отклика |

## Clicks (raw)
| Поле | Тип | Описание |
| --- | --- | --- |
| event_id | string | UUID события |
| vacancy_id | string | Связь |
| owner_id | string | Пользователь |
| event_type | string | `impression`, `click` |
| position | integer | Позиция в выдаче |
| event_ts | string (datetime) | Время события |

## Interactions (cleaned)
| Поле | Тип | Описание |
| --- | --- | --- |
| owner_id_hashed | string | Хэш пользователя |
| vacancy_id | string | ID вакансии |
| label_int | integer | 0/1/2 релевантность |
| source | string | `click`, `response`, `accept` |
| timestamp_hour | string (datetime) | Округлённое время |

## Labels (cleaned)
| Поле | Тип | Описание |
| --- | --- | --- |
| vacancy_id | string | ID вакансии |
| relevance_score | float | Значение [0,1] |
| sample_count | integer | Количество событий |
