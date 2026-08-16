# EvalKit Report
_2026-08-16T11:35:12.243195+00:00_

## Summary
- Cases: **4**
- Passed: **4** (100%)
- Mean faithfulness: **1.0**
- Mean answer relevance: **0.9153**
- Abstention accuracy: **1.0**
- Mean hallucination rate: **0.0**
- Mean tokens/query (prompt / completion): **1818.75 / 76.5**

## Cases
| Case | Type | Faithfulness | Relevance | Hallucination | Abstention OK | Passed |
|------|------|-------------|-----------|---------------|---------------|--------|
| cred_salary_as_candidate | abstain | — | — | — | ✓ | ✓ |
| cred_interview_topics | answer | 1.00 | 0.85 | 0.00 | — | ✓ |
| cred_salary_as_manager | answer | 1.00 | 0.93 | 0.00 | — | ✓ |
| razorpay_interview_topics | answer | 1.00 | 0.97 | 0.00 | — | ✓ |

## Regression Check
| Metric | Baseline | Current | Δ | Status |
|--------|----------|---------|---|--------|
| mean_faithfulness | 1.0 | 1.0 | +0.0000 | ⚪ flat |
| mean_answer_relevance | 0.9176 | 0.9153 | -0.0023 | ⚪ flat |
| abstention_accuracy | 1.0 | 1.0 | +0.0000 | ⚪ flat |
| pass_rate | 1.0 | 1.0 | +0.0000 | ⚪ flat |

🟢 **No regressions**