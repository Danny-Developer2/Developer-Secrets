"""Configuracion comun de las pruebas del laboratorio."""

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PROJECT = "developer-secrets"
INTERNAL_NETWORK = f"{COMPOSE_PROJECT}_ds-lab-net"
EDGE_NETWORK = f"{COMPOSE_PROJECT}_ds-edge-net"

CONTAINERS = {
    "nginx": "ds-nginx",
    "web": "ds-web",
    "api": "ds-api",
    "db": "ds-db",
    "flags": "ds-flags",
}


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("LAB_BASE_URL", "http://localhost:8080").rstrip("/")


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT
