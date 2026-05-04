from __future__ import annotations

import json
from typing import Iterable


def classify_failure(
    factuality_score: float,
    format_score: float,
    consistency_score: float,
    response: str,
    factuality_threshold: float = 0.8,
    consistency_threshold: float | None = None,
    expected_facts: Iterable[str] | None = None,
    forbidden_claims: Iterable[str] | None = None,
    metadata: dict | None = None,
) -> str:
    """Classify the primary failure mode for a model response.

    Expanded failure classes:
      - empty_response
      - format_noncompliance
      - schema_violation
      - missing_required_fact
      - hallucination
      - verbosity_exceeded
      - inconsistent_response
      - passed
    """
    expected_facts = list(expected_facts or [])
    forbidden_claims = list(forbidden_claims or [])
    metadata = metadata or {}
    if consistency_threshold is None:
        consistency_threshold = factuality_threshold

    if not response.strip():
        return "empty_response"

    # Format problems take precedence; allow schema-specific detection
    if format_score < 1.0:
        # If metadata declares expected JSON keys, try to validate simple schema
        expected_keys = metadata.get("expect_json_keys")
        if expected_keys:
            try:
                parsed = json.loads(response)
                if not set(expected_keys).issubset(set(parsed.keys())):
                    return "schema_violation"
            except Exception:
                return "schema_violation"

        return "format_noncompliance"

    # Verbosity check (optional per-case max_chars)
    max_chars = metadata.get("max_chars")
    if isinstance(max_chars, int) and len(response) > max_chars:
        return "verbosity_exceeded"

    # Missing required facts (none of the expected facts appear)
    if expected_facts:
        norm = response.lower()
        found = [f for f in expected_facts if f.lower() in norm]
        if not found:
            return "missing_required_fact"

    # Forbidden claims present -> hallucination
    if forbidden_claims:
        norm = response.lower()
        found_forbidden = [f for f in forbidden_claims if f.lower() in norm]
        if found_forbidden:
            return "hallucination"

    if factuality_score < factuality_threshold:
        return "hallucination"

    if consistency_score < consistency_threshold:
        return "inconsistent_response"

    return "passed"
