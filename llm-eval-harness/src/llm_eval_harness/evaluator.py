from __future__ import annotations

import re
from dataclasses import asdict
from difflib import SequenceMatcher
from itertools import combinations
from statistics import mean
from typing import Iterable

from .failure_analysis import classify_failure
from .logging_config import configure_logging
from .models import EvaluationCase, EvaluationResult

LOGGER = configure_logging()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def factuality_score(response: str, expected_facts: Iterable[str], forbidden_claims: Iterable[str]) -> float:
    normalized_response = _normalize(response)
    expected_facts = list(expected_facts)
    forbidden_claims = list(forbidden_claims)
    expected = [fact for fact in expected_facts if _normalize(fact) in normalized_response]
    forbidden = [claim for claim in forbidden_claims if _normalize(claim) in normalized_response]

    if not expected_facts and not forbidden_claims:
        return 1.0

    positive_ratio = len(expected) / max(1, len(expected_facts))
    penalty = len(forbidden) / max(1, len(forbidden_claims)) if forbidden_claims else 0.0
    score = max(0.0, positive_ratio - penalty)
    return round(score, 3)


def format_score(response: str, expected_format_regex: str | None) -> float:
    if expected_format_regex is None:
        return 1.0
    return 1.0 if re.fullmatch(expected_format_regex, response.strip(), flags=re.DOTALL) else 0.0


def consistency_score(response: str, peer_responses: Iterable[str] | None = None) -> float:
    peers = list(peer_responses or [])
    if not peers:
        return 1.0

    normalized_response = _normalize(response)
    similarities = [SequenceMatcher(None, normalized_response, _normalize(peer)).ratio() for peer in peers]
    return round(mean(similarities), 3)


def _normalize_simple(text: str) -> str:
    return text.strip().lower()


def compare_responses(responses: Iterable[str], keywords: Iterable[str] | None = None) -> dict:
    """Compare a set of responses produced for the same prompt.

    Returns metrics:
      - exact_match_rate: fraction equal to the most common normalized response
      - avg_pairwise_similarity: mean SequenceMatcher ratio across response pairs
      - keyword_overlap: average fraction of keywords present per response (if keywords provided)
      - unique_count: number of distinct normalized responses
    """
    resp_list = [r for r in responses]
    if not resp_list:
        return {
            "exact_match_rate": 0.0,
            "avg_pairwise_similarity": 0.0,
            "keyword_overlap": 0.0,
            "unique_count": 0,
        }

    normalized = [_normalize_simple(r) for r in resp_list]
    # exact match rate (mode frequency)
    mode_resp = max(set(normalized), key=normalized.count)
    exact_match_rate = normalized.count(mode_resp) / len(normalized)

    # average pairwise similarity
    sims: list[float] = []
    for a, b in combinations(normalized, 2):
        sims.append(SequenceMatcher(None, a, b).ratio())
    avg_pairwise = round(mean(sims), 3) if sims else 1.0

    # keyword overlap: average fraction of provided keywords appearing in each response
    keyword_overlap = 0.0
    if keywords:
        kws = list(keywords)
        if kws:
            per_resp = []
            for r in normalized:
                found = sum(1 for k in kws if _normalize_simple(k) in r)
                per_resp.append(found / len(kws))
            keyword_overlap = round(mean(per_resp), 3)

    return {
        "exact_match_rate": round(exact_match_rate, 3),
        "avg_pairwise_similarity": avg_pairwise,
        "keyword_overlap": keyword_overlap,
        "unique_count": len(set(normalized)),
    }


def evaluate_case(
    case: EvaluationCase,
    response: str,
    peer_responses: Iterable[str] | None = None,
    all_responses: Iterable[str] | None = None,
) -> EvaluationResult:
    # Prefer factuality_threshold, but keep compatibility with older case files.
    factuality_threshold = float(
        case.metadata.get("factuality_threshold", case.metadata.get("hallucination_threshold", 0.8))
    )
    consistency_threshold = float(case.metadata.get("consistency_threshold", 0.8))

    factuality = factuality_score(response, case.expected_facts, case.forbidden_claims)
    formatted = format_score(response, case.expected_format_regex)
    consistency = consistency_score(response, peer_responses)
    failure = classify_failure(
        factuality,
        formatted,
        consistency,
        response,
        factuality_threshold=factuality_threshold,
        consistency_threshold=consistency_threshold,
        expected_facts=case.expected_facts,
        forbidden_claims=case.forbidden_claims,
        metadata=case.metadata,
    )
    passed = failure == "passed"

    details = {
        "case": asdict(case),
        "factuality_threshold": factuality_threshold,
        "consistency_threshold": consistency_threshold,
    }

    # If multiple runs were provided for this case, add comparison metrics
    if all_responses:
        details["multi_run_comparison"] = compare_responses(all_responses, keywords=case.expected_facts)

    LOGGER.info(
        "Evaluated case %s: passed=%s failure=%s factuality=%.3f format=%.3f consistency=%.3f",
        case.case_id,
        passed,
        failure,
        factuality,
        formatted,
        consistency,
    )

    return EvaluationResult(
        case_id=case.case_id,
        response=response,
        factuality_score=factuality,
        format_score=formatted,
        consistency_score=consistency,
        failure_classification=failure,
        passed=passed,
        details=details,
    )


def evaluate_suite(
    cases: Iterable[EvaluationCase],
    responses: dict[str, list[str] | str],
    peer_responses: dict[str, list[str]] | None = None,
) -> list[EvaluationResult]:
    peer_responses = peer_responses or {}
    results: list[EvaluationResult] = []

    for case in cases:
        if case.case_id not in responses:
            raise KeyError(f"Missing response for case_id={case.case_id}")

        raw = responses[case.case_id]
        # Accept either a single response string or a list of runs
        if isinstance(raw, list):
            if not raw:
                raise ValueError(f"Empty responses list for case_id={case.case_id}")
            primary = raw[0]
            all_runs = raw
            peers = raw[1:]
        else:
            primary = raw
            all_runs = [raw]
            peers: list[str] = []

        # Merge any separately supplied peer_responses mapping
        peers = list(peers) + list(peer_responses.get(case.case_id, []))

        results.append(
            evaluate_case(
                case,
                primary,
                peer_responses=peers or None,
                all_responses=all_runs,
            )
        )

    return results
