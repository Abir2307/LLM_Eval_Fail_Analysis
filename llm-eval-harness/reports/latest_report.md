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

## Case Results

| case_id | passed | failure_classification | factuality | format | consistency |
|---|---|---|---:|---:|---:|
| case-1 | true | passed | 1.000 | 1.000 | 0.808 |
| case-2 | true | passed | 1.000 | 1.000 | 0.933 |
| case-3 | false | inconsistent_response | 1.000 | 1.000 | 0.637 |
| case-4 | false | schema_violation | 1.000 | 0.000 | 0.934 |
| case-5 | false | verbosity_exceeded | 1.000 | 1.000 | 0.881 |
| case-6 | false | schema_violation | 0.000 | 0.000 | 1.000 |
| case-7 | true | passed | 1.000 | 1.000 | 0.591 |
