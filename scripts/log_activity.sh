#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$ROOT_DIR/PROJECT_ACTIVITY_LOG.txt"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"message\""
  exit 1
fi

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
MESSAGE="$*"

printf '[%s] %s\n' "$TIMESTAMP" "$MESSAGE" >> "$LOG_FILE"
echo "Appended to $LOG_FILE"
