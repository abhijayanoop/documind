from dataclasses import dataclass
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI
from documind.config import settings

class ClaimVerdict(BaseModel):
    claim: str = Field(description="A single factual claim extracted from the answer")
    supported: bool = Field(description="True if the claim is supported by the context")
    reason: str = Field(description="Brief reason for the verdict")

class HallucinationVerdict(BaseModel):
    claims: list[ClaimVerdict]

    @property
    def total(self) -> int:
        return len(self.claims)

    @property
    def unsupported(self) -> int:
        return sum(1 for c in self.claims if not c.supported)

    @property
    def rate(self) -> float:
        return self.unsupported / self.total if self.total else 0.0
    
_client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))

def detect_hallucinations(answer: str, context: list[str], model: str | None = None) -> HallucinationVerdict:
    context_block = "\n\n".join(context) if context else "(no context provided)"

    verdict = _client.chat.completions.create(
        model=model or settings.llm_model,
        response_model=HallucinationVerdict,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict fact-checker. Extract each discrete factual claim "
                    "from the ANSWER. For each claim, decide if it is directly supported by "
                    "the CONTEXT. Be especially strict about numbers, figures, and named "
                    "policies — if a number is not in the context, it is unsupported. "
                    "Do not use outside knowledge."
                ),
            },
            {
                "role": "user",
                "content": f"CONTEXT:\n{context_block}\n\nANSWER:\n{answer}",
            },
        ],
    )
    return verdict