from dataclasses import dataclass
from documind.rbac import AccessController
from documind.embeddings import Embedder, LiteLLMEmbedder
from documind.database import get_connection

@dataclass
class RetrievedDoc:
    document_id: str
    title: str
    content: str 
    score: float

class DenseRetriever:
    def __init__(self, access_controller: AccessController | None = None, embedder: Embedder | None = None,):
        self.access = access_controller or AccessController()
        self.embedder = embedder or LiteLLMEmbedder()

    def retrieve(self, query: str, user_id: str, tenant_id: str, top_k: int = 5) -> list[RetrievedDoc]:
        accessible_ids = self.access.get_accessible_document_ids(user_id, tenant_id)
        if not accessible_ids: 
            return []

        embedded_query = self.embedder.embed_one(query)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document_id, title, content, 1 - (embedding <=> %s::vector) AS similiarity FROM documents 
                            WHERE tenant_id=%s AND document_id=any(%s) AND embedding IS NOT NULL
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s
                """, (embedded_query, tenant_id, accessible_ids, embedded_query, top_k))
                rows = cur.fetchall()
        
        return [RetrievedDoc(document_id=r[0], title=r[1], content=r[2], score=r[3]) for r in rows]
