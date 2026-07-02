import json
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone
from evalkit.metrics import CaseScore
from evalkit.report import EvalSummary

RUNS_DIR = Path("eval_runs")
BASELINE_PATH = RUNS_DIR / "baseline.json"


def save_run(scores: list[CaseScore], summary: EvalSummary) -> Path:
    """Persist a run to a timestamped file. Returns the path."""
    RUNS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"run_{stamp}.json"
    payload = {"summary": asdict(summary), "cases": [asdict(s) for s in scores]}
    path.write_text(json.dumps(payload, indent=2))
    return path


def promote_to_baseline(run_path: Path) -> None:
    """Mark a run as the baseline to compare future runs against."""
    RUNS_DIR.mkdir(exist_ok=True)
    BASELINE_PATH.write_text(Path(run_path).read_text())
    print(f"Promoted {run_path.name} to baseline.")


def load_baseline() -> dict | None:
    """Load the current baseline payload, or None if none exists yet."""
    if not BASELINE_PATH.exists():
        return None
    return json.loads(BASELINE_PATH.read_text())