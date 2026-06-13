from dataclasses import dataclass
from documind.embeddings import Embedder, LiteLLMEmbedder
from documind.database import get_connection

@dataclass
class DocumentInput:
    tenant_id: str
    document_id: str
    title: str
    content: str
    access_level: str

def ingest_documents(docs: list[DocumentInput], embedder: Embedder | None = None)->int:
    if not docs:
        return 0
    
    embedder = embedder or LiteLLMEmbedder()

    vectors = embedder.embed([doc.content for doc in docs])

    with get_connection() as conn:
        with conn.cursor() as cur:
            for doc, vector in zip(docs, vectors):
                cur.execute("""
                    INSERT INTO documents (tenant_id, document_id, title, content, access_level, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, document_id)
                    DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    access_level = EXCLUDED.access_level,
                    embedding = EXCLUDED.embedding
                """, (doc.tenant_id, doc.document_id, doc.title, doc.content, doc.access_level, vector))
        conn.commit()
    return len(docs)

def backfill_embeddings(embedder: Embedder | None = None, batch_size: int = 100)-> int:
    embedder = embedder or LiteLLMEmbedder()

    updated: int = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE embedding IS NULL LIMIT %s", (batch_size,))
            rows = cur.fetchall()
        if not rows:
            return 0
        ids = [r[0] for r in rows]
        contents = [r[1] for r in rows]
        vectors = embedder.embed(contents)

        with conn.cursor() as cur:
            for row_id, vector in zip(ids, vectors):
                cur.execute("UPDATE documents SET embedding=%s WHERE id=%s", (vector, row_id))
        conn.commit()
        updated += len(rows)
    return updated