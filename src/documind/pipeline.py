from dataclasses import dataclass, field
from documind.rbac import AccessController
from documind.embeddings import Embedder
from documind.retrieval import HybridRetriever, RetrievedDoc
from documind.llm import LLMClient, LiteLLMClient
from documind.database import log_query
from documind.prompts import ABSTENTION, build_messages
from documind.tracing import observe, update_current_observation

@dataclass
class AnswerResult:
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_titles: list[str] = field(default_factory = list)
    abstained: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""

class AnswerPipeline:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        llm: LLMClient | None = None,
        access_controller: AccessController | None = None,
        embedder: Embedder | None = None,
    ):        
        self.access = access_controller or AccessController()
        self.retriever = retriever or HybridRetriever(access_controller, embedder)
        self.llm = llm or LiteLLMClient()

    @observe(name="answer_query")
    def answer_query(self, query: str, user_id: str, tenant_id: str, top_k: int = 5)->AnswerResult:
        docs: list[RetrievedDoc] = self._retrieve(query, user_id, tenant_id, top_k)

        doc_ids = [doc.document_id for doc in docs]

        log_query(tenant_id, user_id, query, doc_ids)

        if not docs:
            update_current_observation({"abstained": True, "n_docs": 0, "tenant_id": tenant_id})
            return AnswerResult(answer=ABSTENTION, retrieved_doc_ids=[], abstained=True)
        
        response, answer = self._generate(query, docs)
        update_current_observation(
            metadata={
                "answer": answer == ABSTENTION,
                "tenant_id": tenant_id,
                "n_docs": len(docs),
                "retrieved_doc_ids": doc_ids
            },
            usage={
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens
            }
        )

        return AnswerResult(
            answer= answer,
            retrieved_doc_ids=doc_ids,
            retrieved_titles=[doc.title for doc in docs],
            abstained=(answer == ABSTENTION),
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            model=response.model
        )
    
    @observe(name="retrieve")
    def _retrieve(self, query: str, user_id: str, tenant_id: str, top_k: int = 5):
        return self.retriever.retrieve(query, user_id, tenant_id, top_k)

    @observe(name="generate")
    def _generate(self, query: str, docs: list[RetrievedDoc]):
        messages = build_messages(question=query, docs=docs)
        response = self.llm.complete(messages=messages)
        answer = response.text.strip()
        return response, answer