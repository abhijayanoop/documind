from typing import Protocol
from documind.config import settings
import litellm

class Embedder(Protocol):
    def embed(self, texts: list[str])->list[list[float]]:
        ...

class LiteLLMEmbedder:
    def __init__(self, model: str | None = None):
        self.model = model or settings.embedding_model

    def embed(self, texts: list[str])->list[list[float]]:
        if not texts:
            return []
        
        response = litellm.embedding(model=settings.embedding_model, input=texts, api_key=settings.openai_api_key or None)
        # litellm normalizes provider responses to a common shape:
        # response.data is a list of {"embedding": [...], "index": i}
        # Sort by index to guarantee input order is preserved.
        items = sorted(response.data, key=lambda d: d["index"])
        return [item["embedding"] for item in items]
    
    def embed_one(self, text: str)->list[float]:
        return self.embed([text])[0]
