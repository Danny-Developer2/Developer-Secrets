# Developer Secrets — Docker Hacking Lab

Laboratorio de entrenamiento en ciberseguridad: una máquina **deliberadamente
vulnerable**, desplegable con un solo comando, inspirada en el funcionamiento de
Hack The Box / TryHackMe.

Simula **DevCore Solutions**, una empresa ficticia que desarrolló la plataforma **DCPM**.
El participante debe reconstruir la cadena de exposición —desde el reconocimiento hasta
comprometer la base de datos— y obtener **6 flags progresivas** (170 puntos).

> **ADVERTENCIA**
> Contiene vulnerabilidades reales (SQL injection, directory listing, fugas de
> configuración, control de acceso roto). Úsalo **solo** en un entorno aislado y
> autorizado. Todas las personas, empresas, correos, credenciales y secretos son
> **ficticios**. Este repositorio incluye las soluciones porque está pensado como
> material de administración: no lo compartas con los participantes.

---

## 1. Requisitos

| Componente | Detalle |
|---|---|
| Docker Desktop | con el daemon activo |
| Docker Compose | v2 (`docker compose version`) |
| Puerto | `8080` libre en el host |
| Utilidades | `curl` y `python3` (opcional, para las pruebas) |

No necesita Internet una vez construidas las imágenes: los contenedores vulnerables
**tienen el egress bloqueado por diseño**.

---

## 2. Instalación y uso

```bash
git clone https://github.com/Danny-Developer2/Developer-Secrets.git
cd Developer-Secrets
docker compose up -d --build
```

Abre **http://localhost:8080**.

Eso es todo. La base de datos se migra y se puebla sola, y los cinco servicios quedan
con healthcheck en verde.

### Scripts de operación

| Acción | Comando | Efecto |
|---|---|---|
| Iniciar / reconstruir | `./scripts/start.sh` | `up -d --build` + verificación |
| Detener | `./scripts/stop.sh` | `compose stop`; conserva los volúmenes |
| **Reinicio completo** | `./scripts/reset.sh` | `down -v` + `up -d --build` |
| Ver estado | `./scripts/healthcheck.sh` | contenedores, endpoints y base de datos |
| Pruebas | `./scripts/test.sh` | 57 pruebas (unit + integración + seguridad) |

`reset.sh` usa `docker compose down -v --remove-orphans`: afecta **únicamente** a este
proyecto. Nunca ejecuta limpiezas globales de Docker.

### Personalizar el puerto o la interfaz

```bash
LAB_HOST_PORT=8090 docker compose up -d        # otro puerto
LAB_BIND_ADDRESS=0.0.0.0 docker compose up -d  # exponer en la red local
```

Por defecto escucha solo en `127.0.0.1` para no dejar la máquina expuesta en la red.

---

## 3. Acceso

| Recurso | URL |
|---|---|
| Portal | http://localhost:8080 |
| API | http://localhost:8080/api/ |
| Archivos expuestos | http://localhost:8080/files/ |
| Copias de seguridad | http://localhost:8080/backup/ |
| Estado del borde | http://localhost:8080/server-status |
| Progreso de flags | `curl -s http://localhost:8080/api/flags/progress` |

---

## 4. Niveles y flags

| Nivel | Nombre | Flag | Puntos |
|---|---|---|---|
| 1 | Reconocimiento | `FLAG{RECON_COMPLETE}` | 10 |
| 2 | Enumeración de directorios | `FLAG{DIRECTORY_DISCOVERED}` | 20 |
| 3 | Exposición de información de desarrolladores | `FLAG{DEVELOPER_EXPOSED}` | 20 |
| 4 | Descubrimiento de secretos | `FLAG{SECRET_FOUND}` | 30 |
| 5 | Investigación de base de datos | `FLAG{DATABASE_COMPROMISED}` | 40 |
| 6 | Root / flag final | `FLAG{DEVELOPER_SECRETS_ROOT}` | 50 |

Las flags se almacenan **solo** en el contenedor interno `flags` (sin puertos publicados).
El participante las obtiene al demostrar el hallazgo de cada nivel, o al extraerla de la
base de datos mediante la SQLi del nivel 5.

### Sistema de flags

```bash
# Validar una flag
curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{...}"}'

# Desbloquear un nivel por evidencia (niveles 1-4)
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' -d '{"level":1,"evidence":"<evidencia>"}'

# Nivel final: requiere las cinco flags anteriores, en orden
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":6,"flags":["FLAG{...}","FLAG{...}","FLAG{...}","FLAG{...}","FLAG{...}"]}'

# Progreso y reinicio
curl -s http://localhost:8080/api/flags/progress
curl -s -X POST http://localhost:8080/api/flags/reset -H 'Content-Type: application/json' -d '{}'
```

---

## 5. Ruta de explotación (resumen)

```
recon (cabeceras, robots.txt, sitemap.xml, stub_status)
  → directory listing (/files, /backup, /old)
    → información de desarrolladores (/files/internal)
      → secretos señuelo (/.env, /files/config)
        → SQL injection en /api/search  →  base de datos
          → combinación final de las cinco flags
```

La ruta completa, con comandos y salida esperada, está en
[`docs/attack-path.md`](docs/attack-path.md). Las soluciones paso a paso, en
[`docs/solutions.md`](docs/solutions.md), y las pistas graduales en
[`docs/hints.md`](docs/hints.md).

---

## 6. Estructura del repositorio

```
Developer-Secrets/
├── docker-compose.yml
├── .env.example
├── docs/                 # requirements, architecture, attack-path, admin, hints, solutions
├── app/                  # portal web (Flask)
├── api/                  # API interna (Flask) — SQLi de laboratorio
├── database/             # migrations/ y seed/ (datos ficticios)
├── nginx/                # configuración del borde (insegura a propósito)
├── vulnerable-files/     # archivos expuestos que se sirven en /files
├── flags/                # servicio interno de flags + flags.json
├── scripts/              # start, stop, reset, healthcheck, test
├── tests/                # unit, integration, security
└── reports/              # informes de QA y de ciberseguridad
```

---

## 7. Arquitectura y aislamiento

Cinco servicios: `nginx` (borde), `web`, `api`, `db` (PostgreSQL 16) y `flags`.

| Servicio | Contenedor | ¿Publica puerto? |
|---|---|---|
| nginx | `ds-nginx` | sí, `127.0.0.1:8080 → 80` |
| web | `ds-web` | no |
| api | `ds-api` | no |
| db | `ds-db` | no |
| flags | `ds-flags` | no |

Dos redes:

- `developer-secrets_ds-lab-net` — `internal: true`. Sin Internet y sin DNS externo.
  Viven `web`, `api`, `db` y `flags`.
- `developer-secrets_ds-edge-net` — solo `nginx`, para poder publicar el puerto.

Verificación: desde los contenedores vulnerables falla la resolución DNS y cualquier
conexión saliente. No se monta el socket de Docker y los únicos *bind mounts* son del
propio proyecto. Detalle y justificación en [`docs/architecture.md`](docs/architecture.md).

---

## 8. Documentación

| Documento | Contenido |
|---|---|
| [`docs/requirements.md`](docs/requirements.md) | Requisitos, criterios de aceptación y trazabilidad |
| [`docs/architecture.md`](docs/architecture.md) | Decisiones de arquitectura (ADRs) |
| [`docs/attack-path.md`](docs/attack-path.md) | Ruta de explotación completa |
| [`docs/administrator-guide.md`](docs/administrator-guide.md) | Instalación, operación y solución de problemas |
| [`docs/hints.md`](docs/hints.md) | Pistas graduales para el participante |
| [`docs/solutions.md`](docs/solutions.md) | Solución completa (administración) |
| [`reports/qa-report.md`](reports/qa-report.md) | Informe de QA |
| [`reports/security-report.md`](reports/security-report.md) | Informe de ciberseguridad |

---

## 9. Resolución de problemas

- **`bind: address already in use`** → `LAB_HOST_PORT=8090 docker compose up -d`.
- **No responde ningún contenedor** → `docker compose logs <servicio>`; si la base de datos
  no se puebla, `./scripts/reset.sh`.
- **Las flags no validan** → `POST /api/flags/reset` y comprueba que `ds-flags` está sano.
- **No puedo acceder desde otro equipo** → es el comportamiento por defecto; usa
  `LAB_BIND_ADDRESS=0.0.0.0`.

Más detalle en [`docs/administrator-guide.md`](docs/administrator-guide.md).

---

## 10. Descargo de responsabilidad

Material educativo. Todas las personas, empresas, correos, credenciales, tokens y
secretos son ficticios y no sirven para autenticar en ningún servicio real. Úsalo solo
en entornos controlados y autorizados. El autor no se hace responsable del uso indebido.
