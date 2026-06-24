from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path
import yaml

@dataclass
class TestCase:
    id: str
    question: str
    user_id: str
    tenant_id: str
    role: str
    expected_behavior: Literal["answer", "abstain"]
    expected_facts: list[str] = field(default_factory=list)
    expected_doc_ids: list[str] = field(default_factory=list)

@dataclass
class TestSet:
    version: int
    domain: str
    cases: list[TestCase]

def load_testset(path: str | Path) -> TestSet:
    raw = yaml.safe_load(Path(path).read_text())

    cases = []

    for c in raw["cases"]:
        if(c["expected_behavior"] not in ("answer", "abstain")):
            raise ValueError(
                 f"case {c['id']}: expected_behavior must be 'answer' or 'abstain'"
            )
        
        cases.append(TestCase(
            id=c["id"],
            question=c["question"],
            user_id=c["user_id"],
            tenant_id=c["tenant_id"],
            role=c["role"],
            expected_behavior=c["expected_behavior"],
            expected_facts=c.get("expected_facts", []),
            expected_doc_ids=c.get("expected_doc_ids", []),
        ))

        return TestSet(version=raw["version"], domain=raw["domain"], cases=cases)
