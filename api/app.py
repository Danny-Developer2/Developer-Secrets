"""DevCore Solutions - API interna (DELIBERADAMENTE VULNERABLE).

Laboratorio de entrenamiento: contiene SQL injection en /api/search y una
confianza indebida en X-Forwarded-For en /api/internal/recon-report.
El resto de endpoints usan consultas parametrizadas a modo de contraste.

Todos los datos son ficticios.
"""

import os

import psycopg2
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

BUILD_TOKEN = os.environ.get("DEVCORE_BUILD_TOKEN", "dc-api-unknown")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://devcore:devcore_ficticio_2024@db:5432/devcore"
)
FLAGS_SERVICE_URL = os.environ.get("FLAGS_SERVICE_URL", "http://flags:8000")
HTTP_TIMEOUT = 5


# ---------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------
def get_conn():
    return psycopg2.connect(DATABASE_URL)


def fetch_all(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


@app.after_request
def add_headers(response):
    # Filtra el token de build del API (utilizado como evidencia del Nivel 1)
    response.headers["X-DevCore-Build"] = BUILD_TOKEN
    response.headers["X-Powered-By"] = "Flask/3.0 (DevCore)"
    response.headers["Server"] = "devcore-api"
    return response


# ---------------------------------------------------------------
# Informacion y endpoints "normales"
# ---------------------------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "devcore-api", "build": BUILD_TOKEN})


@app.get("/api/")
def api_root():
    return jsonify(
        {
            "service": "DevCore API",
            "version": "2.4.1",
            "build": BUILD_TOKEN,
            "endpoints": [
                "/api/health",
                "/api/projects",
                "/api/projects/{id}",
                "/api/users",
                "/api/search?q=",
                "/api/config",
                "/api/internal/recon-report",
                "/api/flags/validate",
                "/api/flags/unlock",
                "/api/flags/progress",
            ],
        }
    )


@app.get("/api/projects")
def projects():
    rows = fetch_all(
        "SELECT id, code, name, status, owner FROM projects ORDER BY id"
    )
    return jsonify(
        {
            "count": len(rows),
            "results": [
                {"id": r[0], "code": r[1], "name": r[2], "status": r[3], "owner": r[4]}
                for r in rows
            ],
        }
    )


@app.get("/api/projects/<int:project_id>")
def project_detail(project_id):
    # Contraste seguro: consulta parametrizada
    rows = fetch_all(
        "SELECT id, code, name, status, owner FROM projects WHERE id = %s",
        (project_id,),
    )
    if not rows:
        return jsonify({"error": "proyecto no encontrado"}), 404
    r = rows[0]
    return jsonify(
        {"id": r[0], "code": r[1], "name": r[2], "status": r[3], "owner": r[4]}
    )


@app.get("/api/users")
def users():
    rows = fetch_all(
        "SELECT id, username, full_name, email, role, department FROM users ORDER BY id"
    )
    return jsonify(
        {
            "count": len(rows),
            "results": [
                {
                    "id": r[0],
                    "username": r[1],
                    "full_name": r[2],
                    "email": r[3],
                    "role": r[4],
                    "department": r[5],
                }
                for r in rows
            ],
        }
    )


@app.get("/api/config")
def config():
    """Expone la tabla de configuracion interna (incluye secretos senuelo)."""
    rows = fetch_all("SELECT key, value, is_secret FROM app_config ORDER BY key")
    return jsonify(
        {
            "count": len(rows),
            "results": [{"key": r[0], "value": r[1], "is_secret": r[2]} for r in rows],
        }
    )


# ---------------------------------------------------------------
# VULNERABILIDAD: SQL injection (Nivel 5)
# ---------------------------------------------------------------
@app.get("/api/search")
def search():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "parametro 'q' requerido"}), 400

    sql = f"SELECT id, name, status FROM projects WHERE name LIKE '%{q}%'"
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql)  # VULNERABLE: concatenacion directa
        rows = cur.fetchall()
    except Exception as exc:  # nosec - laboratorio
        conn.rollback()
        return (
            jsonify(
                {
                    "error": "error de sintaxis en la consulta",
                    "detail": str(exc),
                    "query": sql,
                }
            ),
            500,
        )
    finally:
        conn.close()

    return jsonify(
        {
            "query": sql,
            "count": len(rows),
            "results": [{"id": r[0], "name": r[1], "status": r[2]} for r in rows],
        }
    )


# ---------------------------------------------------------------
# VULNERABILIDAD: control de acceso por X-Forwarded-For (Nivel 1)
# ---------------------------------------------------------------
@app.get("/api/internal/recon-report")
def recon_report():
    # VULNERABLE: confia en la cabecera X-Forwarded-For sin validar el origen
    forwarded = request.headers.get("X-Forwarded-For", "")
    peer = forwarded.split(",")[0].strip()
    if peer != "127.0.0.1":
        return jsonify({"error": "acceso interno denegado"}), 403
    return jsonify(
        {
            "internal": True,
            "build": BUILD_TOKEN,
            "servicios": ["web", "api", "db", "flags"],
            "rutas_internas": ["/api/internal/recon-report", "/api/config"],
            "nota": "informe generado para el equipo de seguridad de DevCore",
        }
    )


# ---------------------------------------------------------------
# Sistema de flags (proxied al servicio interno)
# ---------------------------------------------------------------
def _proxy(method, path, payload=None):
    try:
        resp = requests.request(
            method,
            f"{FLAGS_SERVICE_URL}{path}",
            json=payload,
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException:
        return (
            jsonify({"error": "servicio de flags no disponible", "detail": "internal"}),
            503,
        )
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}
    return jsonify(body), resp.status_code


@app.post("/api/flags/validate")
def validate_flag():
    data = request.get_json(force=True, silent=True) or {}
    return _proxy("POST", "/internal/validate", {"flag": data.get("flag", "")})


@app.post("/api/flags/unlock")
def unlock_flag():
    data = request.get_json(force=True, silent=True) or {}
    payload = {"level": data.get("level")}
    if "evidence" in data:
        payload["evidence"] = data.get("evidence")
    if "flags" in data:
        payload["flags"] = data.get("flags")
    return _proxy("POST", "/internal/unlock", payload)


@app.get("/api/flags/progress")
def flag_progress():
    return _proxy("GET", "/internal/progress")


@app.post("/api/flags/reset")
def flag_reset():
    return _proxy("POST", "/internal/reset")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
