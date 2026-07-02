import click
from evalkit.testset import load_testset
from evalkit.runner import EvalRunner
from evalkit.metrics import score_records
from evalkit.report import summarize, write_json, to_markdown
from evalkit.baseline import save_run, promote_to_baseline
from evalkit.regression import detect_regressions, format_regression_md


@click.command()
@click.option("--testset", default="src/evalkit/testsets/interview_prep.yaml")
@click.option("--promote", is_flag=True, help="Promote this run to the baseline.")
def main(testset: str, promote: bool):
    ts = load_testset(testset)
    print(f"Running {len(ts.cases)} cases over '{ts.domain}' ...")
    records = EvalRunner().run(ts)
    scores = score_records(records)
    summary = summarize(scores)

    run_path = save_run(scores, summary)
    reg = detect_regressions(summary)

    md = to_markdown(scores, summary) + "\n\n" + format_regression_md(reg)
    write_json(scores, summary, "eval_report.json")
    with open("eval_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("\n" + md)

    if promote:
        promote_to_baseline(run_path)

    if reg.has_regression:
        raise SystemExit(1)


if __name__ == "__main__":
    main()