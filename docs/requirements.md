# Developer Secrets - Docker Hacking Lab
## Documento de requisitos y criterios de aceptación

| Campo | Valor |
|---|---|
| Proyecto | Developer Secrets - Docker Hacking Lab |
| Empresa simulada | DevCore Solutions (ficticia) |
| Plataforma simulada | DCPM (Plataforma de gestión de proyectos) |
| Rol de este documento | Business Analyst |
| Estado | Aprobado para verificación |
| Alcance | Laboratorio local, deliberadamente vulnerable, de un solo participante por ejecución |
| Confidencialidad | **Solo administración.** Contiene las 6 flags y las evidencias; no debe exponerse al participante ni servirse desde el laboratorio. |

---

## 1. Introducción y alcance

### 1.1 Propósito

El laboratorio **Developer Secrets - Docker Hacking Lab** reproduce, en un entorno controlado y reversible, una empresa ficticia (**DevCore Solutions**) que desarrolló la plataforma **DCPM**. Su objetivo es que un participante practique un ciclo completo de pentesting defensivo-ofensivo sobre una aplicación web y su API, desde el reconocimiento hasta la obtención de la flag final.

El laboratorio está expresamente diseñado para ser **vulnerable**: las debilidades no son accidentales, son el material de aprendizaje. Todas las personas, correos, credenciales, tokens, clientes, proyectos y secretos son **ficticios**.

### 1.2 Alcance incluido

- Despliegue local con Docker Compose de 5 servicios: `nginx` (borde), `web` (Flask), `api` (Flask), `db` (PostgreSQL 16) y `flags` (validador interno).
- 6 niveles progresivos de dificultad con flags y puntuación acumulativa (170 puntos en total).
- Sistema de validación y desbloqueo de flags con registro de progreso persistente.
- Pistas progresivas integradas en los propios recursos expuestos.
- Scripts de ciclo de vida: arranque, verificación de salud, detención y reinicio completo.
- Pruebas unitarias, de integración y de seguridad/aislamiento.
- Trazabilidad nivel → evidencia → flag → puntos.

### 1.3 Alcance no incluido

Ver la sección 7 (Fuera de alcance).

---

## 2. Actor / participante tipo

### 2.1 Participante

| Atributo | Descripción |
|---|---|
| Rol | Estudiante o profesional de ciberseguridad en etapa de práctica de pentesting web. |
| Conocimientos previos | Manejo básico de terminal, HTTP, `curl`, conceptos de red (puertos, DNS), SQL básico. |
| Herramientas típicas | Navegador con inspector de red, `curl`, `nmap`/escáner de puertos, `gobuster`/`ffuf`/`dirb`, `Burp Suite` o similar, `psql` opcional. |
| Objetivo | Obtener las 6 flags en orden, sumando 170 puntos. |
| Restricciones | Trabaja solo contra `http://localhost:8080`. No ataca el host, otros contenedores ni Internet. |
| Tiempo estimado | 2-4 horas, según experiencia. |

### 2.2 Operador / administrador del laboratorio

- Persona que despliega, verifica, reinicia y retira el laboratorio.
- No comparte `flags/flags.json` ni la flag final con el participante.
- Usa exclusivamente los scripts del proyecto (`scripts/start.sh`, `scripts/healthcheck.sh`, `scripts/stop.sh`, `scripts/reset.sh`).

---

## 3. Requisitos funcionales

### 3.1 Requisitos de plataforma y servicios

| ID | Requisito |
|---|---|
| **RF-01** | El laboratorio debe simular la empresa ficticia **DevCore Solutions** y su plataforma **DCPM**, con datos coherentes en portal, API y base de datos. |
| **RF-02** | El borde debe ser **nginx**, el único contenedor con puerto publicado en el host (por defecto `8080`, configurable mediante `LAB_HOST_PORT`). |
| **RF-03** | El portal web (Flask) debe servir: `/` (inicio), `/about`, `/team`, `/status` y una ruta administrativa señuelo `/admin/` con formulario de acceso sin efecto real. |
| **RF-04** | La API (Flask) debe exponer endpoints informativos y de datos: `/api/health`, `/api/`, `/api/projects`, `/api/projects/{id}`, `/api/users` y `/api/config`. |
| **RF-05** | Los servicios internos (`web`, `api`, `db`, `flags`) no deben publicar puertos en el host; solo son alcanzables desde la red interna del laboratorio. |
| **RF-06** | Todos los servicios deben tener healthcheck y el arranque debe esperar a que estén sanos antes de dar por disponible el laboratorio. |
| **RF-07** | Los datos de demostración deben cargarse de forma reproducible mediante migraciones y seed de base de datos. |

### 3.2 Requisitos de niveles y flags

El participante debe poder resolver cada nivel de forma independiente en contenido, pero la flag final exige las cinco anteriores.

#### Nivel 1 - Reconocimiento (10 pts)

| ID | Requisito |
|---|---|
| **RF-08** | La API debe filtrar el token de build ficticio `dc-api-2024.11-rc2` en la cabecera `X-DevCore-Build` de todas sus respuestas, de modo que el participante lo obtenga por inspección de cabeceras (por ejemplo, en `GET /api/health`). |
| **RF-09** | La evidencia del Nivel 1 es el valor de esa cabecera. El endpoint de desbloqueo debe aceptarla sin distinguir mayúsculas/minúsculas y con espacios laterales. |

#### Nivel 2 - Enumeración de directorios (20 pts)

| ID | Requisito |
|---|---|
| **RF-10** | nginx debe publicar listado de directorios (directory listing) en `/backup/`, `/files/` y `/old/`, de modo que el participante descubra el nombre del respaldo `devcore_archive_20241031.tar.gz` sin necesidad de adivinarlo. |
| **RF-11** | `robots.txt` y `sitemap.xml` deben estar servidos y deben sugerir rutas interesantes (`/backup/`, `/old/`, `/files/config/`, `/api/internal/`). |
| **RF-12** | La evidencia del Nivel 2 es el nombre del archivo de respaldo. El desbloqueo debe aceptarlo. |

#### Nivel 3 - Exposición de información de desarrolladores (20 pts)

| ID | Requisito |
|---|---|
| **RF-13** | El archivo `/files/internal/README-dev.md` debe estar accesible y contener el alias de la desarrolladora **s.ostermann**, además de notas internas que orienten al participante. |
| **RF-14** | El alias también debe aparecer en la página `/team`, en comentarios HTML de las plantillas y en notas internas de la base de datos, de modo que existan varias vías de verificación. |
| **RF-15** | La evidencia del Nivel 3 es el alias `s.ostermann`. |

#### Nivel 4 - Descubrimiento de secretos (30 pts)

| ID | Requisito |
|---|---|
| **RF-16** | El archivo de configuración `/files/config/.env.bak` debe quedar expuesto también en la ruta `/.env`, y debe contener la API key señuelo ficticia `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b`. |
| **RF-17** | La misma API key debe existir en `/api/config` y en el seed de base de datos, para que el participante pueda contrastar el secreto en más de un recurso. |
| **RF-18** | La evidencia del Nivel 4 es la API key. El desbloqueo debe aceptarla. |

#### Nivel 5 - Investigación de base de datos (40 pts)

| ID | Requisito |
|---|---|
| **RF-19** | El endpoint `GET /api/search?q=` debe ser vulnerable a inyección SQL por concatenación, permitiendo un `UNION SELECT` que extraiga de la tabla `internal_flags` el nivel, la flag y los puntos. |
| **RF-20** | La consulta `' UNION SELECT level, flag, points::text FROM internal_flags --` debe devolver la flag del Nivel 5 con estado HTTP 200. |
| **RF-21** | Los errores SQL deben reflejarse en la respuesta (estado 500 con la consulta y el detalle), como apoyo pedagógico para ajustar el payload. |
| **RF-22** | El resto de endpoints que consultan la base de datos deben usar consultas parametrizadas, como contraste de buenas prácticas. |
| **RF-23** | La flag del Nivel 5 debe poder validarse en el sistema de flags como cualquier otra. |

#### Nivel 6 - Root / flag final (50 pts)

| ID | Requisito |
|---|---|
| **RF-24** | El endpoint de desbloqueo debe aceptar `{"level": 6, "flags": [f1, f2, f3, f4, f5]}` y devolver la flag final únicamente si se entregan las cinco flags anteriores **en el orden correcto**. |
| **RF-25** | Debe rechazar combinaciones incompletas, desordenadas, duplicadas o con flags ajenas, devolviendo un error 403 y un mensaje que no entregue la solución. |

### 3.3 Sistema de flags

| ID | Requisito |
|---|---|
| **RF-26** | Debe existir un **servicio interno de flags** que concentre la configuración de niveles, flags, evidencias y puntos, y que no publique puertos en el host. |
| **RF-27** | **Validación**: `POST /api/flags/validate` con `{"flag": "..."}` debe responder si la flag existe, indicando nivel y puntos; una flag desconocida debe responder 404. |
| **RF-28** | **Desbloqueo por evidencia**: `POST /api/flags/unlock` con `{"level": N, "evidence": "..."}` para niveles 1-4, y con `{"level": 6, "flags": [...]}` para el nivel final. Evidencia incorrecta → 403. |
| **RF-29** | **Puntuación**: cada nivel otorga 10, 20, 20, 30, 40 y 50 puntos, con un total de **170 puntos**. La puntuación debe acumularse sin duplicados por nivel. |
| **RF-30** | **Registro de progreso**: el sistema debe persistir en una base de datos local (SQLite) el nivel resuelto, la flag, los puntos y la fecha. `GET /api/flags/progress` debe devolver niveles resueltos, puntuación acumulada, total de niveles y detalle. |
| **RF-31** | **Reinicio**: debe existir un mecanismo para reiniciar el progreso (reset) sin borrar las flags ni la configuración. |
| **RF-32** | **Pistas progresivas**: cada nivel debe tener al menos una pista accesible que oriente sobre la técnica o el recurso siguiente **sin revelar la flag ni la evidencia literal**. Las pistas se entregan a través de los propios recursos expuestos (ver tabla 3.4). |
| **RF-33** | El proxy de flags de la API debe reenviar validación, desbloqueo, progreso y reset al servicio interno, preservando códigos de estado y cuerpos. |
| **RF-34** | El servicio de flags no debe ser accesible directamente desde el host ni desde la red del borde; solo desde la red interna. |

### 3.4 Pistas progresivas (sin revelar evidencia)

| Nivel | Pista | Recurso |
|---|---|---|
| 1 | «Inspecciona las cabeceras de la API; DevCore versiona sus despliegues.» | `/api/health`, cabecera `X-DevCore-Build` |
| 2 | «El archivo de respaldo quedó publicado; empieza por `robots.txt` y `sitemap.xml`.» | `/robots.txt`, `/sitemap.xml`, `/backup/` |
| 3 | «La documentación interna no debía estar pública; busca el responsable de plataforma.» | `/files/internal/README-dev.md`, `/team` |
| 4 | «Los secretos de configuración suelen quedar en copias de `.env`.» | `/.env`, `/files/config/.env.bak`, `/api/config` |
| 5 | «La búsqueda de proyectos consulta nombres; prueba a romper el `LIKE`.» | `/api/search`, error SQL reflejado |
| 6 | «Reúne las cinco flags anteriores y entrégalas en orden.» | `/api/flags/unlock`, `/api/flags/progress` |

### 3.5 Inventario de endpoints

**Portal web (vía nginx, `http://localhost:8080`)**

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Portal DCPM |
| GET | `/health` | Salud del portal |
| GET | `/about` | Acerca de |
| GET | `/team` | Equipo (contiene alias de desarrolladores) |
| GET | `/status` | Estado del servicio |
| GET | `/admin/` | Login administrativo señuelo |
| POST | `/admin/login` | Credenciales señuelo, sin acceso real |
| GET | `/robots.txt` | Pistas de rutas |
| GET | `/sitemap.xml` | Mapa del sitio |
| GET | `/.env` | Fuga de configuración (señuelo) |
| GET | `/files/` | Listado de archivos internos |
| GET | `/backup/` | Listado de respaldos |
| GET | `/old/` | Listado de versión antigua |
| GET | `/server-status` | Estado de nginx |

**API interna (vía nginx)**

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Salud + cabecera de build |
| GET | `/api/` | Inventario de endpoints |
| GET | `/api/projects` | Proyectos |
| GET | `/api/projects/{id}` | Detalle parametrizado |
| GET | `/api/users` | Usuarios ficticios |
| GET | `/api/config` | Configuración interna con secretos señuelo |
| GET | `/api/search?q=` | Búsqueda vulnerable (SQLi) |
| GET | `/api/internal/recon-report` | Informe interno (confía en `X-Forwarded-For`) |
| POST | `/api/flags/validate` | Validar flag |
| POST | `/api/flags/unlock` | Desbloquear nivel |
| GET | `/api/flags/progress` | Progreso y puntuación |
| POST | `/api/flags/reset` | Reiniciar progreso |

**Servicio interno de flags (sin acceso desde el host)**

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/internal/health` | Salud |
| POST | `/internal/validate` | Validar flag |
| POST | `/internal/unlock` | Desbloquear nivel |
| GET | `/internal/progress` | Progreso |
| POST | `/internal/reset` | Reiniciar progreso |

---

## 4. Requisitos no funcionales

### 4.1 Aislamiento

| ID | Requisito |
|---|---|
| **RNF-01** | Todo el laboratorio debe ejecutarse con Docker Compose, en un proyecto propio (`developer-secrets`), sin depender de otros proyectos. |
| **RNF-02** | Deben existir dos redes: una **interna** (`ds-lab-net`, `internal: true`, sin Internet) para `web`, `api`, `db` y `flags`, y una **de borde** (`ds-edge-net`) que use únicamente `nginx`. |
| **RNF-03** | Los contenedores vulnerables (`web`, `api`, `db`, `flags`) no deben tener **egress a Internet** ni resolución DNS externa. |
| **RNF-04** | Solo `nginx` debe publicar puerto en el host; el resto debe usar `expose` interno. |
| **RNF-05** | El servicio de flags no debe publicar puertos ni ser accesible desde la red del borde. |
| **RNF-06** | **Prohibido** montar el socket de Docker (`/var/run/docker.sock`) en cualquier contenedor. |
| **RNF-07** | Los bind mounts deben limitarse a rutas dentro del directorio del proyecto; **prohibido** montar directorios personales, `HOME`, `Desktop`, etc. |
| **RNF-08** | Los volúmenes con nombre deben usar el prefijo del proyecto (`developer-secrets_`) para evitar colisiones. |
| **RNF-09** | Las imágenes deben ser propias (`devcore/*-lab:1.0.0`) o base explícita (`postgres:16-alpine`); no se deben referenciar imágenes de otros proyectos. |
| **RNF-10** | El laboratorio no debe afectar a otros proyectos Docker del host ni a sus redes, volúmenes o contenedores. |

### 4.2 Reversibilidad

| ID | Requisito |
|---|---|
| **RNF-11** | Debe ser posible detener y eliminar **solo** los recursos del proyecto (`docker compose down`), sin limpiezas globales. |
| **RNF-12** | Debe existir un reinicio completo que elimine contenedores, redes y volúmenes del proyecto, reconstruya las imágenes y vuelva a levantar todo desde cero. |
| **RNF-13** | **Prohibido** usar `docker system prune`, `volume prune` o `image prune` en los scripts del laboratorio. |
| **RNF-14** | El estado del progreso debe poder reiniciarse de forma independiente del despliegue. |

### 4.3 Reproducibilidad

| ID | Requisito |
|---|---|
| **RNF-15** | `docker compose up -d --build` debe dejar el laboratorio operativo y con todos los servicios sanos en un tiempo razonable (ver CA-GLOBAL-02). |
| **RNF-16** | El arranque debe ser idempotente y repetible en un host con Docker, sin pasos manuales ni estado previo. |
| **RNF-17** | El puerto del host debe ser configurable por variable de entorno (`LAB_HOST_PORT`) con valor por defecto `8080`. |
| **RNF-18** | Las credenciales, tokens y URLs internas deben ser configurables por variables de entorno, con valores por defecto ficticios. |
| **RNF-19** | El esquema y los datos de base de datos deben aplicarse de forma determinista (migración + seed). |
| **RNF-20** | Debe existir un script de verificación de salud que compruebe contenedores, endpoints y datos. |
| **RNF-21** | Deben existir pruebas unitarias, de integración y de seguridad/aislamiento ejecutables con un solo comando. |
| **RNF-22** | El laboratorio debe poder retirarse por completo sin dejar recursos huérfanos del proyecto. |

### 4.4 Seguridad del propio laboratorio

| ID | Requisito |
|---|---|
| **RNF-23** | Las flags y las evidencias solo deben residir en el servicio interno de flags y en la tabla `internal_flags` (Nivel 5); **no** deben aparecer en recursos servidos al participante ni en el código de `app`, `api`, `nginx`, `vulnerable-files` o `database`. |
| **RNF-24** | Las flags no deben aparecer en `/api/flags/progress` ni en respuestas de errores. |
| **RNF-25** | Todos los datos personales, correos, credenciales y secretos deben ser ficticios; no se debe incluir información real de personas ni organizaciones. |
| **RNF-26** | El laboratorio no debe usarse como referencia de configuración segura; debe identificarse claramente como material de entrenamiento vulnerable. |

---

## 5. Criterios de aceptación

### 5.1 Por nivel

| Nivel | Criterios de aceptación |
|---|---|
| **1 - Reconocimiento** | AC-1.1 `GET /api/health` responde 200 e incluye `X-DevCore-Build: dc-api-2024.11-rc2`.<br>AC-1.2 `POST /api/flags/unlock` con `{"level":1,"evidence":"dc-api-2024.11-rc2"}` responde 200 y devuelve `FLAG{RECON_COMPLETE}`.<br>AC-1.3 Una evidencia incorrecta responde 403 y no registra progreso.<br>AC-1.4 `POST /api/flags/validate` con esa flag responde 200, `valid: true`, `level: 1`, `points: 10`. |
| **2 - Enumeración** | AC-2.1 `GET /backup/` (o `/files/backups/`) muestra listado con `devcore_archive_20241031.tar.gz`.<br>AC-2.2 `robots.txt` y `sitemap.xml` son accesibles y sugieren rutas.<br>AC-2.3 El desbloqueo con `evidence: "devcore_archive_20241031.tar.gz"` responde 200 y devuelve `FLAG{DIRECTORY_DISCOVERED}` (+20). |
| **3 - Desarrolladores expuestos** | AC-3.1 `GET /files/internal/README-dev.md` contiene `s.ostermann`.<br>AC-3.2 `GET /team` muestra el alias del equipo.<br>AC-3.3 El desbloqueo con `evidence: "s.ostermann"` responde 200 y devuelve `FLAG{DEVELOPER_EXPOSED}` (+20). |
| **4 - Secretos** | AC-4.1 `GET /.env` devuelve texto con `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b`.<br>AC-4.2 `GET /files/config/.env.bak` y `GET /api/config` contienen la misma API key.<br>AC-4.3 El desbloqueo con esa evidencia responde 200 y devuelve `FLAG{SECRET_FOUND}` (+30). |
| **5 - Base de datos** | AC-5.1 `GET /api/search?q=' UNION SELECT level, flag, points::text FROM internal_flags -- ` responde 200 e incluye `FLAG{DATABASE_COMPROMISED}`.<br>AC-5.2 Una consulta que rompe la sintaxis responde 500 con la consulta reflejada.<br>AC-5.3 Los endpoints `/api/projects/{id}` y equivalentes usan consultas parametrizadas (no vulnerables a la misma inyección).<br>AC-5.4 `POST /api/flags/validate` con la flag del Nivel 5 responde 200, `valid: true`, `level: 5`, `points: 40`. |
| **6 - Final** | AC-6.1 `POST /api/flags/unlock` con `{"level":6,"flags":[las cinco flags en orden]}` responde 200 y devuelve `FLAG{DEVELOPER_SECRETS_ROOT}` (+50).<br>AC-6.2 Una lista con menos de cinco flags, en orden incorrecto o con flags ajenas responde 403.<br>AC-6.3 `GET /api/flags/progress` tras completar todo muestra `solved: [1,2,3,4,5,6]` y `score: 170`. |

### 5.2 Globales

| ID | Criterio |
|---|---|
| **CA-GLOBAL-01** | `./scripts/start.sh` construye y levanta los 5 servicios sin errores. |
| **CA-GLOBAL-02** | `healthcheck.sh` confirma contenedores sanos y endpoints `200` en menos de 60 segundos tras el arranque. |
| **CA-GLOBAL-03** | Solo `nginx` publica puerto; `web`, `api`, `db` y `flags` no publican ninguno. |
| **CA-GLOBAL-04** | La red interna `ds-lab-net` está marcada `internal: true`; `ds-edge-net` no. |
| **CA-GLOBAL-05** | `web`, `api`, `flags` y `db` no resuelven DNS externo ni conectan a Internet (verificado en pruebas). |
| **CA-GLOBAL-06** | Ningún contenedor monta `/var/run/docker.sock`; todos los bind mounts quedan dentro del proyecto. |
| **CA-GLOBAL-07** | Las banderas **no** aparecen en los recursos servidos (páginas, archivos, API, `/api/flags/progress`). |
| **CA-GLOBAL-08** | Las banderas **no** aparecen en el código servido (`app`, `api`, `nginx`, `vulnerable-files`, `database`). |
| **CA-GLOBAL-09** | El suite de pruebas (unitarias, integración, seguridad) pasa completamente. |
| **CA-GLOBAL-10** | `./scripts/reset.sh` deja el laboratorio recién construido, con progreso vacío y servicios sanos. |
| **CA-GLOBAL-11** | `./scripts/stop.sh` detiene y elimina solo los recursos del proyecto, sin afectar otros contenedores. |
| **CA-GLOBAL-12** | El progreso se conserva entre reinicios de servicios y puede reiniciarse con `/api/flags/reset`. |
| **CA-GLOBAL-13** | La puntuación máxima es 170 puntos y corresponde a la suma de los 6 niveles. |
| **CA-GLOBAL-14** | No se ejecuta ninguna limpieza global de Docker (`system prune`, `volume prune`, `image prune`). |
| **CA-GLOBAL-15** | El laboratorio no expone información real de personas u organizaciones; todo el contenido es ficticio. |

---

## 6. Restricciones

| ID | Restricción |
|---|---|
| **RES-01** | Solo se usa **Docker / Docker Compose**; no máquinas virtuales, ni Podman, ni clusters. |
| **RES-02** | El laboratorio es **local**: punto de entrada único `http://localhost:${LAB_HOST_PORT:-8080}`. |
| **RES-03** | Los contenedores vulnerables **no pueden salir a Internet** (red interna sin egress). |
| **RES-04** | **Prohibido** montar el socket de Docker en cualquier contenedor. |
| **RES-05** | **Prohibido** montar directorios personales o rutas fuera del proyecto. |
| **RES-06** | Red dedicada al proyecto, con nombres y volúmenes con prefijo propio. |
| **RES-07** | Todas las personas, correos, credenciales, tokens, clientes y secretos son **ficticios**; no se deben usar datos reales. |
| **RES-08** | El laboratorio debe poder **revertirse por completo** sin afectar otros proyectos del host. |
| **RES-09** | No se deben modificar archivos, configuraciones o recursos de otros proyectos. |
| **RES-10** | Los scripts del laboratorio no deben ejecutar limpiezas globales de Docker. |
| **RES-11** | Las flags, evidencias y este documento son **material de administración**; no deben publicarse en el laboratorio ni entregarse al participante. |
| **RES-12** | La configuración vulnerable es intencional; no debe "corregirse" en los servicios del laboratorio. |
| **RES-13** | El laboratorio no debe exponerse a Internet ni publicarse con credenciales reales. |
| **RES-14** | No se ejecuta Docker durante la redacción de este documento; la verificación es responsabilidad del operador. |

---

## 7. Fuera de alcance

- Ataques contra sistemas, hosts, contenedores o personas reales.
- Escapada del contenedor ("container escape") o ataques a Docker Engine / al anfitrión.
- Ataques de denegación de servicio (DoS/DDoS) o fuzzing masivo.
- Explotación de servicios de terceros, bibliotecas o infraestructura de Internet.
- Recolección o tratamiento de datos personales reales (PII).
- Autenticación real, SSO/LDAP, MFA/2FA o integración con proveedores externos.
- Despliegue en la nube, orquestadores (Kubernetes) o múltiples instancias simultáneas.
- Clasificación multicompetidor o tabla de posiciones externa; el progreso es local.
- Envío real de correos, notificaciones o webhooks.
- Persistencia real post-explotación en el host.
- Auditoría de seguridad del propio motor de Docker.
- Uso del laboratorio como plantilla de configuración segura para producción.
- Traducción del laboratorio a otros idiomas o adaptación a otros frameworks.
- Implementar más niveles, más flags o un modo "hardcore" distintos a los especificados.

---

## 8. Matriz de trazabilidad nivel → evidencia → flag → puntos

| Nivel | Objetivo | Evidencia | Recurso / vector | Flag | Puntos | RF relacionados |
|---|---|---|---|---|---|---|
| 1 | Reconocimiento de servicios | `dc-api-2024.11-rc2` | Cabecera `X-DevCore-Build` en `GET /api/health` | `FLAG{RECON_COMPLETE}` | 10 | RF-04, RF-08, RF-09 |
| 2 | Enumeración de directorios | `devcore_archive_20241031.tar.gz` | Directory listing en `/backup/` o `/files/backups/`; pistas en `/robots.txt` y `/sitemap.xml` | `FLAG{DIRECTORY_DISCOVERED}` | 20 | RF-10, RF-11, RF-12 |
| 3 | Exposición de información de desarrolladores | `s.ostermann` | `/files/internal/README-dev.md`, `/team`, comentarios HTML | `FLAG{DEVELOPER_EXPOSED}` | 20 | RF-03, RF-13, RF-14, RF-15 |
| 4 | Descubrimiento de secretos | `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b` | `/.env`, `/files/config/.env.bak`, `/api/config` | `FLAG{SECRET_FOUND}` | 30 | RF-04, RF-16, RF-17, RF-18 |
| 5 | Investigación de base de datos | `FLAG{DATABASE_COMPROMISED}` (extraída de `internal_flags`) | SQLi en `GET /api/search` con `UNION SELECT level, flag, points::text FROM internal_flags` | `FLAG{DATABASE_COMPROMISED}` | 40 | RF-19, RF-20, RF-21, RF-22, RF-23 |
| 6 | Root / flag final | Las cinco flags anteriores en orden | `POST /api/flags/unlock` con `{"level":6,"flags":[...]}` | `FLAG{DEVELOPER_SECRETS_ROOT}` | 50 | RF-24, RF-25, RF-28, RF-30 |

**Total de puntos posibles: 170.**

### 8.1 Trazabilidad inversa (requisito → criterio de aceptación)

| Requisito | Criterio de aceptación |
|---|---|
| RF-08, RF-09 (Nivel 1) | AC-1.1, AC-1.2, AC-1.3, AC-1.4 |
| RF-10, RF-11, RF-12 (Nivel 2) | AC-2.1, AC-2.2, AC-2.3 |
| RF-13, RF-14, RF-15 (Nivel 3) | AC-3.1, AC-3.2, AC-3.3 |
| RF-16, RF-17, RF-18 (Nivel 4) | AC-4.1, AC-4.2, AC-4.3 |
| RF-19, RF-20, RF-21, RF-22 (Nivel 5) | AC-5.1, AC-5.2, AC-5.3, AC-5.4 |
| RF-24, RF-25 (Nivel 6) | AC-6.1, AC-6.2, AC-6.3 |
| RF-26 a RF-34 (sistema de flags) | AC-1.2 a AC-6.3, CA-GLOBAL-07, CA-GLOBAL-12, CA-GLOBAL-13 |
| RNF-01 a RNF-10 (aislamiento) | CA-GLOBAL-03, CA-GLOBAL-04, CA-GLOBAL-05, CA-GLOBAL-06 |
| RNF-11 a RNF-14 (reversibilidad) | CA-GLOBAL-10, CA-GLOBAL-11, CA-GLOBAL-14 |
| RNF-15 a RNF-22 (reproducibilidad) | CA-GLOBAL-01, CA-GLOBAL-02, CA-GLOBAL-09 |
| RNF-23 a RNF-26 (seguridad del laboratorio) | CA-GLOBAL-07, CA-GLOBAL-08, CA-GLOBAL-15 |

---

*Documento de requisitos y criterios de aceptación. Contenido ficticio; material de administración del laboratorio.*
