from dataclasses import dataclass
from evalkit.runner import EvalRecord
from ragas.metrics import faithfulness, answer_relevancy
from ragas import evaluate
from datasets import Dataset
from evalkit.retrieval_metrics import score_retrieval
from evalkit.hallucination import detect_hallucinations
from documind.database import get_connection


@dataclass 
class CaseScore:
    case_id: str
    expected_behavior: str
    abstention_correct: bool | None = None
    faithfulness: float | None = None
    answer_relevance: float | None = None
    context_precision: float | None = None   
    context_recall: float | None = None      
    hallucination_rate: float | None = None 
    hallucination_claims: list[dict] | None = None
    passed: bool = False

def _fetch_context(tenant_id: str, doc_ids: list[str]) -> list[str]:
    if not doc_ids:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT content FROM documents "
            "WHERE tenant_id = %s AND document_id = ANY(%s)",
            (tenant_id, doc_ids),
        )
        return [row[0] for row in cur.fetchall()]

def score_records(records: list[EvalRecord]) -> list[CaseScore]:
    scores: list[CaseScore] = []

    answer_records = [r for r in records if r.case.expected_behavior == "answer"]
    abstain_records = [r for r in records if r.case.expected_behavior == "abstain"]

    retrieval_by_id = {score_retrieval(r.case.expected_doc_ids, r.retrieved_doc_ids)  for r in records}

    for r in abstain_records:
        rscore = retrieval_by_id[r.case.id]
        scores.append(CaseScore(
            case_id=r.case.id,
            expected_behavior="abstain",
            abstention_correct=r.abstained,
            context_precision=rscore.precision,  
            context_recall=rscore.recall,
            passed=r.abstained,
        ))

    if answer_records:
        contexts = {
            r.case.id: _fetch_context(r.case.tenant_id, r.retrieved_doc_ids)
            for r in answer_records
        }

        ragas_scores = _run_ragas(answer_records)

        for r, s in zip(answer_records, ragas_scores):
            ctx = contexts[r.case.id]
            faith = s["faithfulness"]
            rel = s["answer_relevancy"]
            passed = (faith >= 0.80) and (rel >= 0.75)
            verdict = detect_hallucinations(r.answer, ctx)
            rscore = retrieval_by_id[r.case.id]
            scores.append(CaseScore(
                case_id=r.case.id,
                expected_behavior="answer",
                faithfulness=faith,
                answer_relevance=rel,
                context_precision=rscore.precision,
                context_recall=rscore.recall,
                hallucination_rate=round(verdict.rate, 4),
                hallucination_claims=[c.model_dump() for c in verdict.claims],
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