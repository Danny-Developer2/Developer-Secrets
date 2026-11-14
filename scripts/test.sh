#!/usr/bin/env bash
# Ejecuta las pruebas del laboratorio (unitarias, integracion y seguridad).
# Crea un venv local (.venv) si no existe.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
    echo "[tests] Creando entorno virtual..."
    python3 -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -r tests/requirements.txt
fi

exec .venv/bin/python -m pytest tests -v "$@"
