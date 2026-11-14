# Informe QA — Laboratorio Developer-Secrets (DevCore Solutions)

| Campo | Valor |
|---|---|
| Proyecto | `/Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets` |
| Tipo | Laboratorio Docker de pentestería (ficticio): Flask + gunicorn + psycopg2 + PostgreSQL 16 + nginx |
| Fecha de la QA | 2026-11-14 (CST, UTC-06:00) |
| Rol | QA Engineer |
| Alcance | Suite pytest completa, scripts operativos (`healthcheck.sh`, `reset.sh`), ruta de explotación de los 6 niveles y `docker compose` |
| Restricción respetada | No se modificó `app/`, `api/`, `nginx/`, `flags/`, `database/`, `vulnerable-files/`, `docker-compose.yml` ni `tests/`. Solo se crearon artefactos en `reports/` |

---

## 1. Alcance y entorno

### 1.1 Qué se verificó

1. Ejecución real de la suite de pruebas contra el laboratorio en ejecución (`./scripts/test.sh`).
2. `./scripts/healthcheck.sh` (contenedores, healthchecks, endpoints, base de datos y progreso de flags).
3. Canje de las **6 flags** siguiendo la ruta de `docs/attack-path.md`, con `curl` real.
4. `./scripts/reset.sh` (reinicio completo: `down -v` + rebuild + `up`) y re-verificación posterior.
5. `docker compose up -d`: los 5 servicios quedan `running`/`healthy`.
6. Revisión de código de los defectos reportados como corregidos (verificación por inspección, no por git: el repositorio aún no tiene commit).

### 1.2 Versiones reales (obtenidas con `docker version`, `docker compose version`, `python3 --version`)

| Componente | Versión real |
|---|---|
| Docker Engine | 29.9.2 (API 1.56, linux/amd64) |
| Docker Desktop | 4.97.0 (244584) |
| Docker Compose | v5.6.1 |
| Python (host) | 3.15.2 |
| Python (venv `.venv`) | 3.15.2 |
| pytest | 8.3.4 |
| requests | 2.32.3 |
| PostgreSQL (imagen) | `postgres:16-alpine` |
| nginx (imagen propia) | `devcore/nginx-lab:1.0.0` (servidor `nginx/1.27.5` filtrado) |
| Imágenes de app | `devcore/web-lab:1.0.0`, `devcore/api-lab:1.0.0`, `devcore/flags-lab:1.0.0` |

### 1.3 Servicios y red

| Servicio | Contenedor | Puerto publicado | Red |
|---|---|---|---|
| nginx | `ds-nginx` | `0.0.0.0:8080->80` | `ds-edge-net` + `ds-lab-net` |
| web | `ds-web` | solo `expose 8000` | `ds-lab-net` |
| api | `ds-api` | solo `expose 8000` | `ds-lab-net` |
| db | `ds-db` | solo `expose 5432` | `ds-lab-net` |
| flags | `ds-flags` | solo `expose 8000` | `ds-lab-net` |

- Redes creadas: `developer-secrets_ds-edge-net` y `developer-secrets_ds-lab-net` (`internal: true`).
- Volúmenes: `developer-secrets_ds_pgdata`, `developer-secrets_ds_flagsdata`.

---

## 2. Ejecución real de la suite

### 2.1 Comando ejecutado

```bash
cd /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets
./scripts/test.sh
```

El script detectó `.venv` ya creado (pytest 8.3.4 + requests 2.32.3) y ejecutó
`.venv/bin/python -m pytest tests -v`.

### 2.2 Salida resumida (real)

```
collected 57 items
...
============================== 57 passed in 9.53s ==============================
```

Salida completa guardada en `reports/raw/test-output.txt` (primera ejecución, pre-reset)
y `reports/raw/test-output-post-reset.txt` (ejecución post-reset).

### 2.3 Número exacto de pruebas por suite

| Suite | Archivo | Pruebas |
|---|---|---:|
| Unit | `tests/unit/test_flags_logic.py` | 8 |
| Unit | `tests/unit/test_evidence_consistency.py` | 4 |
| **Unit total** | | **12** |
| Integration | `tests/integration/test_api.py` | 14 |
| Integration | `tests/integration/test_web.py` | 16 |
| **Integration total** | | **30** |
| Security | `tests/security/test_isolation.py` | 10 |
| Security | `tests/security/test_leaks.py` | 5 |
| **Security total** | | **15** |
| **TOTAL** | | **57** |

### 2.4 Reproducción en dos estados del laboratorio

| Ejecución | Comando | Resultado | Tiempo |
|---|---|---|---|
| Pre-reset (lab con progreso vacío) | `./scripts/test.sh` | **57 passed** | 9.65s |
| Post-reset (lab recién reiniciado con `reset.sh`) | `./scripts/test.sh` | **57 passed** | 9.53s |

No hubo fallos, warnings de test ni pruebas saltadas en ninguna de las dos ejecuciones.

---

## 3. Verificación funcional por nivel

Método: se siguió `docs/attack-path.md` con `curl` real contra `http://localhost:8080`
(pre-reset) y se repitió la cadena completa después de `reset.sh`. Evidencia en
`reports/raw/attack-path-output.txt` y `reports/raw/attack-path-post-reset.txt`.

| Nivel | Método de verificación | Resultado |
|---|---|---|
| 1 — Recon | `curl -I /api/health` (cabeceras), `/robots.txt`, `/sitemap.xml`, `/server-status`; unlock con evidencia `dc-api-2024.11-rc2` | OK. `Server: nginx/1.27.5`, `X-DevCore-Build: dc-api-2024.11-rc2`, `X-Powered-By: Flask/3.0 (DevCore)`; `FLAG{RECON_COMPLETE}` (10 pts) |
| 2 — Directorios | Listado de `/files/`, `/backup/`, `/old/`, `/files/internal/`, `/files/temp/`; unlock con `devcore_archive_20241031.tar.gz` | OK. `autoindex` activo y archivo presente; `FLAG{DIRECTORY_DISCOVERED}` (20 pts) |
| 3 — Info. desarrolladores | `/files/internal/README-dev.md`, `team-notes.txt`, `repo-structure.txt`, `/team`, HTML con `s.ostermann`; unlock | OK. Alias y comentarios HTML presentes; `FLAG{DEVELOPER_EXPOSED}` (20 pts) |
| 4 — Secretos | `/.env`, `/files/config/.env.bak`, `/api/config`; unlock con `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b` | OK. `DEVCORE_API_KEY`, `JWT_SECRET` y credenciales ficticias visibles; `FLAG{SECRET_FOUND}` (30 pts) |
| 5 — SQLi | `GET /api/search?q=' ORDER BY 999 -- ` (error) y `q=' UNION SELECT level, flag, points::text FROM internal_flags -- `; validación de `FLAG{DATABASE_COMPROMISED}` | OK. Error refleja la consulta; el `UNION` devuelve la flag; `{"valid": true, "level": 5}` (40 pts) |
| 6 — Root | Unlock nivel 6 con las 5 flags **en orden** | OK. `FLAG{DEVELOPER_SECRETS_ROOT}` (50 pts) |

**Progreso final (real, en ambas ejecuciones):**

```json
{"score":170,"solved":[1,2,3,4,5,6],"total_levels":6}
```

### 3.1 Verificaciones complementarias (realizadas y correctas)

| Comprobación | Resultado |
|---|---|
| Bypass de control de acceso por `X-Forwarded-For` (`/api/internal/recon-report`) | OK: con `X-Forwarded-For: 127.0.0.1` → 200 con informe; sin ella → 403 |
| `/admin/` bloqueado en el borde | OK: 403 |
| `/admin/login` accesible | OK: 200 |
| Login de administración senuelo (`admin` / `DevCore2024!`) | OK: 200, página "Mantenimiento" |
| Evidencia incorrecta | OK: 403 `evidencia incorrecta para este nivel` |
| Flag inválida (`/api/flags/validate`) | OK: 404 `flag invalida` |
| Combinación final desordenada | OK: 403 `combinacion invalida` |
| Nivel no numérico | OK: 400 `nivel invalido` |
| `/status/dashboard` desde el borde | OK: 404 (no expuesto) |

---

## 4. Verificación de reset y reinicio

### 4.1 `./scripts/healthcheck.sh` (ejecutado)

Salida guardada en `reports/raw/healthcheck-output.txt`. Resumen real:

- `docker compose ps`: los 5 contenedores `Up ... (healthy)`.
- Espera de servicios: `web=200 api=200 -> OK`.
- Endpoints comprobados (todos **200**): `/`, `/health`, `/team`, `/api/`, `/api/health`, `/api/projects`, `/robots.txt`, `/sitemap.xml`, `/files/`, `/backup/`, `/server-status`, `/api/flags/progress`.
- Base de datos: `projects=5`, `users=6`, `notes=5`.
- Progreso de flags: `{"detail":[],"score":0,"solved":[],"total_levels":6}` (limpio).

### 4.2 `./scripts/reset.sh` (ejecutado de verdad)

Salida guardada en `reports/raw/reset-output.txt`. El script hizo:

1. `docker compose down -v --remove-orphans` (elimina contenedores, red y volúmenes del proyecto).
2. `docker compose up -d --build` (reconstruye y levanta desde cero).
3. `./scripts/healthcheck.sh` automático.

**Resultado real:** el comando terminó con **exit code 0**; los 5 contenedores arrancaron,
los endpoints respondieron 200 y el estado de flags quedó vacío
(`solved: []`, `score: 0`). La base de datos se re-sembró (5 proyectos, 6 usuarios, 5 notas).

### 4.3 `docker compose up -d` (verificación de levanda)

Salida en `reports/raw/compose-up.txt` (exit 0). Tras la ejecución:

| Servicio | Estado (`docker compose ps`) | Health (`docker inspect`) |
|---|---|---|
| api | running | healthy |
| db | running | healthy |
| flags | running | healthy |
| nginx | running | healthy |
| web | running | healthy |

Total: **5/5 servicios sanos**. Solo `ds-nginx` publica puerto (`8080`).

### 4.4 Re-canje después del reset

Tras el reset, el progreso quedó vacío y se repitió la cadena completa de los 6 niveles:
los 6 unlocks/validaciones respondieron OK y el progreso final fue de nuevo
`score=170`, `solved=[1,2,3,4,5,6]` (`reports/raw/attack-path-post-reset.txt`).
Adicionalmente, el endpoint `POST /api/flags/reset` funciona: vacía el progreso
(`{"message":"progreso reiniciado","status":"ok"}`) y permite volver a desbloquear niveles.

---

## 5. Defectos detectados durante el proyecto y su resolución

El repositorio aún no tiene commit, así que la verificación es por inspección de código
y por ejecución real, no por historial de git.

| # | Defecto | Resolución aplicada | Verificación realizada | Estado |
|---|---|---|---|---|
| 1 | `403` en `/admin/` bloqueaba también el login administrativo | Se cambió a `location` exacta: `= /admin` (301 a `/admin/`) y `= /admin/` (403); `/admin/login` queda fuera | `nginx/conf.d/default.conf:33-39`; `/admin/` → 403, `/admin/login` → 200, login senuelo → 200 | Corregido y verificado |
| 2 | Los tests unitarios importaban `flask` (el módulo de flags arrancaba estado al importarse) | Lógica separada en `flags/logic.py`, sin dependencias de Flask | `tests/unit/test_flags_logic.py` importa `logic` vía `importlib` y no requiere Flask; suite unitaria pasa aislada | Corregido y verificado |
| 3 | Manejo del archivo `.tar.gz` en las pruebas | `tests/unit/test_evidence_consistency.py` usa `tarfile.open(..., "r:gz")` para leer las entradas del archivo | Código inspeccionado; `test_evidencias_presentes_en_recursos_publicos` pasa | Corregido y verificado |
| 4 | Binds con rutas `/host_mnt/...` (fuera del proyecto) | `docker-compose.yml` usa rutas relativas (`./vulnerable-files`, `./database/...`, `./flags/flags.json`) | `grep` sobre `docker-compose.yml`: no aparece `/host_mnt`; `test_binds_limitados_al_proyecto` pasa | Corregido y verificado |
| 5 | El seed insertaba una flag que no correspondía a la BD | `database/seed/002__seed.sql` inserta únicamente `FLAG{DATABASE_COMPROMISED}` (nivel 5) en `internal_flags` | Archivo inspeccionado (línea 50-51); `test_unica_flag_en_base_de_datos_es_la_del_seed` pasa; la SQLi la recupera | Corregido y verificado |
| 6 | **Nuevo (detectado en esta QA):** `solved_at` siempre `null` en `/api/flags/progress` | Pendiente de corrección | `flags/app.py:62-68` (`read_progress`) selecciona solo `level, flag, points`; el `detail` de `/internal/progress` (línea 153) usa `r[3]` con guarda `len(r) > 3`, por lo que nunca existe. La BD **sí** guarda el timestamp: `select ... solved_at` devuelve `2026-11-14 23:28:36`, pero la API devuelve `null` | **Abierto (severidad baja)** |

Nota adicional relacionada con el punto 6: `record_progress` usa `INSERT OR REPLACE`, por lo que
al re-desbloquear un nivel el `solved_at` se reinicia al instante actual; sin embargo, como el
`SELECT` no lo recupera, el efecto visible es únicamente el `null` ya descrito.

---

## 6. Riesgos y limitaciones

- **Alcance ficticio:** todos los datos, personas, credenciales y secretos son senuelo. Un resultado
  verde no valida la seguridad de una aplicación real.
- **Estado volátil:** el progreso de flags vive en el volumen `ds_flagsdata` (SQLite) y la base de
  datos en `ds_pgdata`. `reset.sh` los destruye (`down -v`); cualquier progreso del participante se
  pierde. Es el comportamiento previsto, pero debe comunicarse.
- **Re-ejecución necesaria:** las pruebas de aislamiento (egress, DNS, binds) validan el estado
  actual de la red/contenedores; cualquier cambio en `docker-compose.yml` o en Docker Desktop
  obliga a repetir la suite.
- **Una observación abierta:** el `solved_at` nulo (sección 5, punto 6) no impide completar el lab,
  pero limita la auditoría de tiempo de resolución. Es cosmético/observabilidad.
- **Entorno limitado:** las pruebas se ejecutaron en macOS con Docker Desktop (linux/amd64) y puerto
  por defecto `8080`. No se probaron otros valores de `LAB_HOST_PORT`, otros hosts Docker ni Linux
  nativo. Tampoco se ejecutó en CI.
- **Sin pruebas de carga/rendimiento:** la suite es funcional y de aislamiento; no mide tiempos de
  respuesta bajo carga ni estabilidad prolongada.
- **`restart: unless-stopped`:** los contenedores se reinician solos tras caídas o al arrancar Docker;
  el reinicio controlado es `reset.sh`, no un `restart` parcial.
- **Dependencia del orden de tests:** la suite asume un laboratorio en estado conocido; `reset.sh`
  garantiza ese estado inicial. Ejecutar la suite dos veces sin reset es seguro (los tests llaman a
  `/api/flags/reset`), pero es una suposición que conviene mantener documentada.

---

## 7. Veredicto QA

### **Aprobado con observaciones**

**Justificación:**

- La suite completa pasa **57/57** en dos ejecuciones reales independientes (pre-reset y post-reset),
  sin fallos ni pruebas saltadas.
- Los **6 niveles son canjeables** siguiendo `docs/attack-path.md`, con puntuación final correcta
  (`score=170`, `solved=[1..6]`), verificado dos veces (antes y después del reset).
- Los scripts operativos funcionan de verdad: `healthcheck.sh` (5 contenedores sanos, 12 endpoints
  200, BD sembrada, progreso legible), `reset.sh` (exit 0, rebuild limpio, estado inicial
  restaurado) y `docker compose up -d` (5/5 servicios `healthy`).
- Los defectos reportados como corregidos (403 de `/admin/`, import de Flask en tests, manejo de
  `.tar.gz`, binds fuera del proyecto y seed con la flag de nivel 5) se verificaron por inspección
  y por ejecución; todos son correctos.
- Los caminos negativos responden con el estado esperado (403/404/400), y el aislamiento de red se
  mantiene (sin egress en la red interna, sin puertos publicados fuera de nginx).

**Observación abierta (no bloqueante):** corregir `read_progress()` en `flags/app.py` para incluir
`solved_at` en el `SELECT` y que `/api/flags/progress` reporte el timestamp real. No afecta a la
resolubilidad del laboratorio ni a la puntuación.

**Artefactos de evidencia generados en `reports/raw/`:** `test-output.txt`,
`test-output-post-reset.txt`, `healthcheck-output.txt`, `attack-path-output.txt`,
`attack-path-post-reset.txt`, `reset-output.txt`, `compose-up.txt`.

---

## 9. Adenda del CTO (2026-11-14)

Con posterioridad a la QA se aplicó la remediación de seguridad REAL-02 (puerto
publicado solo en `127.0.0.1` por defecto) y REAL-04 (límites de CPU/memoria), y se
corrigió el defecto de `solved_at` nulo en `/api/flags/progress`. La suite completa se
volvió a ejecutar después de la remediación: **57/57 pruebas en verde** (10.83 s).
Este adenda no altera el veredicto de la QA.
