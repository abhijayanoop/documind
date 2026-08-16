import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from statistics import mean
from evalkit.metrics import CaseScore
from evalkit.runner import EvalRecord


@dataclass
class EvalSummary:
    timestamp: str
    total_cases: int
    passed: int
    pass_rate: float
    mean_faithfulness: float | None
    mean_answer_relevance: float | None
    abstention_accuracy: float | None
    mean_hallucination_rate: float | None = None
    mean_prompt_tokens: float | None = None
    mean_completion_tokens: float | None = None


def summarize(scores: list[CaseScore], records: list[EvalRecord] | None = None) -> EvalSummary:
    answer_scores = [s for s in scores if s.expected_behavior == "answer"]
    abstain_scores = [s for s in scores if s.expected_behavior == "abstain"]

    faiths = [s.faithfulness for s in answer_scores if s.faithfulness is not None]
    rels = [s.answer_relevance for s in answer_scores if s.answer_relevance is not None]
    absts = [s.abstention_correct for s in abstain_scores if s.abstention_correct is not None]
    halluc = [s.hallucination_rate for s in scores if s.hallucination_rate is not None]

    records = records or []
    prompt_toks = [r.prompt_tokens for r in records]
    completion_toks = [r.completion_tokens for r in records]

    return EvalSummary(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_cases=len(scores),
        passed=sum(1 for s in scores if s.passed),
        pass_rate=round(mean([1.0 if s.passed else 0.0 for s in scores]), 4) if scores else 0.0,
        mean_faithfulness=round(mean(faiths), 4) if faiths else None,
        mean_answer_relevance=round(mean(rels), 4) if rels else None,
        abstention_accuracy=round(mean([1.0 if a else 0.0 for a in absts]), 4) if absts else None,
        mean_hallucination_rate=round(mean(halluc), 4) if halluc else None,
        mean_prompt_tokens=round(mean(prompt_toks), 2) if prompt_toks else None,
        mean_completion_tokens=round(mean(completion_toks), 2) if completion_toks else None,
    )


def write_json(scores: list[CaseScore], summary: EvalSummary, path: str) -> None:
    payload = {
        "summary": asdict(summary),
        "cases": [asdict(s) for s in scores],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def to_markdown(scores: list[CaseScore], summary: EvalSummary) -> str:
    lines = [
        "# EvalKit Report",
        f"_{summary.timestamp}_",
        "",
        "## Summary",
        f"- Cases: **{summary.total_cases}**",
        f"- Passed: **{summary.passed}** ({summary.pass_rate:.0%})",
        f"- Mean faithfulness: **{summary.mean_faithfulness}**",
        f"- Mean answer relevance: **{summary.mean_answer_relevance}**",
        f"- Abstention accuracy: **{summary.abstention_accuracy}**",
        f"- Mean hallucination rate: **{summary.mean_hallucination_rate}**",
        f"- Mean tokens/query (prompt / completion): **{summary.mean_prompt_tokens} / {summary.mean_completion_tokens}**",
        "",
        "## Cases",
        "| Case | Type | Faithfulness | Relevance | Hallucination | Abstention OK | Passed |",
        "|------|------|-------------|-----------|---------------|---------------|--------|",
    ]
    for s in scores:
        faith = "—" if s.faithfulness is None else f"{s.faithfulness:.2f}"
        rel = "—" if s.answer_relevance is None else f"{s.answer_relevance:.2f}"
        halluc = "—" if s.hallucination_rate is None else f"{s.hallucination_rate:.2f}"
        ab = "—" if s.abstention_correct is None else ("✓" if s.abstention_correct else "✗")
        ok = "✓" if s.passed else "✗"
        lines.append(f"| {s.case_id} | {s.expected_behavior} | {faith} | {rel} | {halluc} | {ab} | {ok} |")
    return "\n".join(lines)