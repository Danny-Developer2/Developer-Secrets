#!/bin/sh
# Puente de inicializacion: aplica el seed mountado en /seed despues del
# esquema (el entrypoint de PostgreSQL ejecuta los archivos de
# /docker-entrypoint-initdb.d en orden; este script queda despues de 001__init.sql).
set -e

echo "[devcore-lab] Aplicando seed: /seed/002__seed.sql"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /seed/002__seed.sql
echo "[devcore-lab] Seed aplicado correctamente."
