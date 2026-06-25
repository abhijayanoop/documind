from dataclasses import dataclass
from evalkit.runner import EvalRecord
from ragas.metrics import faithfulness, answer_relevancy
from ragas import evaluate
from datasets import Dataset

@dataclass 
class CaseScore:
    case_id: str
    expected_behavior: str
    abstention_correct: bool | None = None
    faithfulness: float | None = None
    answer_relevance: float | None = None
    passed: bool = False

def score_records(records: list[EvalRecord]) -> list[CaseScore]:
    scores: list[CaseScore] = []

    answer_records = [r for r in records if r.case.expected_behavior == "answer"]
    abstain_records = [r for r in records if r.case.expected_behavior == "abstain"]

    for r in abstain_records:
        correct = r.abstained
        scores.append(CaseScore(
            case_id=r.case.id,
            expected_behavior="abstain",
            abstention_correct=correct,
            passed=correct,
        ))

    if answer_records:
        ragas_scores = _run_ragas(answer_records)
        for r, s in zip(answer_records, ragas_scores):
            faith = s["faithfulness"]
            rel = s["answer_relevancy"]
            passed = (faith >= 0.80) and (rel >= 0.75)
            scores.append(CaseScore(
                case_id=r.case.id,
                expected_behavior="answer",
                faithfulness=faith,
                answer_relevance=rel,
                passed=passed,
            ))
    
    return scores

def _run_ragas(records: list[EvalRecord]) -> list[dict]:
    from documind.database import get_connection

    context: list[list[str]] = []

    for r in records:
        if r.retrieved_doc_ids:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT content FROM documents WHERE tenant_id=%s AND document_id=ANY(%s)", 
                                (r.case.tenant_id, r.retrieved_doc_ids))
                    rows = cur.fetchall()
                    context.append([row[0] for row in rows])
        else:
            context.append([])

    dataset = Dataset.from_dict({
        "question": [r.case.question for r in records],
        "answer": [r.answer for r in records],
        "contexts": context,
        "ground_truth": [" ".join(r.case.expected_facts) for r in records],
    })

    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
    df = result.to_pandas()
    return df.to_dict("records")