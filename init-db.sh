#!/bin/bash
# File: init-db.sh
# Purpose: Create the test database alongside the main one on first Postgres start

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE fastapi_test_db;
EOSQL
