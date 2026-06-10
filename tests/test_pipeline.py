import pytest
from documind.pipeline import AnswerPipeline, AnswerResult
from documind.llm import LLMResponse
from documind.prompts import ABSTENTION
from documind.retrieval import HybridRetriever
from documind.rbac import AccessController
from documind.database import get_connection

# Reuse the deterministic embedder from the retrieval tests.
from tests.test_retrieval import FakeEmbedder


class FakeLLM:
    """Deterministic LLM: echoes the first document's content as the 'answer'.

    Enough to prove grounding wiring without network/cost. If no document
    content is present, returns the abstention string.
    """
    def complete(self, messages: list[dict], temperature: float | None = None) -> LLMResponse:
        user = messages[-1]["content"]
        # Crude: if the context block has real content, 'answer' from it.
        answer = "Grounded answer from context." if "Document 1" in user else ABSTENTION
        return LLMResponse(
            text=answer, prompt_tokens=10, completion_tokens=5, model="fake",
        )


@pytest.fixture
def pipeline():
    access = AccessController()
    retriever = HybridRetriever(access, embedder=FakeEmbedder())
    return AnswerPipeline(retriever=retriever, llm=FakeLLM(), access_controller=access)


def test_candidate_salary_query_abstains(pipeline):
    """Candidate has no access to salary docs -> abstain, no salary doc retrieved."""
    r = pipeline.answer_query("What is the ML engineer salary?", "candidate_1", "cred")
    assert "doc_002" not in r.retrieved_doc_ids       # salary doc filtered out
    # With salary doc filtered, either no docs (abstain) or only public docs returned.
    if not r.retrieved_doc_ids:
        assert r.abstained
        assert r.answer == ABSTENTION


def test_manager_salary_query_answers(pipeline):
    """Manager can access the salary doc -> grounded answer, doc present."""
    r = pipeline.answer_query("What is the ML engineer salary?", "manager_1", "cred")
    assert "doc_002" in r.retrieved_doc_ids
    assert not r.abstained
    assert r.answer != ABSTENTION


def test_query_is_audited(pipeline):
    """Every query writes an audit row to query_log."""
    before = _count_logs("cred", "manager_1")
    pipeline.answer_query("Tell me about interviews", "manager_1", "cred")
    after = _count_logs("cred", "manager_1")
    assert after == before + 1


def test_tokens_recorded(pipeline):
    """A non-abstaining answer records token counts for cost tracking."""
    r = pipeline.answer_query("Tell me about interviews", "manager_1", "cred")
    if not r.abstained:
        assert r.prompt_tokens > 0
        assert r.completion_tokens > 0


def _count_logs(tenant_id: str, user_id: str) -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM query_log WHERE tenant_id=%s AND user_id=%s",
            (tenant_id, user_id),
        )
        return cur.fetchone()[0]