CREATE TABLE IF NOT EXISTS  documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    access_level TEXT NOT NULL CHECK(
        access_level in ('public','internal','salary_tier','hiring_manager','c_suite')
    ),
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant_access
    ON documents (tenant_id, access_level);

CREATE TABLE IF NOT EXISTS  user_roles (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (
                    role IN
                    ('public_user','candidate','junior_employee',
                     'hiring_manager','hr','admin','c_suite')
                ),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id)
);

CREATE TABLE IF NOT EXISTS  query_log (
    id                 BIGSERIAL PRIMARY KEY,
    tenant_id          TEXT NOT NULL,
    user_id            TEXT NOT NULL,
    query_text         TEXT NOT NULL,
    retrieved_doc_ids  TEXT[] NOT NULL DEFAULT '{}',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_log_tenant_user
    ON query_log (tenant_id, user_id);


