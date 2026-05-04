from llm_eval_harness.evaluator import evaluate_case, evaluate_suite
from llm_eval_harness.models import EvaluationCase


def test_evaluate_case_passes_on_expected_content() -> None:
    case = EvaluationCase(
        case_id="case-1",
        prompt="Summarize the policy",
        expected_facts=["policy requires approval"],
        expected_format_regex=r"Summary: .+",
    )

    result = evaluate_case(case, "Summary: policy requires approval")

    assert result.passed is True
    assert result.failure_classification == "passed"
    assert result.format_score == 1.0
    assert result.factuality_score == 1.0


def test_evaluate_case_detects_format_failure() -> None:
    case = EvaluationCase(
        case_id="case-2",
        prompt="Return a labeled summary",
        expected_facts=["approval"],
        expected_format_regex=r"Summary: .+",
    )

    result = evaluate_case(case, "approval only")

    assert result.passed is False
    assert result.failure_classification == "format_noncompliance"
    assert result.format_score == 0.0


def test_evaluate_suite_requires_all_responses() -> None:
    case = EvaluationCase(case_id="case-3", prompt="Answer")

    results = evaluate_suite([case], {"case-3": "Answer"})

    assert len(results) == 1
    assert results[0].case_id == "case-3"


def test_evaluate_case_respects_metadata_consistency_threshold() -> None:
    case = EvaluationCase(
        case_id="case-4",
        prompt="One-line summary",
        expected_facts=["approval"],
        expected_format_regex=r"Summary: .+",
        metadata={"consistency_threshold": 0.5},
    )

    result = evaluate_case(
        case,
        "Summary: approval is needed.",
        peer_responses=["Summary: approval needed.", "Summary: prior approval is required."],
    )

    assert result.consistency_score >= 0.5
    assert result.failure_classification == "passed"
