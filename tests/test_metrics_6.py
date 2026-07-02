import json
import pytest
from evalkit.retrieval_metrics import score_retrieval
from evalkit.hallucination import HallucinationVerdict, ClaimVerdict
from evalkit.report import EvalSummary
from evalkit import baseline as bl
from evalkit.regression import detect_regressions


def test_retrieval_precision_recall():
    s = score_retrieval(["doc_001", "doc_004"], ["doc_001"])
    assert s.precision == 0.5 and s.recall == 1.0
    s = score_retrieval(["doc_001"], ["doc_001", "doc_002"])
    assert s.precision == 1.0 and s.recall == 0.5


def test_retrieval_abstention_is_none():
    s = score_retrieval([], [])
    assert s.precision is None and s.recall is None


def test_hallucination_rate_math():
    v = HallucinationVerdict(claims=[
        ClaimVerdict(claim="a", supported=True, reason=""),
        ClaimVerdict(claim="b", supported=False, reason=""),
        ClaimVerdict(claim="c", supported=False, reason=""),
    ])
    assert v.total == 3 and v.unsupported == 2
    assert round(v.rate, 4) == round(2 / 3, 4)


def test_no_baseline_is_clean(tmp_path, monkeypatch):
    # Point baseline at an empty temp dir -> no baseline file.
    monkeypatch.setattr(bl, "BASELINE_PATH", tmp_path / "baseline.json")
    summary = EvalSummary("t", 2, 2, 1.0, 0.9, 0.85, 1.0)
    report = detect_regressions(summary)
    assert report.has_regression is False
    assert report.deltas == []


def test_regression_flagged(tmp_path, monkeypatch):
    bpath = tmp_path / "baseline.json"
    monkeypatch.setattr(bl, "BASELINE_PATH", bpath)
    # Baseline with high faithfulness.
    bpath.write_text(json.dumps({"summary": {
        "mean_faithfulness": 0.90, "mean_answer_relevance": 0.85,
        "abstention_accuracy": 1.0, "pass_rate": 1.0,
    }}))
    # Current run drops faithfulness well beyond tolerance.
    current = EvalSummary("t", 2, 1, 0.5, 0.70, 0.85, 1.0)
    report = detect_regressions(current)
    assert report.has_regression is True
    faith = next(d for d in report.deltas if d.metric == "mean_faithfulness")
    assert faith.regressed is True


def test_abstention_regression_zero_tolerance(tmp_path, monkeypatch):
    """Any drop in abstention accuracy is a regression — security never regresses."""
    bpath = tmp_path / "baseline.json"
    monkeypatch.setattr(bl, "BASELINE_PATH", bpath)
    bpath.write_text(json.dumps({"summary": {
        "mean_faithfulness": 0.90, "mean_answer_relevance": 0.85,
        "abstention_accuracy": 1.0, "pass_rate": 1.0,
    }}))
    current = EvalSummary("t", 2, 2, 1.0, 0.90, 0.85, 0.99)  # tiny abstention drop
    report = detect_regressions(current)
    assert report.has_regression is True   # zero tolerance -> flagged