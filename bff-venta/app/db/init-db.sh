#!/bin/bash
set -e

echo "🔎 Creando base 'bffdb' si no existe..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_DB:-postgres}" \
  -tc "SELECT 1 FROM pg_database WHERE datname = 'bffdb'" | grep -q 1 || \
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_DB:-postgres}" \
  -c "CREATE DATABASE bffdb;"
