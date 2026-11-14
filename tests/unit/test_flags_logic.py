"""Pruebas unitarias de la logica del servicio de flags."""

import importlib
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "flags"))

# El modulo de logica no tiene dependencias de Flask: se puede probar aislado.
logic = importlib.import_module("logic")


def _cfg():
    return logic.load_config(REPO_ROOT / "flags" / "flags.json")


def test_config_carga_seis_niveles():
    cfg = _cfg()
    assert len(cfg["flags"]) == 6
    assert set(cfg["flags"]) == {"1", "2", "3", "4", "5", "6"}


def test_normalizar_flag_ignora_espacios():
    nivel, puntos = logic.find_flag(_cfg(), "  FLAG{RECON_COMPLETE}  ")
    assert nivel == "1"
    assert puntos == 10


def test_flag_invalida_no_resuelve_nada():
    nivel, puntos = logic.find_flag(_cfg(), "FLAG{NO_EXISTE}")
    assert nivel is None
    assert puntos == 0


def test_flag_vacia_no_resuelve_nada():
    assert logic.find_flag(_cfg(), "") == (None, 0)
    assert logic.find_flag(_cfg(), None) == (None, 0)


def test_evidencia_correcta_nivel_1():
    cfg = _cfg()
    assert logic.check_evidence(cfg, 1, "dc-api-2024.11-rc2") is True
    assert logic.check_evidence(cfg, 1, "DC-API-2024.11-RC2") is True


def test_evidencia_incorrecta():
    cfg = _cfg()
    assert logic.check_evidence(cfg, 3, "m.retana") is False
    assert logic.check_evidence(cfg, 3, ["s.ostermann"]) is False


def test_evidencia_nivel_sin_definir():
    cfg = _cfg()
    assert logic.check_evidence(cfg, 5, "lo-que-sea") is False


def test_combinacion_final_requiere_cinco_flags_en_orden():
    cfg = _cfg()
    flags = [cfg["flags"][str(nivel)] for nivel in range(1, 6)]
    assert logic.check_final_combo(cfg, flags) is True
    assert logic.check_final_combo(cfg, list(reversed(flags))) is False
    assert logic.check_final_combo(cfg, flags[:4]) is False
    assert logic.check_final_combo(cfg, "no-es-lista") is False
