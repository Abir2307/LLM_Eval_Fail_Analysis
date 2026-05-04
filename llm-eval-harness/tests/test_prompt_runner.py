import json
from pathlib import Path

import requests

from llm_eval_harness.prompt_runner import run_prompts


def test_run_prompts_calls_mistral_and_returns_responses(tmp_path: Path, monkeypatch) -> None:
    cases = [
        {"case_id": "p-1", "prompt": "Say hello"},
    ]

    cases_file = tmp_path / "cases.json"
    cases_file.write_text(json.dumps(cases))

    # Prepare fake response payloads for consecutive calls
    payloads = [
        {"output": ["Hello from run 1"]},
        {"choices": [{"text": "Hello from run 2"}]},
    ]

    def fake_post(url, json=None, headers=None, timeout=None):
        class FakeResp:
            def __init__(self, payload):
                self._payload = payload
                self.text = json_module.dumps(payload)

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        # pop next payload (cycle if necessary)
        payload = payloads.pop(0) if payloads else {"output": [""]}
        return FakeResp(payload)

    import json as json_module

    # Patch requests.post used inside prompt_runner
    monkeypatch.setenv("MISTRAL_API_KEY", "fakekey")
    monkeypatch.setenv("MISTRAL_API_URL", "https://api.example/test")
    monkeypatch.setattr(requests, "post", fake_post)

    results = run_prompts(cases_file, runs=2, api_key_env="MISTRAL_API_KEY", api_url_env="MISTRAL_API_URL")

    assert "p-1" in results
    assert len(results["p-1"]) == 2
    assert "Hello from run 1" in results["p-1"][0]
    assert "Hello from run 2" in results["p-1"][1]


def test_run_prompts_rewrites_legacy_generate_url(tmp_path: Path, monkeypatch) -> None:
    cases = [{"case_id": "p-legacy", "prompt": "Ping"}]
    cases_file = tmp_path / "cases.json"
    cases_file.write_text(json.dumps(cases))

    seen_url = {"value": ""}

    def fake_post(url, json=None, headers=None, timeout=None):
        seen_url["value"] = url

        class FakeResp:
            text = '{"choices":[{"message":{"content":"ok"}}]}'

            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return FakeResp()

    monkeypatch.setenv("MISTRAL_API_KEY", "fakekey")
    monkeypatch.setenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/generate")
    monkeypatch.setattr(requests, "post", fake_post)

    run_prompts(cases_file, runs=1)
    assert seen_url["value"] == "https://api.mistral.ai/v1/chat/completions"
