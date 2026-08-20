#!/usr/bin/env bash
#
# tooling_db.sh — manage the local Postgres "tooling DB" that runs alongside DDEV.
#
# Commands:
#   migrate   Apply every tooling-db/migrations/*.sql (idempotent)
#   status    Show tables + row counts + applied migrations
#   psql      Open an interactive psql shell
#   reset     DROP and recreate the schema (destructive; asks for confirmation)
#
# Connection (local dev creds only, not secrets):
#   from host:          127.0.0.1:5433  db=vertical_tooling user=tooling
#   from DDEV web:      postgres:5432   db=vertical_tooling user=tooling
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PROJECT="$(basename "$REPO_ROOT")"        # matches .ddev project name (vertical-web)
PG_CONTAINER="ddev-${PROJECT}-postgres"
DB="vertical_tooling"
DBUSER="tooling"
MIGRATIONS_DIR="tooling-db/migrations"

require_container() {
  if ! docker ps --format '{{.Names}}' | grep -qx "$PG_CONTAINER"; then
    echo "ERROR: $PG_CONTAINER is not running. Run 'ddev start' (or 'ddev restart')." >&2
    exit 1
  fi
}

psql_exec() {   # non-interactive SQL from stdin
  docker exec -i "$PG_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DBUSER" -d "$DB" "$@"
}

cmd="${1:-help}"
case "$cmd" in
  migrate)
    require_container
    shopt -s nullglob
    files=("$MIGRATIONS_DIR"/*.sql)
    [ ${#files[@]} -gt 0 ] || { echo "No migrations found in $MIGRATIONS_DIR"; exit 1; }
    for f in "${files[@]}"; do
      echo "==> applying $f"
      psql_exec < "$f"
    done
    echo "Done."
    ;;

  status)
    require_container
    echo "== tables =="
    psql_exec -c "\dt"
    echo "== row counts =="
    psql_exec -Atc "
      SELECT relname || ' = ' || n_live_tup
      FROM pg_stat_user_tables ORDER BY relname;"
    echo "== applied migrations =="
    psql_exec -Atc "SELECT version || ' @ ' || applied_at FROM schema_migrations ORDER BY version;" \
      2>/dev/null || echo "(schema_migrations not present yet — run: $0 migrate)"
    ;;

  psql)
    require_container
    docker exec -it "$PG_CONTAINER" psql -U "$DBUSER" -d "$DB"
    ;;

  reset)
    require_container
    read -r -p "This DROPs and recreates the '$DB' schema. Type 'reset' to confirm: " ans
    [ "$ans" = "reset" ] || { echo "Aborted."; exit 1; }
    psql_exec -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    "$0" migrate
    ;;

  *)
    sed -n '2,20p' "$0"
    ;;
esac
