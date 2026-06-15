# tests/evidence/test_scoring.py
import pytest
from unittest.mock import patch, MagicMock
from django_tenants.utils import schema_context

pytestmark = pytest.mark.django_db


def _adapter_result(output, error=None):
    from apps.evidence.adapters.base import AdapterResult
    return AdapterResult(output=output, latency_ms=100, token_count=50, error=error)


CONTRADICTS_JSON = (
    '{"verdict":"CONTRADICTS","conflict_type":"direct","severity":4,'
    '"reasoning":"test reason","source_sentence_a":"A sentence","source_sentence_b":"B sentence",'
    '"error_types":["condition_dropping"]}'
)

FENCED_JSON = "```json\n" + CONTRADICTS_JSON + "\n```"

SUPPORTS_JSON = (
    '{"verdict":"SUPPORTS","conflict_type":"none","severity":1,'
    '"reasoning":"test reason","source_sentence_a":"A","source_sentence_b":"B",'
    '"error_types":[]}'
)

FAITHFULNESS_CLEAN = (
    '{"faithful":true,"faithfulness_score":0.9,'
    '"error_types":[],"reasoning":"claim matches source"}'
)

FAITHFULNESS_OVERGENERALIZED = (
    '{"faithful":false,"faithfulness_score":0.3,'
    '"error_types":["overgeneralization","condition_dropping"],'
    '"reasoning":"claim removes population restriction"}'
)


# ── conflict_judge tests ───────────────────────────────────────────────────────

def test_conflict_judge_contradicts(claim_a, claim_b):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
            Mock.return_value.complete.return_value = _adapter_result(CONTRADICTS_JSON)
            from apps.evidence.scoring.conflict_judge import judge_conflict
            result = judge_conflict(claim_a, claim_b)
        assert result.verdict == "CONTRADICTS"
        assert result.conflict_type == "direct"
        assert result.severity == 4
        assert "condition_dropping" in result.error_types


def test_conflict_judge_strips_json_fences(claim_a, claim_b):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
            Mock.return_value.complete.return_value = _adapter_result(FENCED_JSON)
            from apps.evidence.scoring.conflict_judge import judge_conflict
            result = judge_conflict(claim_a, claim_b)
        assert result.verdict == "CONTRADICTS"


def test_conflict_judge_bad_json_falls_back_to_nei(claim_a, claim_b):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
            Mock.return_value.complete.return_value = _adapter_result("not json at all !!!")
            from apps.evidence.scoring.conflict_judge import judge_conflict
            result = judge_conflict(claim_a, claim_b)
        assert result.verdict == "NEI"


def test_conflict_judge_adapter_error_falls_back(claim_a, claim_b):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
            Mock.return_value.complete.return_value = _adapter_result("", error="connection refused")
            from apps.evidence.scoring.conflict_judge import judge_conflict
            result = judge_conflict(claim_a, claim_b)
        assert result.verdict == "NEI"


def test_conflict_judge_text_returns_dict():
    with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
        Mock.return_value.complete.return_value = _adapter_result(CONTRADICTS_JSON)
        from apps.evidence.scoring.conflict_judge import judge_conflict_text
        result = judge_conflict_text("claim A text", "claim B text")
    assert result["verdict"] == "CONTRADICTS"
    assert "reasoning" in result
    assert "error_types" in result


def test_conflict_judge_invalid_error_type_filtered(claim_a, claim_b):
    bad_json = (
        '{"verdict":"CONTRADICTS","conflict_type":"direct","severity":2,'
        '"reasoning":"test","source_sentence_a":"A","source_sentence_b":"B",'
        '"error_types":["overgeneralization","totally_fake_error_type"]}'
    )
    with schema_context("demo"):
        with patch("apps.evidence.scoring.conflict_judge.OpenAICompatAdapter") as Mock:
            Mock.return_value.complete.return_value = _adapter_result(bad_json)
            from apps.evidence.scoring.conflict_judge import judge_conflict
            result = judge_conflict(claim_a, claim_b)
        assert "overgeneralization" in result.error_types
        assert "totally_fake_error_type" not in result.error_types


# ── faithfulness tests ─────────────────────────────────────────────────────────

def test_faithfulness_clean_claim():
    with patch("apps.evidence.scoring.faithfulness.OpenAICompatAdapter") as Mock:
        Mock.return_value.complete.return_value = _adapter_result(FAITHFULNESS_CLEAN)
        from apps.evidence.scoring.faithfulness import score_faithfulness
        result = score_faithfulness("Drug X reduces tumors.", "Drug X reduces tumors in mice.")
    assert result["faithful"] is True
    assert result["faithfulness_score"] == pytest.approx(0.9)
    assert result["error_types"] == []


def test_faithfulness_overgeneralized_claim():
    with patch("apps.evidence.scoring.faithfulness.OpenAICompatAdapter") as Mock:
        Mock.return_value.complete.return_value = _adapter_result(FAITHFULNESS_OVERGENERALIZED)
        from apps.evidence.scoring.faithfulness import score_faithfulness
        result = score_faithfulness("Drug X always reduces tumors.", "Drug X reduces tumors in mice.")
    assert result["faithful"] is False
    assert "overgeneralization" in result["error_types"]
    assert "condition_dropping" in result["error_types"]


def test_faithfulness_empty_inputs():
    from apps.evidence.scoring.faithfulness import score_faithfulness
    result = score_faithfulness("", "source text")
    assert result["faithful"] is None
    assert result["faithfulness_score"] is None
    assert result["error_types"] == []


def test_faithfulness_score_clamped():
    out_of_range = (
        '{"faithful":true,"faithfulness_score":1.5,'
        '"error_types":[],"reasoning":"test"}'
    )
    with patch("apps.evidence.scoring.faithfulness.OpenAICompatAdapter") as Mock:
        Mock.return_value.complete.return_value = _adapter_result(out_of_range)
        from apps.evidence.scoring.faithfulness import score_faithfulness
        result = score_faithfulness("claim", "source")
    assert result["faithfulness_score"] == pytest.approx(1.0)


# ── reward_voting tests ────────────────────────────────────────────────────────

def test_reward_voting_unanimous_verdict(claim_a, claim_b):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        cp = ConflictPair(
            claim_a=claim_a, claim_b=claim_b,
            verdict="CONTRADICTS", conflict_type="direct", severity=4,
            reasoning="test", source_sentence_a="A", source_sentence_b="B",
            error_types=[],
        )
        with patch("apps.evidence.scoring.reward_voting.judge_conflict", return_value=cp):
            with patch("apps.evidence.scoring.reward_voting.score_faithfulness",
                       return_value={"faithfulness_score": 0.9, "error_types": []}):
                from apps.evidence.scoring.reward_voting import compute_reward
                result_pair, reward = compute_reward(claim_a, claim_b, n_samples=3)
        assert result_pair.verdict == "CONTRADICTS"
        assert reward.consistency_score == pytest.approx(1.0)
        assert reward.final_confidence == pytest.approx(0.7 * 1.0 + 0.3 * 0.9)


def test_reward_voting_majority_verdict(claim_a, claim_b):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        def _cp(verdict):
            return ConflictPair(
                claim_a=claim_a, claim_b=claim_b,
                verdict=verdict, conflict_type="none", severity=1,
                reasoning="test", source_sentence_a="A", source_sentence_b="B",
                error_types=[],
            )
        side_effects = [_cp("CONTRADICTS"), _cp("CONTRADICTS"), _cp("SUPPORTS")]
        with patch("apps.evidence.scoring.reward_voting.judge_conflict", side_effect=side_effects):
            with patch("apps.evidence.scoring.reward_voting.score_faithfulness",
                       return_value={"faithfulness_score": 0.8, "error_types": []}):
                from apps.evidence.scoring.reward_voting import compute_reward
                result_pair, reward = compute_reward(claim_a, claim_b, n_samples=3)
        assert result_pair.verdict == "CONTRADICTS"
        assert reward.consistency_score == pytest.approx(2 / 3, abs=0.01)


def test_reward_voting_all_fail(claim_a, claim_b):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.reward_voting.judge_conflict",
                   side_effect=Exception("LLM unavailable")):
            with patch("apps.evidence.scoring.reward_voting.score_faithfulness",
                       return_value={"faithfulness_score": None, "error_types": []}):
                from apps.evidence.scoring.reward_voting import compute_reward
                result_pair, reward = compute_reward(claim_a, claim_b, n_samples=3)
        assert result_pair.verdict == "NEI"
        # All 3 samples fail → 3 NEI votes → unanimous consistency = 1.0
        assert reward.consistency_score == pytest.approx(1.0)
        # faithfulness is None → final_confidence = consistency = 1.0
        assert reward.final_confidence == pytest.approx(1.0)


def test_reward_voting_faithfulness_none_uses_consistency(claim_a, claim_b):
    with schema_context("demo"):
        from apps.evidence.models import ConflictPair
        cp = ConflictPair(
            claim_a=claim_a, claim_b=claim_b,
            verdict="NEI", conflict_type="none", severity=1,
            reasoning="test", source_sentence_a="A", source_sentence_b="B",
            error_types=[],
        )
        with patch("apps.evidence.scoring.reward_voting.judge_conflict", return_value=cp):
            with patch("apps.evidence.scoring.reward_voting.score_faithfulness",
                       return_value={"faithfulness_score": None, "error_types": []}):
                from apps.evidence.scoring.reward_voting import compute_reward
                _, reward = compute_reward(claim_a, claim_b, n_samples=1)
        assert reward.final_confidence == pytest.approx(1.0)
        assert reward.faithfulness_score is None
