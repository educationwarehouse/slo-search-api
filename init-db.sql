-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embedding tables with 1536 dimensions
CREATE TABLE IF NOT EXISTS doelzin_embedding (
    id SERIAL PRIMARY KEY,
    doelzin_id INTEGER NOT NULL UNIQUE,
    embedding_model VARCHAR(512) NOT NULL,
    embedding vector(1536) NOT NULL
);

CREATE TABLE IF NOT EXISTS uitwerking_embedding (
    id SERIAL PRIMARY KEY,
    uitwerking_id INTEGER NOT NULL UNIQUE,
    embedding_model VARCHAR(512) NOT NULL,
    embedding vector(1536) NOT NULL
);

-- Create vector indexes
CREATE INDEX IF NOT EXISTS doelzin_embedding_vector_idx ON doelzin_embedding 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS uitwerking_embedding_vector_idx ON uitwerking_embedding 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
