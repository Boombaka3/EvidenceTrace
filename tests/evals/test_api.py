# tests/evals/test_api.py
import json
import pytest
from unittest.mock import patch

from apps.evals.models import EvalRun, EvalSuite, ModelRun, PromptCase

pytestmark = pytest.mark.django_db


# ── helpers ───────────────────────────────────────────────────────────────────

def _post_json(client, path, body):
    return client.post(
        path,
        data=json.dumps(body),
        content_type="application/json",
    )


def _create_suite(client, name="API Test Suite") -> dict:
    r = _post_json(client, "/api/evals/suites/", {
        "name": name,
        "version": 1,
        "rubric": [{"criterion": "quality", "weight": 1.0}],
        "regression_threshold": 0.3,
    })
    assert r.status_code == 200, r.content
    return r.json()


def _create_case(client, suite_id: int) -> dict:
    r = _post_json(client, f"/api/evals/suites/{suite_id}/cases/", {
        "name": "Test Case",
        "system_prompt": "You are helpful.",
        "user_prompt": "Say hello in one word.",
        "expected_output": "Hello",
    })
    assert r.status_code == 200, r.content
    return r.json()


# ── tests ─────────────────────────────────────────────────────────────────────

def test_health_check(client):
    r = client.get("/api/health/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_suite(client):
    data = _create_suite(client, name="Create Suite Test")
    assert "id" in data
    assert data["name"] == "Create Suite Test"
    assert data["version"] == 1


def test_list_suites(client):
    _create_suite(client, name="Suite A")
    _create_suite(client, name="Suite B")
    r = client.get("/api/evals/suites/")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "Suite A" in names
    assert "Suite B" in names


def test_create_case(client):
    suite = _create_suite(client)
    r = _post_json(client, f"/api/evals/suites/{suite['id']}/cases/", {
        "name": "My Case",
        "system_prompt": "You are helpful.",
        "user_prompt": "What is 2+2?",
        "expected_output": "4",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Case"
    assert data["suite_id"] == suite["id"]


def test_create_run(client):
    suite = _create_suite(client)
    _create_case(client, suite["id"])

    with patch("apps.evals.tasks.dispatch.dispatch_eval_run.delay"):
        r = _post_json(client, "/api/evals/runs/", {
            "suite_id": suite["id"],
            "model_ids": ["claude-haiku-4-5-20251001"],
            "score_mode": "exact_match",
        })

    assert r.status_code == 200, r.content
    data = r.json()
    assert "id" in data
    assert data["status"] == "PENDING"
    assert data["score_mode"] == "exact_match"


def test_get_run_status(client):
    suite = _create_suite(client)
    _create_case(client, suite["id"])

    with patch("apps.evals.tasks.dispatch.dispatch_eval_run.delay"):
        create_resp = _post_json(client, "/api/evals/runs/", {
            "suite_id": suite["id"],
            "model_ids": ["test-model"],
            "score_mode": "llm_judge",
        })
    run_id = create_resp.json()["id"]

    r = client.get(f"/api/evals/runs/{run_id}/")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == run_id
    assert "status" in data
    assert "progress" in data
    assert "total" in data
    assert "score_mode" in data


def test_regression_no_baseline(client):
    suite = _create_suite(client)
    _create_case(client, suite["id"])

    with patch("apps.evals.tasks.dispatch.dispatch_eval_run.delay"):
        create_resp = _post_json(client, "/api/evals/runs/", {
            "suite_id": suite["id"],
            "model_ids": ["test-model"],
            "score_mode": "llm_judge",
        })
    run_id = create_resp.json()["id"]

    # EvalRun has no baseline_run; should return 400
    r = client.get(f"/api/evals/runs/{run_id}/regression/")
    assert r.status_code == 400


def test_list_models(client):
    r = client.get("/api/evals/models/")
    assert r.status_code == 200
    models = r.json()
    assert isinstance(models, list)
    assert len(models) > 0
    assert any("claude" in m for m in models)
