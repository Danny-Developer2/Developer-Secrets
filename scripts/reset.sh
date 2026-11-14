#!/usr/bin/env bash
# Reinicio COMPLETO y reversible del laboratorio:
#   1. detiene y elimina los contenedores, redes y volumenes del proyecto
#   2. reconstruye las imagenes
#   3. vuelve a levantar todo desde cero
# Alcance: unicamente el proyecto "developer-secrets". No ejecuta limpiezas
# globales de Docker (nada de docker system prune ni eliminacion de volumenes
# de otros proyectos).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[devcore-lab] Reinicio completo del laboratorio..."
docker compose down -v --remove-orphans

echo "[devcore-lab] Reconstruyendo y levantando desde cero..."
docker compose up -d --build

./scripts/healthcheck.sh

echo
echo "[devcore-lab] Reinicio completo. Laboratorio disponible en http://localhost:${LAB_HOST_PORT:-8080}"
