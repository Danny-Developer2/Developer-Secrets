# Guia del administrador

## 1. Requisitos

- Docker Desktop (daemon activo) y Docker Compose v2.
- Puerto libre `8080` en el host.
- Acceso a una terminal con `docker`, `curl` y `python3` (para las pruebas).

## 2. Despliegue

```bash
cd /Users/ing_juan/Desktop/HTB-Labs/Developer-Secrets
docker compose up -d --build
```

Tambien puedes usar el script, que ademas verifica el estado:

```bash
./scripts/start.sh
```

La maquina queda en **http://localhost:8080**.

## 3. Operacion

| Accion | Comando | Efecto |
|---|---|---|
| Iniciar / reconstruir | `./scripts/start.sh` | `up -d --build` + healthcheck |
| Detener | `./scripts/stop.sh` | `compose stop`; conserva volumenes |
| Reinicio completo | `./scripts/reset.sh` | `down -v` + `up -d --build` |
| Ver estado | `./scripts/healthcheck.sh` | contenedores, endpoints y DB |
| Pruebas | `./scripts/test.sh` | unit + integracion + seguridad |

`reset.sh` ejecuta `docker compose down -v --remove-orphans`, que **unicamente** afecta
al proyecto `developer-secrets`. No ejecuta `docker system prune` ni elimina volumenes de
otros proyectos.

## 4. Usuarios y credenciales del laboratorio (todos ficticios)

| Uso | Valor |
|---|---|
| Postgres usuario | `devcore` |
| Postgres password | `devcore_ficticio_2024` |
| Postgres base de datos | `devcore` |
| Login admin senuelo (web) | `admin` / `DevCore2024!` |
| API key senuelo | `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b` |

Ninguno de estos valores sirve para autenticar en servicios reales.

## 5. Flags y referencia del administrador

Las flags y las evidencias estan en `flags/flags.json`. El sistema de validacion solo
existe en el contenedor `flags` (red interna).

| Nivel | Evidencia requerida | Flag | Puntos |
|---|---|---|---|
| 1 | `dc-api-2024.11-rc2` | `FLAG{RECON_COMPLETE}` | 10 |
| 2 | `devcore_archive_20241031.tar.gz` | `FLAG{DIRECTORY_DISCOVERED}` | 20 |
| 3 | `s.ostermann` | `FLAG{DEVELOPER_EXPOSED}` | 20 |
| 4 | `dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b` | `FLAG{SECRET_FOUND}` | 30 |
| 5 | (se obtiene de la SQLi) | `FLAG{DATABASE_COMPROMISED}` | 40 |
| 6 | las cinco flags anteriores | `FLAG{DEVELOPER_SECRETS_ROOT}` | 50 |

Puntuacion maxima: **170**.

Comandos de gestion:

```bash
curl -s http://localhost:8080/api/flags/progress
curl -s -X POST http://localhost:8080/api/flags/reset -H 'Content-Type: application/json' -d '{}'
```

Para inspeccionar el servicio interno directamente (solo desde el host, via contenedor):

```bash
docker compose exec flags python -c \
  "import json;print(json.load(open('/app/flags.json'))['flags'])"
```

## 6. Resolucion de problemas

**`bind: address already in use` en el puerto 8080.**
Cambia el puerto: `LAB_HOST_PORT=8090 docker compose up -d` (o edita `.env`).

**Solo escucha en 127.0.0.1 y no puedo acceder desde otro equipo.**
Es el comportamiento por defecto (recomendacion de seguridad REAL-02). Para exponerlo:
`LAB_BIND_ADDRESS=0.0.0.0 docker compose up -d`.

**Un contenedor queda en `unhealthy`.**
`docker compose logs <servicio>`. Si la base de datos no inicializo el seed, revisa que
`database/migrations/002__apply_seed.sh` tenga permiso de ejecucion y que el volumen no
esté corrupto: `./scripts/reset.sh`.

**Las flags no validan.**
Reinicia el progreso (`POST /api/flags/reset`) y comprueba que el contenedor `flags` esta
`sano` (`docker compose ps`). Las evidencias comparan sin distinguir mayusculas.

**Quiero datos limpios.**
`./scripts/reset.sh` reconstruye desde cero (esquema + seed).

**No puedo acceder desde el navegador.**
Verifica que `ds-nginx` este `Up` y que el puerto publicado sea el esperado:
`docker compose port nginx 80`.

## 7. Apagado

```bash
./scripts/stop.sh
```

Para eliminar tambien los volumenes (sin afectar a otros proyectos):

```bash
docker compose down -v
```
