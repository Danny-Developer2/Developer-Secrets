# README interno - Portal DCPM

> Documento interno del equipo de plataforma. **No deberia estar publicado.**

## Estado del portal

- Version: 2.4.1 (build `2024.11-rc2`)
- Responsable del despliegue: **s.ostermann**
- Base de datos: PostgreSQL 16, esquema `devcore`
- Backups: `/backup/devcore_archive_20241031.tar.gz` (realizado por s.ostermann)

## Estructura del repositorio

```
devcore-dcpm/
  app/            Portal Flask (DCPM)
  api/            API interna Flask
  database/       Migraciones y seeds
  nginx/          Configuracion del borde
  docs/           Documentacion tecnica
  scripts/        Scripts de operacion
```

## Notas pendientes

- Retirar `/files`, `/backup` y `/old` del servidor publico.
- Rotar `DEVCORE_API_KEY` y `JWT_SECRET` (estan en `/files/config/.env.bak`).
- El dashboard interno vive en `/status/dashboard` y solo debe responder
  desde la red interna.

## Contacto

- Plataforma: s.ostermann
- Datos: d.fuentes
- Infraestructura: a.beltran
