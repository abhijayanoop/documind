import pytest
from documind.retrieval import (
    DenseRetriever, BM25Retriever, HybridRetriever, reciprocal_rank_fusion, RetrievedDoc,
)


class FakeEmbedder:
    """Deterministic embedder for tests — no network, no cost.

    Returns a fixed-dimension vector derived from text length so results
    are stable. We're testing the RBAC + fusion plumbing, not embedding quality.
    """
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 7)] * 1536 for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@pytest.fixture
def dense():
    return DenseRetriever(embedder=FakeEmbedder())


def test_same_query_differs_by_role(dense):
    """The flagship guarantee: identical query, different docs per role."""
    q = "What is the ML engineer salary?"
    candidate = {h.document_id for h in dense.retrieve(q, "candidate_1", "cred", top_k=10)}
    manager = {h.document_id for h in dense.retrieve(q, "manager_1", "cred", top_k=10)}

    assert "doc_002" not in candidate     # salary_tier hidden from candidate
    assert "doc_002" in manager           # visible to hiring manager
    assert "doc_001" in candidate         # public visible to both


def test_tenant_isolation_through_retrieval(dense):
    """A CRED user never retrieves Razorpay rows, even semantically similar ones."""
    hits = dense.retrieve("salary bands", "candidate_1", "cred", top_k=10)
    ids = {h.document_id for h in hits}
    # candidate_1 is CRED + candidate role → only CRED public docs
    assert ids <= {"doc_001"}             # subset: nothing forbidden, nothing cross-tenant


def test_bm25_respects_rbac():
    """Sparse retrieval enforces the same access filter as dense."""
    bm25 = BM25Retriever()
    hits = bm25.retrieve("salary", "candidate_1", "cred", top_k=10)
    assert all(h.document_id != "doc_002" for h in hits)


def test_rrf_rewards_agreement():
    """A doc ranked high in both lists beats one ranked high in only one."""
    a = RetrievedDoc("X", "t", "c", 0.9)
    b = RetrievedDoc("Y", "t", "c", 0.9)
    c = RetrievedDoc("Z", "t", "c", 0.9)
    dense_list = [a, b, c]      # X best in dense
    sparse_list = [a, c, b]     # X best in sparse too
    fused = reciprocal_rank_fusion([dense_list, sparse_list], top_k=3)
    assert fused[0].document_id == "X"   # agreed-upon top wins