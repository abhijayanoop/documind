# EvalKit Report
_2026-07-02T19:42:22.368723+00:00_

## Summary
- Cases: **4**
- Passed: **4** (100%)
- Mean faithfulness: **1.0**
- Mean answer relevance: **0.892**
- Abstention accuracy: **1.0**

## Cases
| Case | Type | Faithfulness | Relevance | Abstention OK | Passed |
|------|------|-------------|-----------|---------------|--------|
| cred_salary_as_candidate | abstain | — | — | ✓ | ✓ |
| cred_interview_topics | answer | 1.00 | 0.80 | — | ✓ |
| cred_salary_as_manager | answer | 1.00 | 0.94 | — | ✓ |
| razorpay_interview_topics | answer | 1.00 | 0.94 | — | ✓ |

## Regression Check
| Metric | Baseline | Current | Δ | Status |
|--------|----------|---------|---|--------|
| mean_faithfulness | 0.8889 | 1.0 | +0.1111 | 🟢 improved |
| mean_answer_relevance | 0.892 | 0.892 | +0.0000 | ⚪ flat |
| abstention_accuracy | 1.0 | 1.0 | +0.0000 | ⚪ flat |
| pass_rate | 0.75 | 1.0 | +0.2500 | 🟢 improved |

🟢 **No regressions**