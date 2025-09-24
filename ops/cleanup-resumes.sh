#!/usr/bin/env bash
set -euo pipefail

# Допущение: запускается на прод-хосте по cron/systemd.
TARGET_DIR=${TARGET_DIR:-/opt/app/volumes/resumes}
RETENTION_DAYS=${RETENTION_DAYS:-30}

if [ ! -d "$TARGET_DIR" ]; then
  echo "[cleanup] skip: directory $TARGET_DIR not found" >&2
  exit 0
fi

find "$TARGET_DIR" -type f -mtime +"$RETENTION_DAYS" -print0 | xargs -0r rm -f
