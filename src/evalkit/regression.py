from dataclasses import dataclass
from evalkit.report import EvalSummary
from evalkit.baseline import load_baseline

DEFAULT_TOLERANCE = {
    "mean_faithfulness": 0.03,
    "mean_answer_relevance": 0.03,
    "abstention_accuracy": 0.0,    
    "pass_rate": 0.0,
}


@dataclass
class MetricDelta:
    metric: str
    baseline: float | None
    current: float | None
    delta: float | None
    regressed: bool


@dataclass
class RegressionReport:
    deltas: list[MetricDelta]
    has_regression: bool


def detect_regressions(current: EvalSummary, tolerance: dict | None = None) -> RegressionReport:
    """Compare current run to the saved baseline. Flags drops beyond tolerance."""
    tol = tolerance or DEFAULT_TOLERANCE
    base = load_baseline()

    if base is None:
        return RegressionReport(deltas=[], has_regression=False)

    base_summary = base["summary"]
    deltas: list[MetricDelta] = []
    has_regression = False

    for metric, allowed_drop in tol.items():
        b = base_summary.get(metric)
        c = getattr(current, metric, None)
        if b is None or c is None:
            deltas.append(MetricDelta(metric, b, c, None, regressed=False))
            continue
        delta = round(c - b, 4)
        regressed = delta < -allowed_drop      # dropped more than tolerance
        if regressed:
            has_regression = True
        deltas.append(MetricDelta(metric, b, c, delta, regressed))

    return RegressionReport(deltas=deltas, has_regression=has_regression)


def format_regression_md(report: RegressionReport) -> str:
    if not report.deltas:
        return "_No baseline to compare against (first run)._"
    lines = [
        "## Regression Check",
        "| Metric | Baseline | Current | Δ | Status |",
        "|--------|----------|---------|---|--------|",
    ]
    for d in report.deltas:
        if d.delta is None:
            status, delta_s = "—", "—"
        elif d.regressed:
            status, delta_s = "🔴 REGRESSED", f"{d.delta:+.4f}"
        elif d.delta > 0:
            status, delta_s = "🟢 improved", f"{d.delta:+.4f}"
        else:
            status, delta_s = "⚪ flat", f"{d.delta:+.4f}"
        lines.append(f"| {d.metric} | {d.baseline} | {d.current} | {delta_s} | {status} |")
    verdict = "🔴 **REGRESSION DETECTED**" if report.has_regression else "🟢 **No regressions**"
    lines += ["", verdict]
    return "\n".join(lines)