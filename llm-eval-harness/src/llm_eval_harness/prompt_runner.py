from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import requests

from .models import EvaluationCase
from .env_loader import load_env

LOGGER = logging.getLogger(__name__)


def _normalize_mistral_url(api_url: str) -> str:
    # Backward-compatible rewrite for older config values.
    if api_url.rstrip("/") == "https://api.mistral.ai/v1/generate":
        return "https://api.mistral.ai/v1/chat/completions"
    return api_url


def _load_cases(path: Path) -> list[EvaluationCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvaluationCase(**item) for item in data]


def _call_mistral_api(prompt: str, api_key: str, api_url: str, model: str, timeout: int = 30) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # Best-effort extraction of text from different possible response shapes
    if isinstance(data, dict):
        if "output" in data:
            out = data["output"]
            if isinstance(out, list):
                return out[0]
            return str(out)
        if "text" in data:
            return str(data["text"])
        if "response" in data:
            return str(data["response"])
        if "choices" in data:
            choices = data["choices"]
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    if first.get("text"):
                        return str(first["text"])
                    message = first.get("message")
                    if isinstance(message, dict) and message.get("content"):
                        return str(message["content"])
                    if isinstance(message, str):
                        return message
                    return json.dumps(first)
                return str(first)
    # fallback
    return resp.text


def run_prompts(
    cases_path: str | Path,
    runs: int = 3,
    api_key_env: str = "MISTRAL_API_KEY",
    api_url_env: str = "MISTRAL_API_URL",
    model_env: str = "MISTRAL_MODEL",
    save_responses: str | Path | None = None,
) -> dict[str, list[str]]:
    cases_path = Path(cases_path)
    cases = _load_cases(cases_path)

    # Load env/.env if present (convenience for local dev; do not commit secrets)
    try:
        load_env()
    except Exception:
        pass

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"Mistral API key not found in env var {api_key_env}")
    api_url = _normalize_mistral_url(
        os.environ.get(api_url_env, "https://api.mistral.ai/v1/chat/completions")
    )
    model = os.environ.get(model_env, "mistral-small-latest")

    responses: dict[str, list[str]] = {}
    for case in cases:
        runs_out: list[str] = []
        for i in range(runs):
            try:
                resp_text = _call_mistral_api(case.prompt, api_key, api_url, model=model)
            except Exception as exc:  # network or parsing error
                LOGGER.exception("Error calling Mistral API for case %s: %s", case.case_id, exc)
                resp_text = ""
            runs_out.append(resp_text)
        responses[case.case_id] = runs_out

    if save_responses:
        outp = Path(save_responses)
        outp.write_text(json.dumps(responses, ensure_ascii=False, indent=2), encoding="utf-8")

    return responses
