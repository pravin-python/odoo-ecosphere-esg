-- EcoSphere database bootstrap.
--
-- Creates the application role and database. The app role is deliberately
-- NOSUPERUSER and NOBYPASSRLS so that row-level security policies actually
-- apply to it (combined with FORCE ROW LEVEL SECURITY on each table).
--
-- Run once as a Postgres superuser:
--     psql -U postgres -f scripts/db/init.sql
-- (The docker-compose db service runs this automatically on first boot.)

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ecosphere_app') THEN
        CREATE ROLE ecosphere_app LOGIN PASSWORD 'ecosphere'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
$$;

SELECT 'CREATE DATABASE ecosphere OWNER ecosphere_app'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'ecosphere')\gexec

GRANT ALL PRIVILEGES ON DATABASE ecosphere TO ecosphere_app;
