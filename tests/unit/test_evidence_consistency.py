"""Verifica que el laboratorio sea resoluble: cada evidencia debe aparecer
en, al menos, un recurso publico (fuente o archivo servido)."""

import json
import re
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FUENTES = {
    "1": [
        REPO_ROOT / "docker-compose.yml",
        REPO_ROOT / ".env.example",
        REPO_ROOT / "api" / "app.py",
    ],
    "2": [
        REPO_ROOT / "vulnerable-files" / "backups" / "devcore_archive_20241031.tar.gz",
    ],
    "3": [
        REPO_ROOT / "vulnerable-files" / "internal" / "README-dev.md",
        REPO_ROOT / "vulnerable-files" / "internal" / "team-notes.txt",
        REPO_ROOT / "app" / "templates" / "team.html",
        REPO_ROOT / "app" / "templates" / "maintenance.html",
    ],
    "4": [
        REPO_ROOT / "vulnerable-files" / "config" / ".env.bak",
        REPO_ROOT / "vulnerable-files" / "config" / "app-config.json",
        REPO_ROOT / "database" / "seed" / "002__seed.sql",
    ],
}

FLAG_PATRON = re.compile(rb"FLAG\{[A-Z_]+\}")


def _cargar_config():
    with open(REPO_ROOT / "flags" / "flags.json", encoding="utf-8") as handle:
        return json.load(handle)


def _contenido(ruta):
    """Devuelve el texto de un recurso; para .gz, el texto de sus entradas."""
    if ruta.suffix == ".gz":
        with tarfile.open(ruta, "r:gz") as tar:
            return " ".join(
                tar.extractfile(m).read().decode("utf-8", "ignore")
                for m in tar.getmembers()
                if m.isfile()
            )
    return ruta.read_text(encoding="utf-8")


def test_evidencias_presentes_en_recursos_publicos():
    cfg = _cargar_config()
    for nivel, rutas in FUENTES.items():
        evidencia = cfg["evidence"][nivel]
        encontrada = False
        for ruta in rutas:
            if not ruta.exists():
                continue
            if evidencia in ruta.name or evidencia in _contenido(ruta):
                encontrada = True
        assert encontrada, f"evidencia del nivel {nivel} no encontrada: {evidencia}"


def test_las_seis_flags_estan_en_el_referencial_admin():
    cfg = _cargar_config()
    esperadas = {
        "FLAG{RECON_COMPLETE}",
        "FLAG{DIRECTORY_DISCOVERED}",
        "FLAG{DEVELOPER_EXPOSED}",
        "FLAG{SECRET_FOUND}",
        "FLAG{DATABASE_COMPROMISED}",
        "FLAG{DEVELOPER_SECRETS_ROOT}",
    }
    assert set(cfg["flags"].values()) == esperadas


def test_no_hay_flags_en_el_codigo_servido():
    """El codigo que se sirve (app, api, nginx) y los archivos descargables
    (vulnerable-files) no contienen flags."""
    directorios = ["app", "api", "nginx", "vulnerable-files"]
    fugas = []
    for nombre in directorios:
        for ruta in (REPO_ROOT / nombre).rglob("*"):
            if not ruta.is_file() or ruta.suffix == ".gz":
                continue
            if b"FLAG{" in ruta.read_bytes():
                fugas.append(str(ruta.relative_to(REPO_ROOT)))
    assert not fugas, f"flags en el codigo servido: {fugas}"


def test_unica_flag_en_base_de_datos_es_la_del_seed():
    """En database/ la unica flag debe ser la del nivel 5, en el seed.
    Las demas flags no viven en la base de datos."""
    halladas = {}
    for ruta in (REPO_ROOT / "database").rglob("*"):
        if not ruta.is_file():
            continue
        for coincidencia in FLAG_PATRON.findall(ruta.read_bytes()):
            halladas.setdefault(coincidencia.decode(), set()).add(
                str(ruta.relative_to(REPO_ROOT))
            )
    assert set(halladas) == {"FLAG{DATABASE_COMPROMISED}"}, halladas
    for rutas in halladas.values():
        assert all(r.startswith("database/seed/") for r in rutas), rutas
