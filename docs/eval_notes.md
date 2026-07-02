## Judge Variance Observation (2026-07-02)

RAGAS faithfulness scored `cred_salary_as_manager` at 0.67 on one run despite
the answer being fully grounded (verified via manual inspection and EvalKit's
dedicated hallucination judge, which returned 0.0 hallucination rate with both
claims marked supported). A re-run with no code changes scored the same case
at 1.00. This is documented LLM-as-judge variance, not a system defect — the
reason EvalKit cross-checks RAGAS faithfulness against an independent
hallucination judge rather than trusting a single score.
