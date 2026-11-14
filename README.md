# Developer Secrets — Docker Hacking Lab

Laboratorio de entrenamiento en ciberseguridad: una maquina vulnerable, deliberadamente
insegura, inspirada en el funcionamiento de Hack The Box / TryHackMe.

Simula **DevCore Solutions**, una empresa ficticia que desarrollo la plataforma **DCPM**.
El participante debe reconstruir la cadena de exposicion, desde el reconocimiento hasta
la comprometer la base de datos, y obtener **6 flags progresivas**.

> **ADVERTENCIA**
> Este laboratorio contiene vulnerabilidades reales (SQL injection, directory listing,
> fugas de configuracion, control de acceso roto). Unicamente para entrenamiento en un
> entorno aislado y autorizado. Todos los datos, personas, correos, credenciales y
> secretos son **ficticios**.

---

## Arranque rapido

```bash
cd /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets
docker compose up -d --build
```

Despues abre **http://localhost:8080**.

```bash
./scripts/start.sh     # build + up + verificacion
./scripts/stop.sh      # detener (conserva los volumenes)
./scripts/reset.sh     # reinicio completo y reversible
./scripts/healthcheck.sh
./scripts/test.sh      # pruebas unitarias, integracion y seguridad
```

## Requisitos

- Docker Desktop con Docker Compose v2 (`docker compose version`).
- Ningun otro servicio en el puerto **8080** del host.
- Sin acceso a Internet desde los contenedores vulnerables (asi es por diseno).
- Por defecto el puerto se publica solo en `127.0.0.1`. Para exponerlo en la red
  local: `LAB_BIND_ADDRESS=0.0.0.0 docker compose up -d`.

## Servicios

| Servicio | Contenedor | Rol | Publicado |
|---|---|---|---|
| nginx | `ds-nginx` | Borde, directory listing, fugas de headers | `8080 -> 80` |
| web | `ds-web` | Portal DCPM (Flask) | no |
| api | `ds-api` | API interna (Flask) con SQLi de laboratorio | no |
| db | `ds-db` | PostgreSQL 16 con datos ficticios | no |
| flags | `ds-flags` | Validacion de flags y progreso (red interna) | no |

Redes:

- `developer-secrets_ds-lab-net` — `internal: true`. Sin Internet y sin DNS externo.
  Viven `web`, `api`, `db`, `flags`.
- `developer-secrets_ds-edge-net` — solo `nginx`, para poder publicar el puerto.

## Niveles y flags

| Nivel | Nombre | Flag | Puntos |
|---|---|---|---|
| 1 | Reconocimiento | `FLAG{RECON_COMPLETE}` | 10 |
| 2 | Enumeracion de directorios | `FLAG{DIRECTORY_DISCOVERED}` | 20 |
| 3 | Exposicion de informacion de desarrolladores | `FLAG{DEVELOPER_EXPOSED}` | 20 |
| 4 | Descubrimiento de secretos | `FLAG{SECRET_FOUND}` | 30 |
| 5 | Investigacion de base de datos | `FLAG{DATABASE_COMPROMISED}` | 40 |
| 6 | Root / flag final | `FLAG{DEVELOPER_SECRETS_ROOT}` | 50 |

**Las flags no estan en el codigo servido ni en los archivos descargables.** Se almacenan
en el contenedor `flags` (red interna, sin puertos publicos) y se entregan al demostrar
el hallazgo de cada nivel. El participante las valida y registra su progreso con:

```bash
curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{...}"}'

curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' -d '{"level":1,"evidence":"<evidencia>"}'

curl -s http://localhost:8080/api/flags/progress
```

> Este repositorio es material del **administrador**. No lo compartas con los participantes.

## Estructura

```
Developer-Secrets/
├── docker-compose.yml
├── .env.example
├── docs/                 # requirements, architecture, attack-path, admin, hints, solutions
├── app/                  # portal web (Flask)
├── api/                  # API interna (Flask) - SQLi de laboratorio
├── database/             # migrations/ y seed/ (datos ficticios)
├── nginx/                # configuracion del borde (insegura a proposito)
├── vulnerable-files/     # archivos expuestos que se sirven en /files
├── flags/                # servicio interno de flags + flags.json (admin)
├── scripts/              # start, stop, reset, healthcheck, test
├── tests/                # unit, integration, security
└── reports/              # reportes de QA y seguridad
```

## Aislamiento

- Los contenedores vulnerables no tienen egress a Internet (red `internal: true`).
- Solo `nginx` publica puerto; `db` y `flags` no son alcanzables desde el host.
- No se usa el socket de Docker del host.
- Los unicos bind mounts son del propio proyecto.
- No se ejecutan limpiezas globales de Docker; el proyecto es reversible con
  `./scripts/reset.sh`.

Ver `docs/administrator-guide.md` y `docs/architecture.md`.

## Licencia

Material educativo. Uso bajo tu responsabilidad, en entornos controlados.
