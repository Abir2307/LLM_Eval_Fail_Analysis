from llm_eval_harness.failure_analysis import classify_failure


def test_classify_failure_prioritizes_empty_response() -> None:
    assert classify_failure(0.0, 0.0, 0.0, "   ") == "empty_response"


def test_classify_failure_prioritizes_format() -> None:
    assert classify_failure(1.0, 0.0, 1.0, "hello") == "format_noncompliance"


def test_classify_failure_returns_passed() -> None:
    assert classify_failure(1.0, 1.0, 1.0, "hello") == "passed"
