-- Initialize PostgreSQL database for SLO Search
-- This runs automatically when container is first created

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE slo_search TO slo_user;

-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS public;
GRANT ALL ON SCHEMA public TO slo_user;

-- Done - pydal will handle table creation
