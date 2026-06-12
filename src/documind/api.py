from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from documind.pipeline import AnswerPipeline
from documind.auth import Principal, decode_access_token, AuthError

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

@app.get("/health")
def get_heath():
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

