import json
from pathlib import Path

from llm_eval_harness.cli import _render_markdown_report, _write_report, build_parser


def test_write_report_json(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "latest_report.json"
    results = [
        {
            "case_id": "case-1",
            "passed": True,
            "failure_classification": "passed",
            "factuality_score": 1.0,
            "format_score": 1.0,
            "consistency_score": 1.0,
        }
    ]

    _write_report(report_path, results)

    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    assert loaded["summary"]["total_cases"] == 1
    assert loaded["summary"]["failure_distribution"]["passed"] == 1
    assert loaded["results"][0]["case_id"] == "case-1"
    assert loaded["results"][0]["passed"] is True


def test_write_report_markdown(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "latest_report.md"
    results = [
        {
            "case_id": "case-1",
            "passed": False,
            "failure_classification": "inconsistent_response",
            "factuality_score": 1.0,
            "format_score": 1.0,
            "consistency_score": 0.5,
        }
    ]

    _write_report(report_path, results)

    text = report_path.read_text(encoding="utf-8")
    assert "# LLM Eval Report" in text
    assert "## Failure Distribution" in text
    assert "## Average Scores" in text
    assert "| case-1 | false | inconsistent_response |" in text


def test_parser_allows_generate_without_responses() -> None:
    parser = build_parser()
    args = parser.parse_args(["--cases", "cases.json", "--generate-responses", "--runs", "3"])
    assert str(args.cases) == "cases.json"
    assert args.generate_responses is True
    assert args.responses is None


def test_render_markdown_report_counts() -> None:
    results = [
        {
            "case_id": "a",
            "passed": True,
            "failure_classification": "passed",
            "factuality_score": 1.0,
            "format_score": 1.0,
            "consistency_score": 1.0,
        },
        {
            "case_id": "b",
            "passed": False,
            "failure_classification": "format_noncompliance",
            "factuality_score": 1.0,
            "format_score": 0.0,
            "consistency_score": 1.0,
        },
    ]

    md = _render_markdown_report(results)
    assert "- Total cases: 2" in md
    assert "- Passed: 1" in md
    assert "- Failed: 1" in md
    assert "- format_noncompliance: 1" in md
    assert "- passed: 1" in md
    assert "- Avg factuality: 1.000" in md
    assert "- Avg format: 0.500" in md
    assert "- Avg consistency: 1.000" in md
