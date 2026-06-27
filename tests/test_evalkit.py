import pytest
from documind.pipeline import AnswerResult
from evalkit.testset import TestCase, TestSet
from evalkit.runner import EvalRunner, EvalRecord
from evalkit.metrics import score_records, CaseScore
from evalkit.report import summarize


class FakePipeline:
    """Returns canned AnswerResults keyed by expected behavior — no network."""
    def answer_query(self, question, user_id, tenant_id, top_k=5):
        # Candidate salary query -> abstain; everything else -> a grounded-looking answer.
        if user_id == "candidate_1" and "earn" in question:
            return AnswerResult(answer="I don't have information about that in the documents available to you.",
                                retrieved_doc_ids=[], abstained=True)
        return AnswerResult(
            answer="Study consensus algorithms.",
            retrieved_doc_ids=["doc_001"],
            abstained=False,
            prompt_tokens=12, completion_tokens=6, model="fake",
        )


def _case(cid, q, uid, beh):
    return TestCase(id=cid, question=q, user_id=uid, tenant_id="cred",
                    role="candidate", expected_behavior=beh)


def test_runner_uses_case_identity():
    runner = EvalRunner(pipeline=FakePipeline())
    rec = runner.run_case(_case("c1", "What do ML engineers earn?", "candidate_1", "abstain"))
    assert rec.abstained is True
    assert rec.retrieved_doc_ids == []


def test_abstention_scored_correct_when_abstains():
    rec = EvalRecord(
        case=_case("c1", "What do ML engineers earn?", "candidate_1", "abstain"),
        answer="I don't have information about that in the documents available to you.",
        retrieved_doc_ids=[], abstained=True, prompt_tokens=0, completion_tokens=0,
    )
    scores = score_records([rec])
    assert scores[0].abstention_correct is True
    assert scores[0].passed is True


def test_abstention_scored_wrong_when_answers():
    """An abstention case that DIDN'T abstain is a failure."""
    rec = EvalRecord(
        case=_case("c1", "What do ML engineers earn?", "candidate_1", "abstain"),
        answer="They earn 25-35 LPA.",       # leaked! should have abstained
        retrieved_doc_ids=["doc_002"], abstained=False, prompt_tokens=5, completion_tokens=3,
    )
    scores = score_records([rec])
    assert scores[0].abstention_correct is False
    assert scores[0].passed is False


def test_summary_aggregates():
    scores = [
        CaseScore(case_id="a", expected_behavior="answer", faithfulness=0.9, answer_relevance=0.8, passed=True),
        CaseScore(case_id="b", expected_behavior="abstain", abstention_correct=True, passed=True),
    ]
    s = summarize(scores)
    assert s.total_cases == 2
    assert s.passed == 2
    assert s.pass_rate == 1.0
    assert s.mean_faithfulness == 0.9
    assert s.abstention_accuracy == 1.0