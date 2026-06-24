from documind.pipeline import AnswerPipeline
from evalkit.testset import TestCase, TestSet
from dataclasses import dataclass

@dataclass
class EvalRecord:
    case: TestCase
    answer: str
    retrieved_doc_ids: list[str]
    abstained: bool
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

class EvalRunner:
    def __init__(self, pipeline: AnswerPipeline | None = None):
        self.pipeline = pipeline or AnswerPipeline()

    def run_case(self, case: TestCase) -> EvalRecord:
        result = self.pipeline.answer_query(case.question, case.user_id, case.tenant_id)

        return EvalRecord(
            case=case,
            answer=result.answer,
            retrieved_doc_ids=result.retrieved_doc_ids,
            abstained=result.abstained,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
        )
    
    def run(self, testset: TestSet) -> list[EvalRecord]:
        records = []
        for case in testset.cases: 
            print(f"  running {case.id} ...")
            records.append(self.run_case(case))
        return records