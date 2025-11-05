#!/usr/bin/env bash
set -euo pipefail

if [ -d "HH бот/backend" ]; then
  echo ">>> Переношу 'HH бот/backend' -> 'backend/'"
  git mv "HH бот/backend" backend
  echo ">>> Удаляю 'HH бот'"
  git rm -r "HH бот" || true
  echo ">>> Проверь импорты/CI на упоминания 'HH бот'"
else
  echo ">>> Нечего нормализовать"
fi
