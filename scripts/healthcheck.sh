#!/usr/bin/env bash
# Verifica el estado del laboratorio: contenedores, healthchecks e endpoints.
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${LAB_HOST_PORT:-8080}"
BASE="http://localhost:${PORT}"

echo "[healthcheck] Contenedores:"
docker compose ps

echo
echo "[healthcheck] Esperando que los servicios respondan (max 60s)..."
for i in $(seq 1 30); do
    web="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${BASE}/health" || true)"
    api="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${BASE}/api/health" || true)"
    if [ "${web}" = "200" ] && [ "${api}" = "200" ]; then
        echo "  web=${web} api=${api} -> OK"
        break
    fi
    sleep 2
done

echo
echo "[healthcheck] Endpoints:"
check() {
    local path="$1"
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${BASE}${path}" || echo "000")"
    printf "  %-28s %s\n" "${path}" "${code}"
}

check "/"
check "/health"
check "/team"
check "/api/"
check "/api/health"
check "/api/projects"
check "/robots.txt"
check "/sitemap.xml"
check "/files/"
check "/backup/"
check "/server-status"
check "/api/flags/progress"

echo
echo "[healthcheck] Base de datos:"
docker compose exec -T db psql -U "${POSTGRES_USER:-devcore}" -d "${POSTGRES_DB:-devcore}" \
    -c "SELECT count(*) AS proyectos FROM projects;" \
    -c "SELECT count(*) AS usuarios FROM users;" \
    -c "SELECT count(*) AS notas FROM notes;" || echo "  (no se pudo consultar la base de datos)"

echo
echo "[healthcheck] Progreso de flags:"
curl -s --max-time 5 "${BASE}/api/flags/progress" || echo "  (sin respuesta)"
echo
