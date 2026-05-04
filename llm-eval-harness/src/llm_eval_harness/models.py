from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EvaluationCase:
    case_id: str
    prompt: str
    expected_facts: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    expected_format_regex: str | None = None
    consistency_group: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvaluationResult:
    case_id: str
    response: str
    factuality_score: float
    format_score: float
    consistency_score: float
    failure_classification: str
    passed: bool
    details: dict[str, Any]
