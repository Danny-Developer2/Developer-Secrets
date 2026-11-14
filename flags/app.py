"""Servicio interno de flags del laboratorio DevCore.

NO publica puertos: solo es accesible desde la red interna ds-lab-net.
Almacena las flags y las evidencias que las desbloquean, y mantiene el
registro de progreso en SQLite (volumen ds_flagsdata).
"""

import os
import sqlite3
import threading
from pathlib import Path

from flask import Flask, jsonify, request

from logic import (
    check_evidence,
    check_final_combo,
    find_flag,
    load_config,
    normalize_flag,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("FLAGS_DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "progress.db"

app = Flask(__name__)
_lock = threading.Lock()


# ---------------------------------------------------------------
# Persistencia del progreso
# ---------------------------------------------------------------
def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            level    TEXT PRIMARY KEY,
            flag     TEXT NOT NULL,
            points   INTEGER NOT NULL,
            solved_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def record_progress(level, flag, points):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO progress (level, flag, points) VALUES (?, ?, ?)",
            (str(level), flag, int(points)),
        )
        conn.commit()
        conn.close()


def read_progress():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT level, flag, points, solved_at FROM progress "
        "ORDER BY CAST(level AS INTEGER)"
    ).fetchall()
    conn.close()
    return rows


def clear_progress():
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM progress")
        conn.commit()
        conn.close()


# ---------------------------------------------------------------
# Endpoints internos
# ---------------------------------------------------------------
@app.get("/internal/health")
def health():
    return jsonify({"status": "ok", "service": "devcore-flags"})


@app.post("/internal/validate")
def validate():
    data = request.get_json(force=True, silent=True) or {}
    cfg = load_config()
    level, points = find_flag(cfg, data.get("flag", ""))
    if level is None:
        return jsonify({"valid": False, "message": "flag invalida"}), 404
    record_progress(level, normalize_flag(data.get("flag")), points)
    return jsonify(
        {
            "valid": True,
            "level": int(level),
            "points": points,
            "message": f"flag valida del nivel {level}",
        }
    )


@app.post("/internal/unlock")
def unlock():
    data = request.get_json(force=True, silent=True) or {}
    cfg = load_config()

    try:
        level = int(data.get("level"))
    except (TypeError, ValueError):
        return jsonify({"error": "nivel invalido"}), 400

    if level == 6:
        if not check_final_combo(cfg, data.get("flags")):
            return (
                jsonify(
                    {
                        "error": "combinacion invalida",
                        "message": "se requieren las cinco flags anteriores en orden",
                    }
                ),
                403,
            )
    else:
        if not check_evidence(cfg, level, data.get("evidence")):
            return jsonify({"error": "evidencia incorrecta para este nivel"}), 403

    flag = normalize_flag(cfg["flags"][str(level)])
    points = int(cfg.get("points", {}).get(str(level), 0))
    record_progress(level, flag, points)
    return jsonify(
        {
            "level": level,
            "flag": flag,
            "points": points,
            "message": f"nivel {level} desbloqueado",
        }
    )


@app.get("/internal/progress")
def progress():
    rows = read_progress()
    solved = [int(r[0]) for r in rows]
    return jsonify(
        {
            "solved": solved,
            "score": sum(int(r[2]) for r in rows),
            "total_levels": len(load_config().get("flags", {})),
            "detail": [
                {"level": int(r[0]), "points": int(r[2]), "solved_at": r[3] if len(r) > 3 else None}
                for r in rows
            ],
        }
    )


@app.post("/internal/reset")
def reset():
    clear_progress()
    return jsonify({"status": "ok", "message": "progreso reiniciado"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
