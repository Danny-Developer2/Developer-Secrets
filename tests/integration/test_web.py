"""Pruebas de integracion del portal web y de los archivos expuestos."""

import re

import requests

TIMEOUT = 10


def _get(base, path, **kwargs):
    return requests.get(f"{base}{path}", timeout=TIMEOUT, **kwargs)


def test_portal_responde(base_url):
    resp = _get(base_url, "/")
    assert resp.status_code == 200
    assert "DevCore" in resp.text


def test_paginas_publicas(base_url):
    for path in ["/about", "/team", "/status"]:
        resp = _get(base_url, path)
        assert resp.status_code == 200, path


def test_comentarios_de_desarrollador_en_el_html(base_url):
    resp = _get(base_url, "/")
    assert "s.ostermann" in resp.text
    assert "X-DevCore-Build" in resp.text


def test_admin_bloqueado_en_el_borde(base_url):
    resp = _get(base_url, "/admin/")
    assert resp.status_code == 403


def test_ruta_admin_parcialmente_bloqueada(base_url):
    """El borde solo bloquea /admin/ exacto: /admin/login pasa al portal."""
    resp = _get(base_url, "/admin/login")
    assert resp.status_code == 200
    assert "Acceso administrativo" in resp.text


def test_login_admin_senuelo(base_url):
    resp = requests.post(
        f"{base_url}/admin/login",
        data={"username": "admin", "password": "DevCore2024!"},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert "Mantenimiento" in resp.text


def test_robots_txt(base_url):
    resp = _get(base_url, "/robots.txt")
    assert resp.status_code == 200
    assert "Disallow: /admin/" in resp.text
    assert "Sitemap:" in resp.text


def test_sitemap_xml(base_url):
    resp = _get(base_url, "/sitemap.xml")
    assert resp.status_code == 200
    assert "/files/" in resp.text


def test_directory_listing_files(base_url):
    resp = _get(base_url, "/files/")
    assert resp.status_code == 200
    assert "Index of" in resp.text or "autoindex" in resp.text.lower()
    assert "backups" in resp.text
    assert "internal" in resp.text
    assert "config" in resp.text


def test_directory_listing_backups(base_url):
    resp = _get(base_url, "/backup/")
    assert resp.status_code == 200
    assert "devcore_archive_20241031.tar.gz" in resp.text


def test_evidencia_nivel_2_alcanzable(base_url):
    resp = _get(base_url, "/backup/devcore_archive_20241031.tar.gz")
    assert resp.status_code == 200
    assert resp.content[:2] == b"\x1f\x8b"  # gzip


def test_evidencia_nivel_3_alcanzable(base_url):
    resp = _get(base_url, "/files/internal/README-dev.md")
    assert resp.status_code == 200
    assert "s.ostermann" in resp.text


def test_evidencia_nivel_4_alcanzable_en_raiz(base_url):
    resp = _get(base_url, "/.env")
    assert resp.status_code == 200
    assert "DEVCORE_API_KEY=dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b" in resp.text


def test_evidencia_nivel_4_en_archivo_respaldo(base_url):
    resp = _get(base_url, "/files/config/.env.bak")
    assert resp.status_code == 200
    assert "dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b" in resp.text


def test_server_status_expone_metricas(base_url):
    resp = _get(base_url, "/server-status")
    assert resp.status_code == 200
    assert re.search(r"Active connections", resp.text)


def test_fuga_de_version_nginx(base_url):
    resp = _get(base_url, "/robots.txt")
    assert "nginx" in resp.headers.get("Server", "")
