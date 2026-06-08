ALTER TABLE documents
    ADD COLUMN content_tsv tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED;

CREATE INDEX idx_documents_content_tsv ON documents USING GIN (content_tsv);