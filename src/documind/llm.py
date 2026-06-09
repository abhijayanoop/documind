from dataclasses import dataclass
from typing import Protocol
from documind.config import settings
import litellm

@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str

    @property
    def total_tokens(self)->int:
        return self.prompt_tokens + self.completion_tokens
    
class LLMClient(Protocol):
    def complete(self, messages: list[dict], temperature: float | None = None)->LLMResponse:
        ...

class LiteLLMClient:
    def __init__(self, model: str | None = None):
        self.model = model or settings.llm_model

    def complete(self, messages: list[dict], temperature: float | None = None)->LLMResponse:
        temperature = settings.llm_temperature if temperature is None else temperature
        response = litellm.completion(model=self.model, messages=messages, temperature=temperature, api_key=settings.openai_api_key or None)
        usage = response.usage
        return LLMResponse(text=response.choices[0].message.content, prompt_tokens=usage.prompt_tokens, completion_tokens=usage.completion_tokens, model=self.model)