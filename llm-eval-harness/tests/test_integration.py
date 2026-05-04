import json
from pathlib import Path

from llm_eval_harness.cli import _load_cases, _load_responses
from llm_eval_harness.evaluator import evaluate_suite
from llm_eval_harness.models import EvaluationCase


def test_integration_cases_to_results(tmp_path: Path) -> None:
    cases = [
        {
            "case_id": "int-1",
            "prompt": "Summarize",
            "expected_facts": ["must include this fact"],
            "expected_format_regex": r"Summary: .+",
        },
        {
            "case_id": "int-2",
            "prompt": "Return JSON",
            "expected_facts": [],
            "expected_format_regex": r"\{.*\}",
            "metadata": {"expect_json_keys": ["a", "b"]},
        },
    ]

    responses = {
        "int-1": "Summary: must include this fact",
        "int-2": '{"a": 1, "b": 2}',
    }

    cases_file = tmp_path / "cases.json"
    responses_file = tmp_path / "responses.json"
    cases_file.write_text(json.dumps(cases))
    responses_file.write_text(json.dumps(responses))

    loaded = _load_cases(cases_file)
    loaded_responses = _load_responses(responses_file)

    results = evaluate_suite(loaded, loaded_responses)

    assert len(results) == 2
    assert {r.case_id for r in results} == {"int-1", "int-2"}
    # both should pass in this simple happy-path
    assert all(r.passed for r in results)
