-- Drop existing vector indexes
DROP INDEX IF EXISTS doelzin_embedding_vector_idx;
DROP INDEX IF EXISTS uitwerking_embedding_vector_idx;

-- Truncate embedding tables (removes all existing embeddings)
TRUNCATE TABLE doelzin_embedding CASCADE;
TRUNCATE TABLE uitwerking_embedding CASCADE;

-- Alter vector columns to 1536 dimensions
ALTER TABLE doelzin_embedding ALTER COLUMN embedding TYPE vector(1536);
ALTER TABLE uitwerking_embedding ALTER COLUMN embedding TYPE vector(1536);

-- Recreate vector indexes for 1536 dimensions
CREATE INDEX doelzin_embedding_vector_idx ON doelzin_embedding 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX uitwerking_embedding_vector_idx ON uitwerking_embedding 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
