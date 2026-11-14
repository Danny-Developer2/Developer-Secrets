"""Logica pura del sistema de flags (sin dependencias de Flask).

Se separa del servidor para poder probarla de forma unitaria y para que el
modulo no arranque la base de datos al importarse.
"""

import json
import os
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("FLAGS_CONFIG", "/app/flags.json"))


def load_config(path=None):
    with open(path or CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_flag(value):
    return ("" if value is None else str(value)).strip()


def normalize_evidence(value):
    return normalize_flag(value).lower()


def find_flag(cfg, flag):
    """Devuelve (nivel, puntos) si la flag es valida; si no, (None, 0)."""
    target = normalize_flag(flag)
    if not target:
        return None, 0
    for level, value in cfg.get("flags", {}).items():
        if normalize_flag(value) == target:
            return str(level), int(cfg.get("points", {}).get(str(level), 0))
    return None, 0


def check_evidence(cfg, level, evidence):
    """Valida la evidencia de un nivel (1-4)."""
    expected = cfg.get("evidence", {}).get(str(level))
    if not expected or isinstance(evidence, (list, dict)):
        return False
    return normalize_evidence(evidence) == normalize_evidence(expected)


def check_final_combo(cfg, flags):
    """Nivel 6: exige las cinco flags anteriores, en orden."""
    if not isinstance(flags, list) or len(flags) != 5:
        return False
    expected = [normalize_flag(cfg["flags"][str(level)]) for level in range(1, 6)]
    provided = [normalize_flag(value) for value in flags]
    return provided == expected
