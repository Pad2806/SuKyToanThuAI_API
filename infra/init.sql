-- ============================================================
-- SuKyAI Platform — PostgreSQL Init Script
-- Runs once when the postgres container starts for the first time.
-- ============================================================

-- Extensions (must be in public schema)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Schemas per service (logical isolation)
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS rag;
CREATE SCHEMA IF NOT EXISTS story;
CREATE SCHEMA IF NOT EXISTS ai;

-- Grant all privileges to the app user on each schema
DO $$
DECLARE
  app_user TEXT := current_user;
BEGIN
  EXECUTE format('GRANT ALL ON SCHEMA auth    TO %I', app_user);
  EXECUTE format('GRANT ALL ON SCHEMA content TO %I', app_user);
  EXECUTE format('GRANT ALL ON SCHEMA rag     TO %I', app_user);
  EXECUTE format('GRANT ALL ON SCHEMA story   TO %I', app_user);
  EXECUTE format('GRANT ALL ON SCHEMA ai      TO %I', app_user);
END $$;
