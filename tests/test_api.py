import pytest
from fastapi.testclient import TestClient
from documind import api
from documind.auth import create_access_token
from documind.pipeline import AnswerPipeline
from documind.retrieval import HybridRetriever
from documind.rbac import AccessController

# Reuse the deterministic fakes from earlier weeks.
from tests.test_retrieval import FakeEmbedder
from tests.test_pipeline import FakeLLM


@pytest.fixture(autouse=True)
def patch_pipeline():
    """Replace the module-level pipeline with one using fakes (no network)."""
    access = AccessController()
    retriever = HybridRetriever(access, embedder=FakeEmbedder())
    api.pipeline = AnswerPipeline(retriever=retriever, llm=FakeLLM(), access_controller=access)
    yield


@pytest.fixture
def client():
    return TestClient(api.app)


def _auth(user_id, tenant_id, role):
    return {"Authorization": f"Bearer {create_access_token(user_id, tenant_id, role)}"}


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


def test_query_requires_token(client):
    r = client.post("/query", json={"question": "hi"})
    assert r.status_code == 401


def test_query_rejects_tampered_token(client):
    headers = _auth("manager_1", "cred", "hiring_manager")
    headers["Authorization"] = headers["Authorization"][:-2] + "xx"
    r = client.post("/query", json={"question": "hi"}, headers=headers)
    assert r.status_code == 401


def test_candidate_cannot_see_salary_via_http(client):
    r = client.post(
        "/query",
        json={"question": "What is the ML engineer salary?"},
        headers=_auth("candidate_1", "cred", "candidate"),
    )
    assert r.status_code == 200
    assert "doc_002" not in r.json()["retrieved_doc_ids"]


def test_manager_sees_salary_via_http(client):
    r = client.post(
        "/query",
        json={"question": "What is the ML engineer salary?"},
        headers=_auth("manager_1", "cred", "hiring_manager"),
    )
    assert r.status_code == 200
    assert "doc_002" in r.json()["retrieved_doc_ids"]


def test_empty_question_rejected(client):
    r = client.post("/query", json={"question": "   "},
                    headers=_auth("manager_1", "cred", "hiring_manager"))
    assert r.status_code == 422


def test_ingest_requires_admin(client):
    r = client.post(
        "/ingest",
        json={"documents": [{"document_id": "d", "title": "t", "content": "c", "access_level": "public"}]},
        headers=_auth("candidate_1", "cred", "candidate"),
    )
    assert r.status_code == 403