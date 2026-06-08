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
        
        return [RetrievedDoc(document_id=r[0], title=r[1], content=r[2], score=float(r[3])) for r in rows]

class BM25Retriever:
    def __init__(self, access_controller: AccessController):
        self.access = access_controller or AccessController()

    def retrieve(self, query: str, tenant_id: str, user_id: str, top_k: int = 5)->list[RetrievedDoc]:
        accessible_docs = self.access.get_accessible_document_ids(user_id, tenant_id)
        if not accessible_docs:
            return []
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document_id, title, content, 
                    ts_rank(content_tsv, websearch_to_tsquery("english", %s)) AS rank
                    WHERE tenant_id=%s 
                    AND document_id=ANY(%s)
                    AND content_tsv @@ websearch_to_tsquery("english", %s)
                    LIMIT %s
                """, (query, tenant_id, accessible_docs, query, top_k))
                rows = cur.fetchall()
        
        return [RetrievedDoc(document_id=r[0], title=r[1], content=r[2], score=float(r[3])) for r in rows]
    
def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievedDoc]], k: int = 60, top_k: int = 5
) -> list[RetrievedDoc]:
    """Merge multiple ranked lists by rank position (not raw score).

    Each doc's fused score = sum over lists of 1 / (k + rank_in_that_list).
    rank is 0-based here. Returns the top_k fused docs.
    """
    scores: dict[str, float] = {}
    doc_by_id: dict[str, RetrievedDoc] = {}

    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked):
            scores[doc.document_id] = scores.get(doc.document_id, 0.0) + 1.0 / (k + rank)
            doc_by_id[doc.document_id] = doc   # keep the doc object for output

    fused = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    out: list[RetrievedDoc] = []
    for doc_id, fused_score in fused[:top_k]:
        doc = doc_by_id[doc_id]
        out.append(RetrievedDoc(doc.document_id, doc.title, doc.content, fused_score))
    return out

class HybridRetriever:
    def __init__(self, access_controller: AccessController | None = None, embedder: Embedder | None = None):
        access = access_controller or AccessController()
        self.dense = DenseRetriever(access, embedder)
        self.sparse = BM25Retriever(access)

    def retrieve(
        self, query: str, user_id: str, tenant_id: str, top_k: int = 5
    ) -> list[RetrievedDoc]:
        pool = max(top_k * 2, 10)
        dense_hits = self.dense.retrieve(query, user_id, tenant_id, top_k=pool)
        sparse_hits = self.sparse.retrieve(query, user_id, tenant_id, top_k=pool)
        return reciprocal_rank_fusion([dense_hits, sparse_hits], top_k=top_k)

