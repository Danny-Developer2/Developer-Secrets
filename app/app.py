"""DevCore Solutions - DCPM web (aplicacion vulnerable de laboratorio).

Todos los datos son ficticios. Esta aplicacion forma parte de un laboratorio
de entrenamiento en ciberseguridad y contiene configuraciones inseguras
deliberadas (ver docs/attack-path.md).
"""

import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("APP_SECRET", "devcore-fictitious-secret")

# ---------------------------------------------------------------
# Datos ficticios de la empresa
# ---------------------------------------------------------------
TEAM = [
    {
        "name": "Sofia Ostermann",
        "handle": "s.ostermann",
        "role": "Lead Backend",
        "email": "s.ostermann@devcore.example",
    },
    {
        "name": "Marco Retana",
        "handle": "m.retana",
        "role": "Frontend",
        "email": "m.retana@devcore.example",
    },
    {
        "name": "Diego Fuentes",
        "handle": "d.fuentes",
        "role": "DBA",
        "email": "d.fuentes@devcore.example",
    },
    {
        "name": "Ana Beltran",
        "handle": "a.beltran",
        "role": "DevOps",
        "email": "a.beltran@devcore.example",
    },
]

CLIENTES = ["Grupo Meridian", "Norte Logistica", "Kubo Retail", "Andino Salud"]

PROJECTS = [
    ("DCPM", "Plataforma de gestion de proyectos", "en produccion"),
    ("Meridian ERP", "Integracion contable", "piloto"),
    ("Kubo Storefront", "Tienda en linea", "desarrollo"),
    ("Andino Portal", "Portal de pacientes", "mantenimiento"),
]


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "devcore-web", "version": "2.4.1"})


@app.get("/")
def index():
    return render_template("index.html", projects=PROJECTS, clients=CLIENTES)


@app.get("/about")
def about():
    return render_template("about.html")


@app.get("/team")
def team():
    return render_template("team.html", team=TEAM)


@app.get("/status")
def status():
    return render_template("status.html")


# ---------------------------------------------------------------
# Ruta administrativa ficticia (senuelo)
# ---------------------------------------------------------------
DECOY_ADMIN_USER = "admin"
DECOY_ADMIN_PASS = "DevCore2024!"


@app.get("/admin/")
def admin_login_form():
    return render_template("admin.html")


@app.get("/admin/login")
def admin_login_form_alt():
    # Ruta alternativa que el borde no bloquea (el bloqueo es solo para /admin/)
    return render_template("admin.html")


@app.post("/admin/login")
def admin_login():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    # Laboratorio: credenciales senuelo, ficticias y sin acceso real.
    if username == DECOY_ADMIN_USER and password == DECOY_ADMIN_PASS:
        return render_template("maintenance.html", username=username)
    return render_template("admin.html", error="Credenciales invalidas"), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
