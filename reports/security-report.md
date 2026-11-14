# Informe de auditoría de seguridad — Developer-Secrets (DevCore Solutions)

- **Proyecto:** Developer-Secrets (DevCore Solutions) — Docker Hacking Lab
- **Auditor:** Cybersecurity Engineer — Hermes Agent
- **Fecha:** 2026-11-14
- **Veredicto:** `aprobado_con_observaciones`
- **Modalidad:** solo lectura (inspección de configuración, redes, montajes y respuestas HTTP; sin ejecutar endpoints que modifican estado)
- **Datos ficticios verificado:** sí

---

## 1. Resumen ejecutivo

El laboratorio cumple los requisitos de aislamiento declarados: red interna sin egress, un único puerto publicado (nginx:8080), sin socket de Docker y binds limitados al proyecto. Las vulnerabilidades de la cadena de explotación (SQLi, directory listing, fugas de `.env`, XFF, credenciales señuelo) están presentes y son explotables, pero son **intencionadas por diseño** y están contenidas por el aislamiento de red, no por las aplicaciones.

Además de las vulnerabilidades didácticas, la auditoría encontró **hallazgos reales del laboratorio como contenedor**: servicios corriendo como `root`, puerto publicado en `0.0.0.0` (IPv4 e IPv6), cabeceras de seguridad ausentes, sin límites de recursos e imágenes no fijadas por digest. Todos son de severidad media/baja/informativa.

No se declaró nada que no se comprobara con un comando o con la inspección del código. Los endpoints que modifican estado (`/api/flags/validate`, `/unlock`, `/reset`) **no se ejecutaron**.

---

## 2. Tabla de hallazgos

### 2.1 Vulnerabilidades intencionadas (parte del diseño)

| ID | Hallazgo | Severidad | Estado | Evidencia resumida |
|---|---|---|---|---|
| INT-01 | SQL injection union-based en `/api/search` | alta | aceptado | `UNION SELECT id, username, role FROM users` y `UNION SELECT level, flag, points::text FROM internal_flags` devuelven datos; se obtuvo `FLAG{DATABASE_COMPROMISED}` |
| INT-02 | `/.env` y `/files/config/.env.bak` servidos | alta | aceptado | `GET /.env` → 200 con `APP_SECRET`, `DEVCORE_API_KEY`, `JWT_SECRET`, `DB_PASSWORD` |
| INT-03 | Confianza en `X-Forwarded-For` | alta | aceptado | sin header → 403; con `X-Forwarded-For: 127.0.0.1` → 200 con informe interno |
| INT-04 | `autoindex` y alias en `/files`, `/backup`, `/old`, `/files/config` | media | aceptado | listados con `backups/`, `config/`, `internal/`, `old/`, `temp/` |
| INT-05 | Backups/configuración descargables con secretos | media | aceptado | `tar -tzf devcore_archive_20241031.tar.gz`; `app-config.json` con claves |
| INT-06 | Información de desarrolladores | media | aceptado | `/files/internal/*`, `/api/users` (6 emails), comentario HTML en `/old/` |
| INT-07 | `server_tokens on` y `stub_status` | baja | aceptado | `Server: nginx/1.27.5`; `/server-status` con contadores |
| INT-08 | Credenciales administrativas señuelo | baja | aceptado | `POST /admin/login admin/DevCore2024!` → 200 |
| INT-09 | `/api/config` expone secretos | media | aceptado | 8 claves, `is_secret=true` en `DB_PASSWORD`, `DEVCORE_API_KEY`, `JWT_SECRET` |
| INT-10 | Endpoints de flags sin autenticación | media | aceptado | `/api/` lista `unlock`, `validate`, `reset`; verificados por código/documentación |

### 2.2 Hallazgos reales del laboratorio como contenedor

| ID | Hallazgo | Severidad | Estado | Evidencia resumida |
|---|---|---|---|---|
| REAL-01 | Servicios ejecutan como `root` (`uid=0`) | media | abierto | `/proc/1/status` → `Uid: 0 0 0 0` en web, api, flags y nginx |
| REAL-02 | Puerto 8080 publicado en `0.0.0.0` (IPv4 e IPv6) | media | abierto | `HostIp: 0.0.0.0` y `::` con `HostPort: 8080` |
| REAL-03 | Cabeceras de seguridad HTTP ausentes | baja | abierto | `curl -I` no devuelve `X-Content-Type-Options`, `X-Frame-Options`, CSP ni HSTS |
| REAL-04 | Sin límites de recursos (CPU/memoria) | baja | abierto | `docker-compose.yml` no define `deploy.resources` |
| REAL-05 | Imágenes por etiqueta, no por digest | informativa | abierto | `devcore/*:1.0.0`, `postgres:16-alpine` sin `@sha256` |

---

## 3. Verificación del aislamiento (comandos reales)

### 3.1 Red interna y egress

```
$ docker network inspect developer-secrets_ds-lab-net --format '{{.Internal}} {{.Name}}'
true developer-secrets_ds-lab-net
$ docker network inspect developer-secrets_ds-edge-net --format '{{.Internal}} {{.Name}}'
false developer-secrets_ds-edge-net
```

Las comprobaciones de egress dan **fallo** (esperado) en los contenedores vulnerables:

```
$ docker exec ds-web python -c "import socket; socket.gethostbyname('example.com')"
socket.gaierror: [Errno -3] Temporary failure in name resolution
$ docker exec ds-web python -c "import socket; s=socket.socket(); s.settimeout(4); s.connect(('1.1.1.1',80))"
OSError: [Errno 101] Network is unreachable
$ docker exec ds-api   (mismos tests)  → gaierror / Network is unreachable
$ docker exec ds-flags (mismos tests)  → gaierror / Network is unreachable
$ docker exec ds-db bash -c "timeout 4 bash -c 'echo > /dev/tcp/1.1.1.1/80'"
bash: /dev/tcp/1.1.1.1/80: Network unreachable
```

La DNS interna sí funciona (prueba de que la red interna está operativa):

```
$ docker exec ds-api python -c "import socket; print(socket.gethostbyname('db'))"
172.19.0.2
$ docker exec ds-api python -c "import socket; print(socket.gethostbyname('flags'))"
172.19.0.3
```

### 3.2 Publicación de puertos

```
$ for c in ds-nginx ds-web ds-api ds-db ds-flags; do docker inspect $c --format '{{json .NetworkSettings.Ports}}'; done
ds-nginx: {"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"8080"},{"HostIp":"::","HostPort":"8080"}]}
ds-web:   {"8000/tcp":null}
ds-api:   {"8000/tcp":null}
ds-db:    {"5432/tcp":null}
ds-flags: {"8000/tcp":null}

$ docker compose ps
ds-nginx  Up (healthy)  0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
ds-web    Up (healthy)  8000/tcp
ds-api    Up (healthy)  8000/tcp
ds-db     Up (healthy)  5432/tcp
ds-flags  Up (healthy)  8000/tcp
```

Solo `ds-nginx` publica puerto; `db` y `flags` no son alcanzables desde el host.

### 3.3 Socket de Docker y bind mounts

```
$ docker ps -q | while read id; do docker inspect $id --format '{{.Name}} {{range .Mounts}}{{.Source}}{{end}}'; done | grep -i docker.sock
(sin salida)

$ for c in ds-nginx ds-web ds-api ds-db ds-flags; do docker inspect $c --format '{{.Name}}{{range .Mounts}} {{.Source}}{{end}}'; done
/ds-nginx /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets/vulnerable-files
/ds-web
/ds-api
/ds-db /host_mnt/Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets/database/migrations /host_mnt/Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets/database/seed /var/lib/docker/volumes/developer-secrets_ds_pgdata/_data
/ds-flags /var/lib/docker/volumes/developer-secrets_ds_flagsdata/_data /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets/flags/flags.json
```

No se monta `/var/run/docker.sock`. Todos los binds están dentro del proyecto (el prefijo `/host_mnt` es el que reporta Docker Desktop en macOS). Los volúmenes nombrados pertenecen al proyecto (`developer-secrets_*`).

### 3.4 Contexto de la red del borde

`ds-nginx` está conectado a **ambas** redes (`ds-edge-net` y `ds-lab-net`), lo cual es necesario para proxyear a `web`/`api`. `ds-web`, `ds-api`, `ds-db` y `ds-flags` están solo en `ds-lab-net`. Este es el comportamiento previsto en `docker-compose.yml` y `docs/architecture.md` (ADR-004), y se registra como riesgo residual.

---

## 4. Alcance de las vulnerabilidades

- **Intencionadas (11):** SQLi, `server_tokens`, `stub_status`, `autoindex`/alias, `/.env`, backups, información de desarrolladores, `X-Forwarded-For`, credenciales señuelo, `/api/config`, endpoints de flags. Forman la cadena de los 6 niveles del laboratorio.
- **Reales del contenedor (5):** root, bind en `0.0.0.0`, cabeceras de seguridad, límites de recursos, fijado por digest.
- **Contención:** las vulnerabilidades se explotan sobre HTTP en `localhost:8080`; `web`, `api`, `db` y `flags` no son accesibles directamente desde el host ni desde Internet.
- **No probado:** `validate`/`unlock`/`reset` (modifican el progreso en SQLite) y escaneo de imágenes.

---

## 5. Datos ficticios

Se verificó que todos los datos son ficticios y están declarados como tales:

- `README.md` y `docker-compose.yml` incluyen avisos de "todos los datos, personas, correos, credenciales y secretos son ficticios".
- Los emails usan el dominio reservado `devcore.example` (`s.ostermann@devcore.example`, etc.).
- Los secretos son señuelo y están marcados: `.env.bak` ("entorno de produccion (FICTICIO)"), `app-config.json` ("Las llaves aqui son senuelo"), `team-notes.txt` ("ficticias").
- No se encontró ninguna persona real, correo real ni credencial real. Las 6 flags (`FLAG{RECON_COMPLETE}` … `FLAG{DEVELOPER_SECRETS_ROOT}`) se encuentran en `flags/flags.json`, material de administración.

---

## 6. Riesgos residuales

1. Las vulnerabilidades INT-01 a INT-10 son explotables; solo las contiene el aislamiento de red.
2. `ds-nginx`, en `ds-edge-net`, tiene ruta por defecto a Internet (consecuencia aceptada en ADR-004).
3. Todos los servicios vulnerables comparten la misma red plana `172.19.0.0/16`, sin segmentación entre ellos.
4. Las flags y los secretos señuelo viven en el repositorio (material de administración); una filtración revela las 6 flags.
5. El progreso de flags se registra en SQLite sin cifrar en el volumen `ds_flagsdata`.
6. No se ejecutaron los endpoints que modifican estado; su comportamiento se verificó por inspección del código y documentación.
7. El laboratorio se reinició de forma externa durante la auditoría; las comprobaciones de aislamiento se repitieron tras el reinicio y siguen siendo válidas.
8. Sin escaneo de vulnerabilidades de imagen ni pruebas de penetración completas.

---

## 7. Recomendaciones

1. Mantener el egress bloqueado (`internal: true`) y verificarlo tras cada reinicio.
2. Publicar `8080` solo en `127.0.0.1` si el uso es local.
3. Ejecutar los servicios con usuario no privilegiado y declarar límites de CPU/memoria.
4. Fijar las imágenes por digest y escanear las bases (Trivy/Grype).
5. Mantener las flags solo en el servicio `flags`, nunca en código servido ni archivos descargables.
6. Aislar y rotar los secretos señuelo; no reutilizarlos entre `.env.example`, compose, `/api/config` y archivos servidos.
7. Retirar del borde `/files`, `/backup`, `/old` y `/.env`; desactivar `autoindex` y `stub_status`; `server_tokens off`.
8. Parametrizar el SQL de `/api/search` y validar el origen real en `/api/internal/recon-report`.
9. Añadir cabeceras de seguridad HTTP y eliminar `X-DevCore-Build`/`X-Powered-By`.
10. Documentar el alcance ficticio para evitar confusiones con un entorno real.

---

## 8. Metodología y limitaciones

- Se inspeccionaron el repositorio (`docker-compose.yml`, `nginx/`, `app/`, `api/`, `flags/`, `vulnerable-files/`, `docs/`, `tests/`), el estado de Docker (`docker compose ps`, `docker inspect`, `docker network inspect`) y las respuestas HTTP de `http://localhost:8080`.
- Operaciones de red solo con `SELECT` (la SQLi usada fue de lectura). No se ejecutó ninguna operación que modificara estado.
- Limitaciones: sin escáner de imágenes, sin pruebas de pentesting completas, sin verificación de los endpoints de escritura de flags.

**Veredicto:** `aprobado_con_observaciones`.

---

## 9. Remediación posterior (CTO, 2026-11-14)

Tras la auditoría, el CTO aplicó las correcciones de mejor relación costo/beneficio
sobre los hallazgos reales:

| ID | Estado | Acción |
|---|---|---|
| REAL-02 | mitigado | `docker-compose.yml` publica el puerto en `127.0.0.1` por defecto (`LAB_BIND_ADDRESS`), con opción de exponerlo si el CO lo solicita. |
| REAL-04 | mitigado | Límites de CPU y memoria declarados en los cinco servicios. |
| REAL-01 | aceptado | Los contenedores corren como `root`. En un laboratorio aislado y desechable es una decisión aceptada: nginx requiere root para escuchar en el puerto 80 y el objetivo es reproducir un entorno vulnerable real. El riesgo queda contenido por la red `internal`. |
| REAL-03 | aceptado | No se añadieron cabeceras de seguridad: la ausencia de endurecimiento en el borde es parte del escenario didáctico (niveles 1 y 2). |
| REAL-05 | aceptado | Las imágenes no se fijan por digest porque se construyen localmente con `docker compose --build` y no se publican en un registro. |

Además, el defecto de QA sobre `solved_at` nulo en `/api/flags/progress` quedó corregido
en `flags/app.py` (la consulta ya incluye `solved_at`).

El veredicto de este informe corresponde al estado auditado; las mitigaciones
anteriores no lo modifican.
