import click
from evalkit.testset import load_testset
from evalkit.runner import EvalRunner
from evalkit.metrics import score_records
from evalkit.report import summarize, write_json, to_markdown


@click.command()
@click.option("--testset", default="src/evalkit/testsets/interview_prep.yaml")
@click.option("--json-out", default="eval_report.json")
@click.option("--md-out", default="eval_report.md")
def main(testset: str, json_out: str, md_out: str):
    ts = load_testset(testset)
    print(f"Running {len(ts.cases)} cases over '{ts.domain}' ...")
    records = EvalRunner().run(ts)
    scores = score_records(records)
    summary = summarize(scores)

    write_json(scores, summary, json_out)
    md = to_markdown(scores, summary)
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(md)

    print("\n" + md)
    print(f"\nWrote {json_out} and {md_out}")


if __name__ == "__main__":
    main()