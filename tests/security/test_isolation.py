"""Pruebas de aislamiento del laboratorio (red, publicacion de puertos,
montajes y egress). Requiere acceso a la CLI de Docker del host."""

import json
import subprocess
from pathlib import Path

from conftest import CONTAINERS, EDGE_NETWORK, INTERNAL_NETWORK

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def docker(*args, check=True):
    proc = subprocess.run(["docker", *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"docker {' '.join(args)} fallo: {proc.stderr.strip()}")
    return proc


def inspect_container(nombre):
    return json.loads(docker("inspect", nombre).stdout)[0]


def inspect_network(nombre):
    return json.loads(docker("network", "inspect", nombre).stdout)[0]


def redes_de(contenedor):
    return set(inspect_container(contenedor)["NetworkSettings"]["Networks"].keys())


# ---------------------------------------------------------------
# Redes
# ---------------------------------------------------------------
def test_red_interna_sin_egress():
    assert inspect_network(INTERNAL_NETWORK)["Internal"] is True


def test_red_del_borde_siene_egress():
    assert inspect_network(EDGE_NETWORK)["Internal"] is False


def test_solo_nginx_comparte_la_red_del_borde():
    for nombre, contenedor in CONTAINERS.items():
        redes = redes_de(contenedor)
        if nombre == "nginx":
            assert EDGE_NETWORK in redes
            assert INTERNAL_NETWORK in redes
        else:
            assert INTERNAL_NETWORK in redes, contenedor
            assert EDGE_NETWORK not in redes, contenedor


def test_contenedores_vulnerables_sin_dns_externa():
    for nombre in ["web", "api", "flags"]:
        proc = docker(
            "exec",
            CONTAINERS[nombre],
            "python",
            "-c",
            "import socket; socket.gethostbyname('example.com')",
            check=False,
        )
        assert proc.returncode != 0, f"{nombre} resolvio DNS externo"


def test_contenedores_vulnerables_sin_egress_a_internet():
    codigo = (
        "import socket; "
        "s = socket.socket(); s.settimeout(4); s.connect(('1.1.1.1', 80))"
    )
    for nombre in ["web", "api", "flags"]:
        proc = docker("exec", CONTAINERS[nombre], "python", "-c", codigo, check=False)
        assert proc.returncode != 0, f"{nombre} pudo conectar a 1.1.1.1:80"


def test_db_sin_egress_a_internet():
    proc = docker(
        "exec", CONTAINERS["db"], "bash", "-c",
        "timeout 4 bash -c 'echo > /dev/tcp/1.1.1.1/80'", check=False,
    )
    assert proc.returncode != 0, "la base de datos pudo conectar al exterior"


# ---------------------------------------------------------------
# Publicacion de puertos
# ---------------------------------------------------------------
def test_solo_nginx_publica_puertos():
    for nombre, contenedor in CONTAINERS.items():
        puertos = inspect_container(contenedor)["NetworkSettings"].get("Ports") or {}
        publicados = [p for p, v in puertos.items() if v]
        if nombre == "nginx":
            assert publicados, "nginx debe publicar el puerto 80"
        else:
            assert not publicados, f"{contenedor} no debe publicar puertos: {publicados}"


# ---------------------------------------------------------------
# Montajes
# ---------------------------------------------------------------
def test_sin_socket_de_docker():
    for nombre, contenedor in CONTAINERS.items():
        for mount in inspect_container(contenedor)["Mounts"]:
            assert mount.get("Source") != "/var/run/docker.sock", contenedor
            assert mount.get("Destination") != "/var/run/docker.sock", contenedor


def test_binds_limitados_al_proyecto():
    raiz = str(PROJECT_ROOT)
    for nombre, contenedor in CONTAINERS.items():
        for mount in inspect_container(contenedor)["Mounts"]:
            if mount.get("Type") != "bind":
                continue
            origen = mount.get("Source", "")
            # Docker Desktop reporta los binds del host con prefijo /host_mnt
            origen = origen.removeprefix("/host_mnt")
            assert origen.startswith(raiz), f"{contenedor} monta fuera del proyecto: {origen}"


def test_volumenes_nombrados_del_laboratorio():
    for nombre, contenedor in CONTAINERS.items():
        for mount in inspect_container(contenedor)["Mounts"]:
            if mount.get("Type") == "volume":
                assert mount.get("Name", "").startswith("developer-secrets_"), (
                    contenedor,
                    mount.get("Name"),
                )
