import json
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django_tenants.utils import schema_context

pytestmark = pytest.mark.django_db


def _client(api_key):
    return Client(HTTP_HOST="demo.localhost", HTTP_X_API_KEY=api_key)


def _post_json(c, path, body):
    return c.post(path, data=json.dumps(body), content_type="application/json")


def make_adapter_result(output, error=None):
    from apps.evidence.adapters.base import AdapterResult
    return AdapterResult(output=output, latency_ms=100, token_count=50, error=error)


def test_health_check():
    c = Client(HTTP_HOST="demo.localhost")
    res = c.get("/api/health/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_jobs_public():
    c = Client(HTTP_HOST="demo.localhost")
    res = c.get("/api/evidence/jobs/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_create_job_requires_auth():
    c = Client(HTTP_HOST="demo.localhost")
    res = _post_json(c, "/api/evidence/jobs/", {"n_samples": 1})
    assert res.status_code == 401


def test_get_job_public(job):
    with schema_context("demo"):
      c = Client(HTTP_HOST="demo.localhost")
      res = c.get(f"/api/evidence/jobs/{job.id}/")
      assert res.status_code == 200
      assert res.json()["id"] == job.id


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
        assert "paper_count" in data
        assert "claim_count" in data
        assert "answer_count" in data


def test_get_job_404(api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get("/api/evidence/jobs/999999/")
        assert res.status_code == 404


def test_upload_paper_success(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        uploaded = SimpleUploadedFile("trial.pdf", b"%PDF-1.4 test", content_type="application/pdf")

        mock_s3 = type("MockS3", (), {})()
        mock_s3.create_bucket = lambda **kwargs: None
        uploaded_calls = []

        def fake_upload_fileobj(file_obj, bucket, key):
            uploaded_calls.append((bucket, key, file_obj.read()))
            file_obj.seek(0)

        mock_s3.upload_fileobj = fake_upload_fileobj

        with patch("apps.evidence.router._s3_client", return_value=mock_s3):
            res = c.post(
                f"/api/evidence/jobs/{job.id}/papers/",
                data={"title": "Trial Paper", "pdf_file": uploaded},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["title"] == "Trial Paper"
        assert data["claim_count"] == 0
        assert len(uploaded_calls) == 1
        assert uploaded_calls[0][1].endswith("trial.pdf")


def test_upload_paper_endpoint(job, api_key):
    """POST /papers/ with a minimal PDF returns a paper payload."""
    with schema_context("demo"):
        c = _client(api_key)
        pdf = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>"
            b"endobj\nxref\n0 4\ntrailer<</Size 4/Root 1 0 R>>"
            b"\nstartxref\n9\n%%EOF"
        )
        with patch("apps.evidence.router.boto3") as mock_boto:
            mock_boto.client.return_value.upload_fileobj = lambda *args, **kwargs: None
            mock_boto.client.return_value.create_bucket = lambda **kwargs: None
            res = c.post(
                f"/api/evidence/jobs/{job.id}/papers/",
                data={"pdf_file": SimpleUploadedFile("test.pdf", pdf, "application/pdf")},
            )
        assert res.status_code == 200
        data = res.json()
        assert "id" in data


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


def test_list_answers_empty(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/answers/")
        assert res.status_code == 200
        assert res.json() == []


def test_list_answers_can_filter_low_confidence(job, paper_a, api_key):
    with schema_context("demo"):
        from apps.evidence.models import AnswerRecord, RewardScore

        high = AnswerRecord.objects.create(
            paper=paper_a,
            question="High?",
            answer="yes",
            reasoning="Strong evidence.",
            source_sentence="Strong evidence.",
            error_types=[],
        )
        RewardScore.objects.create(
            answer_record=high,
            consistency_score=1.0,
            final_confidence=0.9,
            n_samples=1,
        )

        low = AnswerRecord.objects.create(
            paper=paper_a,
            question="Low?",
            answer="maybe",
            reasoning="Weak evidence.",
            source_sentence="Weak evidence.",
            error_types=["low_confidence"],
        )
        RewardScore.objects.create(
            answer_record=low,
            consistency_score=1.0,
            final_confidence=0.2,
            n_samples=1,
        )

        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/answers/?include_low_confidence=false")
        assert res.status_code == 200
        questions = [row["question"] for row in res.json()]
        assert questions == ["High?"]


def test_report_answer_counts(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/report/")
        assert res.status_code == 200
        data = res.json()
        assert "yes_count" in data
        assert "no_count" in data
        assert "maybe_count" in data


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


def test_dispatch_sync_requires_auth(job):
    with schema_context("demo"):
        c = Client(HTTP_HOST="demo.localhost")
        res = _post_json(c, f"/api/evidence/jobs/{job.id}/dispatch-sync/", {})
        assert res.status_code == 401


def test_chat_endpoint_no_auth(job):
    """Chat is public (read-only)."""
    with schema_context("demo"):
        c = Client(HTTP_HOST="demo.localhost")
        with patch("apps.evidence.adapters.openai.OpenAICompatAdapter") as adapter_cls:
            adapter_cls.return_value.complete.return_value = make_adapter_result(
                '{"answer":"The evidence supports this claim."}'
            )
            res = _post_json(c, f"/api/evidence/jobs/{job.id}/chat/", {"question": "Test?"})
        assert res.status_code in (200, 422)


def test_chat_endpoint_returns_answer_and_sources(job, paper_a):
    with schema_context("demo"):
        from apps.evidence.models import AnswerRecord, RewardScore

        answer = AnswerRecord.objects.create(
            paper=paper_a,
            question="Does Drug X work?",
            answer="yes",
            reasoning="The abstract states Drug X reduces tumor size.",
            source_sentence="Drug X reduces tumor size by 40% in mouse models.",
            error_types=[],
        )
        RewardScore.objects.create(
            answer_record=answer,
            consistency_score=1.0,
            final_confidence=0.91,
            n_samples=1,
        )

        low = AnswerRecord.objects.create(
            paper=paper_a,
            question="Low confidence question",
            answer="maybe",
            reasoning="Unclear result.",
            source_sentence="Unclear result.",
            error_types=["low_confidence"],
        )
        RewardScore.objects.create(
            answer_record=low,
            consistency_score=1.0,
            final_confidence=0.2,
            n_samples=1,
        )

        c = Client(HTTP_HOST="demo.localhost")
        with patch("apps.evidence.adapters.openai.OpenAICompatAdapter") as adapter_cls:
            adapter_cls.return_value.complete.return_value = make_adapter_result("Grounded response.")
            res = _post_json(c, f"/api/evidence/jobs/{job.id}/chat/", {"question": "Summarize the evidence."})

        assert res.status_code == 200
        data = res.json()
        assert data["answer"] == "Grounded response."
        assert data["context_answers"] == 1
        assert data["sources"][0]["paper"] == "Paper A"


def test_agent_requires_auth(job):
    with schema_context("demo"):
        from apps.evidence.models import AnalysisJob

        job.status = AnalysisJob.Status.DONE
        job.save(update_fields=["status"])

        c = Client(HTTP_HOST="demo.localhost")
        res = _post_json(c, f"/api/evidence/jobs/{job.id}/agent/", {"question": "Test agent"})
        assert res.status_code == 401


def test_agent_endpoint_requires_auth(job):
    with schema_context("demo"):
        c = Client(HTTP_HOST="demo.localhost")
        res = _post_json(c, f"/api/evidence/jobs/{job.id}/agent/", {"question": "Test?"})
        assert res.status_code == 401


def test_agent_endpoint_returns_loop_result(job, api_key):
    with schema_context("demo"):
        from apps.evidence.models import AnalysisJob

        job.status = AnalysisJob.Status.DONE
        job.save(update_fields=["status"])

        c = _client(api_key)
        with patch("apps.evidence.router.run_agent", return_value={
            "session_id": "sess-123",
            "question": "Test agent",
            "answer": "Agent answer",
            "confidence": 0.87,
            "reasoning": "Grounded answer.",
            "iterations": 2,
            "model": "llama-3.3-70b-instruct",
        }):
            res = _post_json(c, f"/api/evidence/jobs/{job.id}/agent/", {"question": "Test agent"})

        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job.id
        assert data["answer"] == "Agent answer"
        assert data["confidence"] == 0.87


def test_get_report(job, api_key):
    with schema_context("demo"):
        c = _client(api_key)
        res = c.get(f"/api/evidence/jobs/{job.id}/report/")
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job.id
        assert "total_claims" in data
        assert "total_answers" in data
        assert "yes_count" in data
        assert "no_count" in data
        assert "maybe_count" in data
