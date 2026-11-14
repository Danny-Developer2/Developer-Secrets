-- ============================================================
--  DevCore Solutions - Laboratorio
--  Migracion 001: esquema (todo ficticio)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(50) UNIQUE NOT NULL,
    full_name  VARCHAR(120),
    email      VARCHAR(120),
    role       VARCHAR(40),
    department VARCHAR(60),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clients (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(120) NOT NULL,
    industry VARCHAR(80),
    country  VARCHAR(60)
);

CREATE TABLE IF NOT EXISTS projects (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(20) UNIQUE NOT NULL,
    name       VARCHAR(120) NOT NULL,
    status     VARCHAR(30),
    owner      VARCHAR(60),
    client_id  INT REFERENCES clients(id),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notes (
    id         SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id),
    author     VARCHAR(60),
    body       TEXT,
    internal   BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS app_config (
    key       VARCHAR(80) PRIMARY KEY,
    value     TEXT,
    is_secret BOOLEAN NOT NULL DEFAULT false
);

-- Solo el flag del Nivel 5 vive en la base de datos (por diseno,
-- para que la SQLi tenga un botin concreto). Las demas flags se
-- guardan en el servicio interno de flags, no en la base de datos.
CREATE TABLE IF NOT EXISTS internal_flags (
    level  INT PRIMARY KEY,
    flag   VARCHAR(120) NOT NULL,
    points INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         SERIAL PRIMARY KEY,
    actor      VARCHAR(60),
    action     VARCHAR(160),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
