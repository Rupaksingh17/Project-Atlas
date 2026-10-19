#!/bin/sh
set -eu

# Restrict password characters so values remain safe in the generated SQL.
case "${ATLAS_APP_PASSWORD:-}" in ''|*[!A-Za-z0-9_-]*) echo "DB_PASSWORD must use letters, numbers, _ or -" >&2; exit 1;; esac
case "${ATLAS_READONLY_PASSWORD:-}" in ''|*[!A-Za-z0-9_-]*) echo "READONLY_DB_PASSWORD must use letters, numbers, _ or -" >&2; exit 1;; esac
case "${MYSQL_ROOT_PASSWORD:-}" in ''|*CHANGE_ME*) echo "MYSQL_ROOT_PASSWORD must be set to a unique secret" >&2; exit 1;; esac
case "${ATLAS_APP_PASSWORD}" in *CHANGE_ME*) echo "DB_PASSWORD must be set to a unique secret" >&2; exit 1;; esac
case "${ATLAS_READONLY_PASSWORD}" in *CHANGE_ME*) echo "READONLY_DB_PASSWORD must be set to a unique secret" >&2; exit 1;; esac

mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS 'atlas_app'@'%' IDENTIFIED BY '${ATLAS_APP_PASSWORD}';
GRANT SELECT ON atlas_db.reports TO 'atlas_app'@'%';
GRANT INSERT, UPDATE ON atlas_db.reports TO 'atlas_app'@'%';
GRANT SELECT ON atlas_db.market_metrics TO 'atlas_app'@'%';
GRANT SELECT (id, purchased_reports) ON atlas_db.clients TO 'atlas_app'@'%';
GRANT INSERT ON atlas_db.escalations TO 'atlas_app'@'%';
GRANT SELECT ON atlas_db.escalations TO 'atlas_app'@'%';
GRANT INSERT ON atlas_db.chat_logs TO 'atlas_app'@'%';
GRANT SELECT (id, client_id) ON atlas_db.chat_logs TO 'atlas_app'@'%';
GRANT UPDATE (feedback) ON atlas_db.chat_logs TO 'atlas_app'@'%';
GRANT INSERT ON atlas_db.security_audit TO 'atlas_app'@'%';

CREATE USER IF NOT EXISTS 'atlas_readonly'@'%' IDENTIFIED BY '${ATLAS_READONLY_PASSWORD}';
GRANT SELECT ON atlas_db.reports TO 'atlas_readonly'@'%';
GRANT SELECT ON atlas_db.market_metrics TO 'atlas_readonly'@'%';
FLUSH PRIVILEGES;
SQL
