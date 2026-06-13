from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from documind.pipeline import AnswerPipeline
from documind.auth import Principal, decode_access_token, AuthError
from documind.ingest import DocumentInput, ingest_documents

app = FastAPI(title="Documind", version="1.0.0")

pipeline = AnswerPipeline()

def get_principal(authorization: str = Header(default="")) -> Principal:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_access_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if(principal.role != "admin"):
        raise HTTPException(403, "Admin role required")
    return principal
    
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_titles: list[str]
    abstained: bool
    model: str
    total_tokens: int

class IngestItem(BaseModel):
    document_id: str
    title: str
    content: str
    access_level: str

class IngestRequest(BaseModel):
    documents: list[IngestItem]

class IngestResponse(BaseModel):
    ingested: int

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, principal: Principal = Depends(get_principal)) -> QueryResponse:
    result = pipeline.answer_query(req.question, principal.user_id, principal.tenant_id, req.top_k)
    return QueryResponse(
        answer=result.answer,
        retrieved_doc_ids=result.retrieved_doc_ids,
        retrieved_titles=result.retrieved_titles,
        abstained=result.abstained,
        model=result.model,
        total_tokens=result.prompt_tokens + result.completion_tokens,
    )

@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest, principal: Principal = Depends(require_admin)) -> IngestResponse:
    docs = [
        DocumentInput(
            tenant_id=principal.tenant_id,   # tenant from token — can't cross-write
            document_id=item.document_id,
            title=item.title,
            content=item.content,
            access_level=item.access_level,
        )
        for item in req.documents
    ]


    n_docs = ingest_documents(docs)
    return IngestResponse(ingested=n_docs)


