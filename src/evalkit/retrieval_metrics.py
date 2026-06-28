from dataclasses import dataclass

@dataclass
class RetrievalScore:
    precision: float | None
    recall: float | None

def score_retrieval(expected: list[str], retrieved: list[str]) -> RetrievalScore:
    if not retrieved:
        return RetrievalScore(precision=None, recall=None)
    
    retrieved_set = set(retrieved)
    expected_set = set(expected)

    hit = retrieved_set & expected_set

    precision = len(hit) / len(retrieved_set) if retrieved_set else 0.0
    recall = len(hit) / len(expected_set)

    return RetrievalScore(
        precision= precision,
        recall=recall
    )