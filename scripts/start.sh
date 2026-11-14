#!/usr/bin/env bash
# Inicia el laboratorio DevCore (build + up) y espera a que este sano.
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${LAB_HOST_PORT:-8080}"

echo "[devcore-lab] Construyendo imagenes y levantando servicios..."
docker compose up -d --build

echo "[devcore-lab] Verificando estado de los servicios..."
./scripts/healthcheck.sh

echo
echo "[devcore-lab] Laboratorio listo."
echo "  URL:      http://localhost:${PORT}"
echo "  API:      http://localhost:${PORT}/api/"
echo "  Archivos: http://localhost:${PORT}/files/"
echo "  Progreso: curl -s http://localhost:${PORT}/api/flags/progress"
echo
echo "  Detener:  ./scripts/stop.sh"
echo "  Reiniciar: ./scripts/reset.sh"
