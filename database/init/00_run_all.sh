#!/bin/bash
# Runs once, on the container's FIRST boot (empty data volume), by the
# gvenzl/oracle-free entrypoint. It executes every schema/ file then every
# seed/ file in filename order, connected as the app user (not SYS), so all
# objects are owned by the least-privilege "cardshop" schema.
#
# To re-run from scratch:  docker compose down -v && docker compose up -d db

DB_DIR=/opt/cardshop/database
CONNECT="${APP_USER}/${APP_USER_PASSWORD}@//localhost/FREEPDB1"

run_sql_file() {
  echo "[cardshop-init] running $1"
  sqlplus -s -L "$CONNECT" <<SQL
WHENEVER SQLERROR EXIT SQL.SQLCODE
WHENEVER OSERROR EXIT FAILURE
SET DEFINE OFF
SET FEEDBACK OFF
@$1
EXIT
SQL
}

(
  set -e
  for f in "$DB_DIR"/schema/*.sql "$DB_DIR"/seed/*.sql; do
    run_sql_file "$f"
  done
) && echo "[cardshop-init] SUCCESS: schema and seed data loaded" \
  || echo "[cardshop-init] FAILED: see the error above; fix it, then 'docker compose down -v' and retry"
