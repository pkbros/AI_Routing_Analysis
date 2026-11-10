"""Smoke + contract tests for the Avaloka inference service."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

import service

client = TestClient(service.app)
EXAMPLE = json.loads((Path(__file__).parent / "example_request.json").read_text())


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_predict_shape():
    r = client.post("/predict", json=EXAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == len(EXAMPLE["instances"])


def test_feature_contract():
    assert service.FEATURES == ['source_benchmark', 'task_domain', 'agent_role', 'difficulty_tag', 'prompt_tokens', 'prompt_words', 'prompt_chars', 'prompt_lines', 'question_marks', 'math_symbols', 'digit_count', 'uppercase_ratio', 'avg_word_length', 'golden_reference_words']
