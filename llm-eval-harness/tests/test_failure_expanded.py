from llm_eval_harness.failure_analysis import classify_failure


def test_missing_required_fact() -> None:
    # No expected facts found in response
    result = classify_failure(1.0, 1.0, 1.0, "answer without facts", expected_facts=["required"])
    assert result == "missing_required_fact"


def test_schema_violation_on_invalid_json() -> None:
    result = classify_failure(1.0, 0.0, 1.0, "not json", metadata={"expect_json_keys": ["a"]})
    assert result == "schema_violation"


def test_verbosity_exceeded() -> None:
    result = classify_failure(1.0, 1.0, 1.0, "x" * 201, metadata={"max_chars": 200})
    assert result == "verbosity_exceeded"


def test_forbidden_claims_trigger_hallucination() -> None:
    result = classify_failure(1.0, 1.0, 1.0, "This contains forbidden", forbidden_claims=["forbidden"])
    assert result == "hallucination"
