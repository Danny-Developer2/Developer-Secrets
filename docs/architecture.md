# Arquitectura — Developer Secrets (Docker Hacking Lab)

Documento del CTO / Software Architect. Incluye las decisiones de arquitectura (ADR)
y la justificacion tecnica.

## 1. Contexto y objetivos

Se necesita una maquina vulnerable **desplegable, reproducible y documentada**, util
para practicar reconocimiento, enumeracion, exposicion de informacion y explotacion
controlada. Restricciones duras:

1. Ejecucion exclusivamente en Docker, aislada del host y de otros proyectos.
2. Sin socket de Docker, sin montar directorios personales, sin egress a Internet
   desde los contenedores vulnerables.
3. Todos los datos y secretos son ficticios.
4. Reversible: poder iniciar, detener y reiniciar sin afectar nada mas.

## 2. Decisiones de arquitectura (ADR)

### ADR-001 — Flask + gunicorn en los tres servicios Python

**Decision:** `web`, `api` y `flags` son aplicaciones Flask servidas con gunicorn.

**Alternativas:** FastAPI, Django, Node/Express.

**Justificacion:** el valor del laboratorio esta en la logica vulnerable y en la ruta de
exposicion, no en el framework. Flask es minimo,imental de revisar y permite construir
los fallos de forma explicita (concatenacion SQL, confianza en `X-Forwarded-For`,
respuestas que filtran detalles). Un unico stack reduce el tiempo de build y la
superficie de fallo. gunicorn con 1-2 workers evita el servidor de desarrollo de Flask,
que es inadecuado y ademas filtraria stack traces de formas no controladas.

**Consecuencia:** el API no usa ORM; el acceso a datos es SQL directo con `psycopg2`,
que es precisamente lo que permite la SQLi didactica.

### ADR-002 — PostgreSQL 16 en contenedor, solo red interna

**Decision:** `postgres:16-alpine`, sin puertos publicos, con migraciones y seed
versionados en SQL.

**Justificacion:** la SQLi union-based needs un motor SQL real y una tabla con la flag
del nivel 5. PostgreSQL es el motor mas usado en entornos empresariales y facilita el
`UNION SELECT ... FROM internal_flags`. El seed versionado en SQL hace que el laboratorio
sea reproducible sin dependencias de ORM.

### ADR-003 — nginx como unico borde publicado

**Decision:** nginx recibe el trafico en el puerto 80 y lo reparte a `web` y `api`.
Ademas sirve los archivos de `vulnerable-files` con `autoindex on`.

**Justificacion:** la enzada de directory listing, las fugas de `Server`, `stub_status`
y los `alias` que exponen directorios "internos" son el corazon de los niveles 1, 2 y 4.
Hacerlo en nginx (y no en Flask) reproduce el escenario real: el borde mal configurado
es el que publica lo que no debe.

### ADR-004 — Dos redes: internal para la aplicacion, bridge para el borde

**Decision:**
- `ds-lab-net` con `internal: true` para `web`, `api`, `db`, `flags`.
- `ds-edge-net` (bridge normal) solo para `nginx`, que publica `8080:80`.

**Justificacion y verificacion empirica:** con una unica red `internal: true`, Docker
**no publica** los puertos del contenedor (verificado: `curl` al puerto publicado da
`connection refused`, mientras que contenedor-a-contenedor si funciona). Por tanto no es
posible tener un solo contenedor internal y acceder desde el host.

La alternativa de borrar la ruta por defecto dentro del contenedor rompe el trafico
entrante publicado (verificado: timeout). Ademas, `internal: true` es la unica forma
nativa y verificable de garantizar **sin egress** (verificado: falla DNS y falla
`wget https://example.com`) sin tocar el firewall del host.

**Consecuencia aceptada:** `ds-edge-net` es un bridge normal y `nginx` tiene ruta por
defecto. `nginx` no realiza ninguna llamada saliente por configuracion (es un proxy
estatico), y todos los contenedores con logica vulnerable estan en la red internal.
Esta decision se registra como observacion en el informe de ciberseguridad.

### ADR-005 — Flags en un servicio interno, no en archivos servidos

**Decision:** las flags y las evidencias viven en `flags/flags.json`, montado **solo**
en el contenedor `flags` (read-only). El `api` consulta a `flags` por la red interna.
El participante obtiene una flag al demostrar el hallazgo (evidencia) o al extraerla de
la base de datos (nivel 5).

**Justificacion:** el requisito explicito es que las flags **no** aparezcan en el codigo
fuente publico ni en archivos descargables. Si las flags fueran archivos estaticos, se
podrian descargar; si estuvieran en el codigo del API, se podrian leer. Centralizarlas
en un contenedor sin puertos publicos cumple la regla de forma estructural y ademas
permite validacion, puntuacion y registro de progreso.

**Mecanismo de desbloqueo:**

| Nivel | Mecanismo |
|---|---|
| 1-4 | `POST /api/flags/unlock` con la evidencia descubierta |
| 5 | La flag se lee de la tabla `internal_flags` mediante SQLi y se valida |
| 6 | `POST /api/flags/unlock` con las cinco flags anteriores en orden |

### ADR-006 — Contenedores por servicio, con nombre e imagen propios

**Decision:** cada servicio tiene su `Dockerfile`, su imagen `devcore/<servicio>-lab:1.0.0`
y su `container_name` `ds-*`. El proyecto compose se llama `developer-secrets`.

**Justificacion:** nombres estables permiten que los tests de aislamiento y los scripts
referencien contenedores sin ambiguedad, y evitan colisiones con otros proyectos del
host. Las imagenes propias dejan claro el alcance.

## 3. Diagrama

```
        host
          │  http://localhost:8080
          ▼
   ┌──────────────┐        ds-edge-net (bridge)
   │  ds-nginx    │────────┐
   └──────┬───────┘        │
          │ ds-lab-net     │
          │ (internal)     │
   ┌──────┴────────────────┴───────────────────────┐
   │  ds-web      ds-api       ds-db      ds-flags │
   │  (Flask)     (Flask+SQLi) (PostgreSQL) (flags)│
   └───────────────────────────────────────────────┘
        ▲ sin Internet, sin DNS externo, sin puertos publicos
```

## 4. Flujo de datos de la SQLi (Nivel 5)

```
participante -> nginx:8080/api/search?q=... -> ds-api -> PostgreSQL
```

`ds-api` concatena el parametro en el SQL y lo ejecuta con el usuario `devcore`, que
tiene permisos sobre todo el esquema (incluida `internal_flags`). De ahi que el
`UNION SELECT` pueda leer la flag del nivel 5. El resto de endpoints usan consultas
parametrizadas, para que el participante tenga contraste entre lo vulnerable y lo correcto.

## 5. Criterios de aceptacion de arquitectura

- [x] `docker compose up -d --build` levanta los cinco servicios.
- [x] Solo `ds-nginx` publica puerto.
- [x] `ds-web`, `ds-api`, `ds-db`, `ds-flags` no tienen egress (red internal).
- [x] No se monta el socket de Docker ni directorios fuera del proyecto.
- [x] Las flags no estan en el codigo servido ni en archivos descargables.
- [x] Reinicio completo sin limpiezas globales de Docker.
