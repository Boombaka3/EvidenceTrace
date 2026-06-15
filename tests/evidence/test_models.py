# tests/evidence/test_models.py
import pytest
from django_tenants.utils import schema_context

pytestmark = pytest.mark.django_db


def test_analysis_job_default_status(db):
    with schema_context("demo"):
        from apps.evidence.models import AnalysisJob
        job = AnalysisJob.objects.create()
        assert job.status == "PENDING"
        assert job.n_samples == 3


def test_analysis_job_str(job):
    with schema_context("demo"):
        assert "PENDING" in str(job)


def test_paper_fk_to_job(paper_a, job):
    with schema_context("demo"):
        assert paper_a.job_id == job.id
        assert paper_a.title == "Paper A"


def test_claim_fk_to_paper(claim_a, paper_a):
    with schema_context("demo"):
        assert claim_a.paper_id == paper_a.id
        assert claim_a.claim_type == "causal"
        assert claim_a.text == "Drug X reduces tumor size by 40%."


def test_conflict_pair_verdict_choices(claim_a, claim_b):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        for verdict in ("SUPPORTS", "CONTRADICTS", "PARTIAL", "NEI"):
            cp = ConflictPair(
                claim_a=claim_a,
                claim_b=claim_b,
                verdict=verdict,
                conflict_type="none",
                severity=1,
                error_types=[],
            )
            cp.full_clean()


def test_conflict_pair_error_types_default(claim_a, claim_b):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        cp = ConflictPair.objects.create(
            claim_a=claim_a,
            claim_b=claim_b,
            verdict="NEI",
            conflict_type="none",
            severity=1,
        )
        assert cp.error_types == []


def test_conflict_pair_error_types_stored(conflict_pair):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        conflict_pair.error_types = ["overgeneralization", "false_certainty"]
        conflict_pair.save()
        refreshed = ConflictPair.objects.get(pk=conflict_pair.pk)
        assert "overgeneralization" in refreshed.error_types
        assert "false_certainty" in refreshed.error_types


def test_reward_score_all_nullable(conflict_pair):
    with schema_context("demo"):
        from apps.evidence.models import RewardScore
        r = RewardScore.objects.create(conflict_pair=conflict_pair)
        assert r.consistency_score is None
        assert r.nli_score is None
        assert r.faithfulness_score is None
        assert r.final_confidence is None


def test_reward_score_with_values(reward):
    with schema_context("demo"):
        assert reward.consistency_score == pytest.approx(1.0)
        assert reward.faithfulness_score == pytest.approx(0.9)
        assert reward.final_confidence == pytest.approx(0.97)
        assert reward.n_samples == 3


def test_reward_score_one_to_one(conflict_pair, reward):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        cp = ConflictPair.objects.select_related("reward").get(pk=conflict_pair.pk)
        assert cp.reward.pk == reward.pk
