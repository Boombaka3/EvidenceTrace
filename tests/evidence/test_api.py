# tests/evidence/test_api.py
import json

import pytest
from django.test import Client
from django_tenants.utils import schema_context
from unittest.mock import patch

pytestmark = pytest.mark.django_db


def _client(api_key):
    return Client(HTTP_HOST="demo.localhost", HTTP_X_API_KEY=api_key)


def _post_json(c, path, body):
    return c.post(path, data=json.dumps(body), content_type="application/json")


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_check():
    c = Client(HTTP_HOST="demo.localhost")
    res = c.get("/api/health/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ── Auth ───────────────────────────────────────────────────────────────────────

def test_unauthed_returns_401():
    c = Client(HTTP_HOST="demo.localhost")
    res = c.get("/api/evidence/jobs/999/")
    assert res.status_code == 401


# ── Jobs ───────────────────────────────────────────────────────────────────────

def test_create_job(api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = _post_json(c, "/api/evidence/jobs/", {"n_samples": 1})
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        assert data["status"] == "PENDING"
        assert data["n_samples"] == 1


def test_get_job(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == job.id
        assert data["status"] == "PENDING"
        assert "papers_count" in data
        assert "claims_count" in data
        assert "conflicts_count" in data


def test_get_job_404(api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get("/api/evidence/jobs/999999/")
        assert res.status_code == 404


# ── Papers ─────────────────────────────────────────────────────────────────────

def test_list_papers_empty(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/papers/")
        assert res.status_code == 200
        assert res.json() == []


def test_list_papers_with_data(job, paper_a, paper_b, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/papers/")
        assert res.status_code == 200
        papers = res.json()
        assert len(papers) == 2
        titles = [p["title"] for p in papers]
        assert "Paper A" in titles
        assert "Paper B" in titles


# ── Claims ─────────────────────────────────────────────────────────────────────

def test_list_claims_empty(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/claims/")
        assert res.status_code == 200
        assert res.json() == []


def test_list_claims_with_data(job, claim_a, claim_b, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/claims/")
        assert res.status_code == 200
        claims = res.json()
        assert len(claims) == 2
        texts = [cl["text"] for cl in claims]
        assert "Drug X reduces tumor size by 40%." in texts


# ── Conflicts ──────────────────────────────────────────────────────────────────

def test_list_conflicts_empty(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/conflicts/")
        assert res.status_code == 200
        assert res.json() == []


def test_list_conflicts_with_data(job, conflict_pair, reward, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/conflicts/")
        assert res.status_code == 200
        conflicts = res.json()
        assert len(conflicts) == 1
        cp = conflicts[0]
        assert cp["verdict"] == "CONTRADICTS"
        assert cp["severity"] == 4
        assert "reward" in cp
        assert cp["reward"]["final_confidence"] == pytest.approx(0.97)
        assert cp["final_confidence"] == pytest.approx(0.97)
        assert cp["consistency_score"] == pytest.approx(1.0)
        assert isinstance(cp["error_types"], list)


# ── Dispatch ───────────────────────────────────────────────────────────────────

def test_dispatch_job(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        with patch("apps.evidence.tasks.dispatch.dispatch_analysis_job.delay"):
            res = _post_json(c, f"/api/evidence/jobs/{job.id}/dispatch/", {})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "dispatched"


def test_dispatch_already_running_job(job, api_key):
    with schema_context("demo"):
        from apps.evidence.models import AnalysisJob
        job.status = AnalysisJob.Status.RUNNING
        job.save()
        c = _client(api_key)
        res = _post_json(c, f"/api/evidence/jobs/{job.id}/dispatch/", {})
        assert res.status_code == 400


# ── Report ─────────────────────────────────────────────────────────────────────

def test_get_report(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/report/")
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job.id
        assert "total_claims" in data
        assert "total_conflicts" in data
        assert "contradictions" in data
        assert "supports" in data
        assert "partial" in data
        assert "nei" in data
