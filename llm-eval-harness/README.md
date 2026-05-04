# LLM Evaluation and Failure Analysis Harness

A compact Python project for evaluating LLM outputs with structured test cases, deterministic scoring, failure classification, logging, and CI automation.

## Why this exists

LLM behavior is often hard to ship safely because quality issues show up as subtle regressions, not obvious crashes. This harness turns prompt quality into a repeatable engineering workflow:

- Run the same prompts multiple times to measure consistency drift.
- Score outputs against explicit requirements (facts, format, schema, verbosity).
- Classify failures into actionable buckets so teams can triage quickly.
- Produce machine-readable report artifacts for CI and release gates.

In short: this project helps move LLM evaluation from ad-hoc spot checks to deterministic, auditable quality checks.

## What it covers

- Factuality checks using expected facts and forbidden claims
- Format compliance checks using regex validation
- Response consistency scoring across repeated runs
- Failure classification for debugging agent outputs
- Pytest-based validation and GitHub Actions CI

## Quick start

```powershell
cd E:\llm-eval-harness
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
pytest
```

## Run the CLI

```powershell
llm-eval --help
```

## End-to-end flow

`cases.json` -> prompt runner -> Mistral API -> response capture -> evaluation engine -> failure classification + logs -> report artifact

## Architecture

```text
cases.json
	↓
Prompt Runner / Model API
	↓
Response Collection
	↓
Evaluation Engine
	├── factuality scoring
	├── format validation
	├── consistency scoring
	↓
Failure Classification
	↓
Logs + Reports + CI artifacts
```

## Testing Strategy

This project uses two layers of validation:

### 1. Code Regression Tests
Ensures evaluation logic remains stable across code changes.

Covered by:
- test_evaluator.py
- test_cli.py
- test_failure_analysis.py
- test_integration.py

Validates:
- scoring logic
- CLI behavior
- report generation
- end-to-end evaluation flow

Run locally:
```powershell
pytest
```

### 2. Runtime Prompt Evaluation
Evaluates live/current LLM outputs against structured cases in `cases.json`.

Checks:
- factuality / forbidden claims
- schema compliance
- formatting constraints
- consistency across repeated runs

Example:
```powershell
llm-eval --cases cases.json --generate-responses --runs 3 --report reports/latest_report.md
```

## Testing Strategy

This project uses two layers of validation:

### 1. Code Regression Tests
Ensures evaluation logic remains stable across code changes.

Covered by:
- test_evaluator.py
- test_cli.py
- test_failure_analysis.py
- test_integration.py

Validates:
- scoring logic
- CLI behavior
- report generation
- end-to-end evaluation flow

Run locally:
```powershell
pytest
```

### 2. Runtime Prompt Evaluation
Evaluates live/current LLM outputs against structured cases in `cases.json`.

Checks:
- factuality / forbidden claims
- schema compliance
- formatting constraints
- consistency across repeated runs

Example:
```powershell
llm-eval --cases cases.json --generate-responses --runs 3 --report reports/latest_report.md
```

## Sample report output

Example excerpt from `reports/latest_report.md`:

```markdown
# LLM Eval Report

- Total cases: 7
- Passed: 3
- Failed: 4

## Failure Distribution
- inconsistent_response: 1
- passed: 3
- schema_violation: 2
- verbosity_exceeded: 1

## Average Scores
- Avg factuality: 0.857
- Avg format: 0.714
- Avg consistency: 0.826
```

## Generating model responses (Mistral)

You can optionally have the CLI call a model (Mistral) to generate responses instead of providing them manually.

- Set your API key in an environment variable (do NOT commit your key):

```powershell
$env:MISTRAL_API_KEY = "<your_api_key_here>"
# optionally set a custom API URL
$env:MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
# optionally set model
$env:MISTRAL_MODEL = "mistral-small-latest"
```

- Or use `env/.env` (auto-loaded by the runner):

```env
MISTRAL_API_KEY=<your_api_key_here>
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_MODEL=mistral-small-latest
```

- Generate responses for `cases.json` (3 runs per case by default):

```powershell
llm-eval --cases path\to\cases.json --generate-responses --runs 3 --save-responses path\to\responses.generated.json
```

- Generate responses and save an artifact report in one command:

```powershell
llm-eval --cases path\to\cases.json --generate-responses --runs 3 --report reports\latest_report.json
```

- Save a Markdown summary report (useful for human-readable CI artifacts):

```powershell
llm-eval --cases path\to\cases.json --generate-responses --runs 3 --report reports\latest_report.md
```

- The CLI will write a JSON mapping of `case_id` → list of generated responses. Then run the evaluation using that file:

```powershell
llm-eval --cases path\to\cases.json --responses path\to\responses.generated.json
```

- Evaluate existing responses and export a report artifact:

```powershell
llm-eval --cases path\to\cases.json --responses path\to\responses.generated.json --report reports\latest_report.json
```

## Cases format

Each case is a JSON object in `cases.json`.

```json
{
	"case_id": "case-1",
	"prompt": "Summarize the policy in exactly one line. Start with 'Summary:' and include 'approval'.",
	"expected_facts": ["approval"],
	"forbidden_claims": ["guaranteed"],
	"expected_format_regex": "Summary: .+",
	"metadata": {
		"consistency_threshold": 0.55,
		"factuality_threshold": 0.8,
		"max_chars": 500,
		"expect_json_keys": ["status", "reason"]
	}
}
```

Common metadata keys:
- `consistency_threshold`: per-case threshold for repeated-run similarity checks.
- `factuality_threshold`: per-case threshold for factuality score.
- `max_chars`: classify as `verbosity_exceeded` when response is too long.
- `expect_json_keys`: used for schema checks when JSON output is expected.

## CI artifact example

In CI, run and upload `reports/latest_report.json` (or `.md`) as an artifact.

```powershell
llm-eval --cases cases.json --generate-responses --runs 3 --report reports/latest_report.json
```

Security: keep your API key in environment variables and never paste it into source or commit history.

## Future Improvements

- Add semantic similarity scoring using embeddings
- Add dashboard for historical evaluation trends
- Add regression testing for prompt versions

## Project layout

- `src/llm_eval_harness/` contains the evaluation logic and logging helpers.
- `tests/` contains the pytest suite.
- `.github/workflows/ci.yml` runs the test suite in GitHub Actions.
