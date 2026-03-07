#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIGRATIONS_DIR="$ROOT_DIR/backend/migrations"

if [[ -z "${POSTGRES_DSN:-}" && -f "$ROOT_DIR/.env" ]]; then
  POSTGRES_DSN="$(sed -n 's/^POSTGRES_DSN=//p' "$ROOT_DIR/.env")"
fi

if [[ ! -d "$MIGRATIONS_DIR" ]]; then
  echo "[FAIL] Migration directory not found: $MIGRATIONS_DIR"
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "[FAIL] psql command not found. Install PostgreSQL client tools first."
  exit 1
fi

if [[ -z "${POSTGRES_DSN:-}" ]]; then
  echo "[FAIL] POSTGRES_DSN is not set. Add it to .env before running migrations."
  exit 1
fi

echo "[STEP 6] Applying case-store migrations"
for migration in "$MIGRATIONS_DIR"/*.sql; do
  [[ -f "$migration" ]] || continue
  echo "[INFO] Applying $(basename "$migration")"
  psql "$POSTGRES_DSN" -v ON_ERROR_STOP=1 -f "$migration"
done

echo "[PASS] Case-store migrations applied successfully."
