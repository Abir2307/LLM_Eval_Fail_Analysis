from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from .evaluator import evaluate_suite
from .models import EvaluationCase


def _load_cases(path: Path) -> list[EvaluationCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvaluationCase(**item) for item in data]


def _load_responses(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_summary_stats(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed

    failures = Counter(str(r.get("failure_classification", "unknown")) for r in results)

    def _avg(key: str) -> float:
        if not results:
            return 0.0
        return round(sum(float(r.get(key, 0.0)) for r in results) / len(results), 3)

    return {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "failure_distribution": dict(failures),
        "average_scores": {
            "factuality": _avg("factuality_score"),
            "format": _avg("format_score"),
            "consistency": _avg("consistency_score"),
        },
    }


def _render_markdown_report(results: list[dict]) -> str:
    summary = _compute_summary_stats(results)

    lines = [
        "# LLM Eval Report",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "## Failure Distribution",
    ]

    for name, count in sorted(summary["failure_distribution"].items()):
        lines.append(f"- {name}: {count}")

    avg = summary["average_scores"]
    lines.extend(
        [
            "",
            "## Average Scores",
            f"- Avg factuality: {avg['factuality']:.3f}",
            f"- Avg format: {avg['format']:.3f}",
            f"- Avg consistency: {avg['consistency']:.3f}",
            "",
            "## Case Results",
            "",
            "| case_id | passed | failure_classification | factuality | format | consistency |",
            "|---|---|---|---:|---:|---:|",
        ]
    )

    for r in results:
        lines.append(
            "| {case_id} | {passed} | {failure} | {factuality:.3f} | {format:.3f} | {consistency:.3f} |".format(
                case_id=r.get("case_id", ""),
                passed=str(bool(r.get("passed"))).lower(),
                failure=r.get("failure_classification", ""),
                factuality=float(r.get("factuality_score", 0.0)),
                format=float(r.get("format_score", 0.0)),
                consistency=float(r.get("consistency_score", 0.0)),
            )
        )
    return "\n".join(lines) + "\n"


def _write_report(report_path: Path, results: list[dict]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.suffix.lower() in {".md", ".markdown"}:
        report_path.write_text(_render_markdown_report(results), encoding="utf-8")
        return
    payload = {
        "summary": _compute_summary_stats(results),
        "results": results,
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LLM evaluation cases.")
    parser.add_argument("--cases", type=Path, help="Path to a JSON array of evaluation cases.")
    parser.add_argument("--responses", type=Path, help="Path to a JSON object keyed by case_id.")
    parser.add_argument(
        "--generate-responses",
        action="store_true",
        help="Call a model API to generate responses for cases (writes responses file).",
    )
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per case when generating responses.")
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="MISTRAL_API_KEY",
        help="Environment variable name that stores the Mistral API key.",
    )
    parser.add_argument(
        "--api-url-env",
        type=str,
        default="MISTRAL_API_URL",
        help="Environment variable name for the Mistral API base URL (optional).",
    )
    parser.add_argument(
        "--save-responses",
        type=Path,
        help="If generating responses, path to write the resulting JSON mapping.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path to save evaluation report (.json or .md).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.cases:
        parser.print_help()
        return 0

    if not args.generate_responses and not args.responses:
        parser.print_help()
        return 0

    # Optionally generate responses by calling a model API
    if args.generate_responses:
        from .prompt_runner import run_prompts

        save_path = args.save_responses or (args.cases.parent / "responses.generated.json")
        run_prompts(
            args.cases,
            runs=args.runs,
            api_key_env=args.api_key_env,
            api_url_env=args.api_url_env,
            save_responses=save_path,
        )
        args.responses = save_path

    cases = _load_cases(args.cases)
    responses = _load_responses(args.responses)
    results = evaluate_suite(cases, responses)
    results_dict = [asdict(result) for result in results]
    if args.report:
        _write_report(args.report, results_dict)
    print(json.dumps(results_dict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
