#!/usr/bin/env bash
# Detiene los contenedores del laboratorio conservando volumenes y datos.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[devcore-lab] Deteniendo contenedores..."
docker compose stop

echo "[devcore-lab] Estado actual:"
docker compose ps
