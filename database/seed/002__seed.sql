-- ============================================================
--  DevCore Solutions - Laboratorio
--  Seed 002: datos ficticios de demostracion
-- ============================================================

-- --- Usuarios ficticios ---
INSERT INTO users (username, full_name, email, role, department) VALUES
    ('s.ostermann', 'Sofia Ostermann', 's.ostermann@devcore.example', 'Lead Backend',   'Plataforma'),
    ('m.retana',    'Marco Retana',    'm.retana@devcore.example',    'Frontend',       'Plataforma'),
    ('d.fuentes',   'Diego Fuentes',   'd.fuentes@devcore.example',   'DBA',            'Datos'),
    ('a.beltran',   'Ana Beltran',     'a.beltran@devcore.example',   'DevOps',         'Infraestructura'),
    ('j.salazar',   'Julio Salazar',   'j.salazar@devcore.example',   'QA',             'Calidad'),
    ('r.villalobos','Raul Villalobos', 'r.villalobos@devcore.example','Soporte',        'Operaciones');

-- --- Clientes ficticios ---
INSERT INTO clients (name, industry, country) VALUES
    ('Grupo Meridian',   'Financiero',   'Mexico'),
    ('Norte Logistica',  'Logistica',    'Mexico'),
    ('Kubo Retail',      'Retail',       'Colombia'),
    ('Andino Salud',     'Salud',        'Peru');

-- --- Proyectos ---
INSERT INTO projects (code, name, status, owner, client_id) VALUES
    ('DCPM',        'Plataforma de gestion de proyectos', 'en produccion', 's.ostermann', 1),
    ('MERIDIAN-ERP','Integracion contable Meridian',      'piloto',        'm.retana',    1),
    ('KUBO-STOREF', 'Tienda en linea Kubo',               'desarrollo',    'j.salazar',   3),
    ('ANDINO-PORT', 'Portal de pacientes Andino',         'mantenimiento', 'd.fuentes',   4),
    ('NORTE-TRACK', 'Rastreo de flotas Norte',            'planeacion',    'a.beltran',   2);

-- --- Notas internas ---
INSERT INTO notes (project_id, author, body, internal) VALUES
    (1, 's.ostermann', 'El API interno usa la cabecera X-DevCore-Build para versionarse.', true),
    (1, 'd.fuentes',   'Credenciales de la base de datos en /files/config/.env.bak (revisar).', true),
    (2, 'm.retana',    'Pendiente revisar el piloto con Meridian la proxima semana.', false),
    (3, 'j.salazar',   'QA cubre flujos de compra y pagos ficticios.', false),
    (4, 'd.fuentes',   'Migracion de la base de datos programada para el finde.', true);

-- --- Configuracion interna (secretos senuelo) ---
INSERT INTO app_config (key, value, is_secret) VALUES
    ('DEVCORE_API_KEY',        'dc_live_9f4e2b7a6c8d1e3f5a7b9c2d4e6f8a0b', true),
    ('JWT_SECRET',             'devcore_jwt_ficticio_a1b2c3d4e5f6',        true),
    ('DB_PASSWORD',            'devcore_ficticio_2024',                    true),
    ('BACKUP_PATH',            '/var/backups/devcore_archive_20241031.tar.gz', false),
    ('BUILD_TOKEN',            'dc-api-2024.11-rc2',                       false),
    ('MAINTENANCE_MODE',       'false',                                   false),
    ('LOG_LEVEL',              'debug',                                   false),
    ('INTERNAL_DASHBOARD_URL', 'http://127.0.0.1:8000/status/dashboard',    false);

-- --- Flag del Nivel 5 (unica flag almacenada en la base de datos) ---
INSERT INTO internal_flags (level, flag, points) VALUES
    (5, 'FLAG{DATABASE_COMPROMISED}', 40);

-- --- Auditoria ---
INSERT INTO audit_log (actor, action) VALUES
    ('s.ostermann', 'Publicacion del build 2024.11-rc2'),
    ('d.fuentes',   'Respaldo completo de la base de datos'),
    ('a.beltran',   'Cambio de la configuracion de nginx'),
    ('m.retana',    'Actualizacion del portal DCPM');
