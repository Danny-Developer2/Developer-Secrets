"""Pruebas antifuga: las flags no deben aparecer en los recursos que el
participante puede descargar desde la aplicacion."""

import subprocess
from pathlib import Path

import requests

from conftest import CONTAINERS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RUTAS_SERVIDAS = [
    "/",
    "/about",
    "/team",
    "/status",
    "/robots.txt",
    "/sitemap.xml",
    "/files/",
    "/backup/",
    "/old/",
    "/.env",
    "/files/config/.env.bak",
    "/files/config/app-config.json",
    "/files/config/database.yml.bak",
    "/files/internal/README-dev.md",
    "/files/internal/team-notes.txt",
    "/files/internal/repo-structure.txt",
    "/files/backups/db_backup_20241028.sql.bak",
    "/files/backups/nginx.conf.bak",
    "/files/temp/scratch_20241102.log",
    "/api/",
    "/api/health",
    "/api/projects",
    "/api/users",
    "/api/config",
    "/server-status",
]

DIRECTORIOS_SERVIDOS = ["app", "api", "nginx", "vulnerable-files"]


def test_recursos_servidos_no_contienen_flags(base_url):
    # Se reinicia el progreso para que /api/flags/progress no exponga flags.
    requests.post(f"{base_url}/api/flags/reset", json={}, timeout=10)

    fugas = []
    for ruta in RUTAS_SERVIDAS:
        resp = requests.get(f"{base_url}{ruta}", timeout=10)
        if "FLAG{" in resp.text:
            fugas.append(ruta)
    assert not fugas, f"flags visibles en: {fugas}"


def test_fuentes_servidas_no_contienen_flags():
    fugas = []
    for nombre in DIRECTORIOS_SERVIDOS:
        for ruta in (PROJECT_ROOT / nombre).rglob("*"):
            if not ruta.is_file() or ruta.suffix == ".gz":
                continue
            if b"FLAG{" in ruta.read_bytes():
                fugas.append(str(ruta.relative_to(PROJECT_ROOT)))
    assert not fugas, f"flags en el codigo servido: {fugas}"


def test_no_se_monta_el_socket_de_docker_en_el_compose():
    texto = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "docker.sock" not in texto


def test_el_compose_no_ejecuta_limpiezas_globales():
    prohibiciones = ["system prune", "volume prune", "image prune", "container prune", "network prune"]
    for script in (PROJECT_ROOT / "scripts").glob("*.sh"):
        # Solo se revisan lineas ejecutables, no comentarios documentales.
        lineas = [
            linea
            for linea in script.read_text(encoding="utf-8").splitlines()
            if linea.strip() and not linea.strip().startswith("#")
        ]
        for linea in lineas:
            for prohibida in prohibiciones:
                assert prohibida not in linea, f"{script.name}: {linea}"


def test_contenedores_usan_imagenes_propias_o_base():
    """Verifica que no se referencian imagenes de otros proyectos."""
    propias = {
        "devcore/nginx-lab:1.0.0",
        "devcore/web-lab:1.0.0",
        "devcore/api-lab:1.0.0",
        "devcore/flags-lab:1.0.0",
        "postgres:16-alpine",
    }
    for contenedor in CONTAINERS.values():
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.Config.Image}}", contenedor],
            capture_output=True,
            text=True,
            check=True,
        )
        imagen = proc.stdout.strip()
        assert imagen in propias, f"{contenedor} usa imagen ajena: {imagen}"
