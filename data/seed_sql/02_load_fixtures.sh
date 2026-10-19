#!/bin/sh
set -eu

if [ "${LOAD_ASSIGNMENT_FIXTURES:-false}" = "true" ]; then
    mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" atlas_db < /opt/atlas/02_seed.sql
else
    echo "Assignment fixture data not loaded (LOAD_ASSIGNMENT_FIXTURES is not true)."
fi
