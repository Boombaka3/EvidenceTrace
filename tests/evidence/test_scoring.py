# tests/evidence/test_scoring.py
import pytest
from unittest.mock import patch, MagicMock
from django_tenants.utils import schema_context

pytestmark = pytest.mark.django_db


def _adapter_result(output, error=None):
    from apps.evidence.adapters.base import AdapterResult
    return AdapterResult(output=output, latency_ms=100, token_count=50, error=error)


YES_TAGGED = (
    "<think>\n"
    "The abstract states that Drug X reduces tumor size by 40%. "
    "This directly supports an affirmative answer.\n"
    "</think>\n"
    "<answer>yes</answer>"
)

MAYBE_TAGGED = (
    "<think>\n"
    "The abstract provides inconclusive evidence. "
    "Results were mixed across populations.\n"
    "</think>\n"
    "<answer>maybe</answer>"
)

# Kept for fallback/backward-compat tests
YES_JSON = ('{"answer":"yes","reasoning":"The abstract confirms this.",'
            '"source_sentence":"Drug X reduces tumor size.","confidence":0.9,'
            '"error_types":[]}')


# ── question_answerer tests ────────────────────────────────────────────────────

def test_question_answerer_returns_yes(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result(YES_TAGGED)
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Does Drug X reduce tumor size?")
            assert result.answer == "yes"
            assert result._format_ok is True
            assert "tumor" in result.reasoning.lower()


def test_question_answerer_handles_fence(paper_a):
    with schema_context("demo"):
        fenced = "```\n" + YES_TAGGED + "\n```"
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result(fenced)
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Test?")
            assert result.answer == "yes"


def test_question_answerer_handles_parse_error(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result("not json")
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Test?")
            assert result.answer == "maybe"


def test_question_answerer_adapter_error_falls_back(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result("", error="connection refused")
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Test?")
            assert result.answer == "maybe"


def test_question_answerer_format_score(paper_a):
    """Format score is 1.0 when <think>/<answer> tags present."""
    with schema_context("demo"):
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result(YES_TAGGED)
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Test?")
            assert result._format_ok is True


def test_question_answerer_json_fallback_format_false(paper_a):
    """JSON fallback sets format_ok=False."""
    with schema_context("demo"):
        with patch("apps.evidence.scoring.question_answerer.OpenAICompatAdapter") as M:
            M.return_value.complete.return_value = _adapter_result(YES_JSON)
            from apps.evidence.scoring.question_answerer import answer_question
            result = answer_question(paper_a, "Test?")
            assert result.answer == "yes"
            assert result._format_ok is False


def test_parse_response_valid_tags():
    from apps.evidence.scoring.question_answerer import _parse_response

    parsed = _parse_response(YES_TAGGED)
    assert parsed["answer"] == "yes"
    assert parsed["format_ok"] is True
    assert "directly supports" in parsed["reasoning"].lower()


def test_parse_response_fallback_json():
    from apps.evidence.scoring.question_answerer import _parse_response

    parsed = _parse_response(YES_JSON)
    assert parsed["answer"] == "yes"
    assert parsed["format_ok"] is False
    assert parsed["confidence"] == pytest.approx(0.9)


def test_parse_response_invalid_answer_normalizes():
    from apps.evidence.scoring.question_answerer import _parse_response

    parsed = _parse_response('{"answer":"uncertain","reasoning":"x","source_sentence":"y"}')
    assert parsed["answer"] == "maybe"
    assert parsed["format_ok"] is False


def test_clamp_bounds():
    from apps.evidence.scoring.question_answerer import _clamp

    assert _clamp(0.5) == pytest.approx(0.5)
    assert _clamp(-1) == 0.0
    assert _clamp(2) == 1.0
    assert _clamp("0.25") == pytest.approx(0.25)
    assert _clamp("bad") is None


# ── NLI grounding tests ────────────────────────────────────────────────────────

def test_nli_grounding_returns_float_or_none():
    """NLI grounding returns a float in [0,1] or None (model may not be cached)."""
    from apps.evidence.scoring.nli_grounding import score_nli_grounding
    result = score_nli_grounding(
        "Drug X reduces tumor size.",
        "Drug X reduces tumor size by 40% in mouse models."
    )
    assert result is None or (isinstance(result, float) and 0.0 <= result <= 1.0)


def test_nli_grounding_empty_inputs_return_none():
    """Empty reasoning or abstract returns None."""
    from apps.evidence.scoring.nli_grounding import score_nli_grounding
    assert score_nli_grounding("", "abstract text") is None
    assert score_nli_grounding("reasoning", "") is None
    assert score_nli_grounding("", "") is None


# ── outcome_reward tests ──────────────────────────────────────────────────────

def test_outcome_reward_correct():
    """Outcome reward is 1.0 when answer matches gold."""
    from apps.evidence.scoring.reward_voting import _compute_outcome_reward
    assert _compute_outcome_reward("yes", "yes") == 1.0
    assert _compute_outcome_reward("no",  "yes") == 0.0
    assert _compute_outcome_reward("yes", "")    is None


def test_outcome_reward_normalization():
    """Gold label variants normalize correctly."""
    from apps.evidence.scoring.reward_voting import _compute_outcome_reward
    assert _compute_outcome_reward("yes", "supports")    == 1.0
    assert _compute_outcome_reward("no",  "contradicts") == 1.0
    assert _compute_outcome_reward("yes", "refutes")     == 0.0
    assert _compute_outcome_reward("maybe", "nei")       == 1.0


def test_compute_format_score_true(paper_a):
    from apps.evidence.models import AnswerRecord
    from apps.evidence.scoring.reward_voting import _compute_format_score

    record = AnswerRecord(paper=paper_a, question="Q?", answer="yes", reasoning="r", source_sentence="s")
    record._format_ok = True
    assert _compute_format_score(record) == 1.0


def test_compute_format_score_false(paper_a):
    from apps.evidence.models import AnswerRecord
    from apps.evidence.scoring.reward_voting import _compute_format_score

    record = AnswerRecord(paper=paper_a, question="Q?", answer="yes", reasoning="r", source_sentence="s")
    record._format_ok = False
    assert _compute_format_score(record) == 0.0


# ── reward_voting tests ────────────────────────────────────────────────────────

def test_reward_voting_consistency(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.reward_voting.answer_question") as mock_aq:
            from apps.evidence.models import AnswerRecord
            yes_record = AnswerRecord(
                paper=paper_a, question="Test?", answer="yes",
                reasoning="The abstract states Drug X reduces tumor size.",
                source_sentence="Drug X reduces tumor size.",
            )
            yes_record._format_ok = True
            mock_aq.return_value = yes_record
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=0.9):
                from apps.evidence.scoring.reward_voting import compute_reward
                answer_record, reward = compute_reward(paper_a, "Test?", n_samples=3)
                assert reward.consistency_score == 1.0
                assert answer_record.answer == "yes"


def test_reward_voting_split(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.reward_voting.answer_question") as mock_aq:
            from apps.evidence.models import AnswerRecord
            yes = AnswerRecord(paper=paper_a, question="Test?", answer="yes",
                               reasoning="r", source_sentence="s")
            yes._format_ok = True
            no  = AnswerRecord(paper=paper_a, question="Test?", answer="no",
                               reasoning="r", source_sentence="s")
            no._format_ok = True
            mock_aq.side_effect = [yes, yes, no]
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=0.8):
                from apps.evidence.scoring.reward_voting import compute_reward
                answer_record, reward = compute_reward(paper_a, "Test?", n_samples=3)
                assert pytest.approx(reward.consistency_score, abs=0.01) == 2/3
                assert answer_record.answer == "yes"


def test_reward_voting_all_fail(paper_a):
    with schema_context("demo"):
        with patch("apps.evidence.scoring.reward_voting.answer_question",
                   side_effect=Exception("LLM unavailable")):
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=None):
                from apps.evidence.scoring.reward_voting import compute_reward
                answer_record, reward = compute_reward(paper_a, "Test?", n_samples=3)
    assert answer_record.answer == "maybe"
    assert reward.consistency_score == pytest.approx(1.0)
    # no gold, nli=None → grounding=consistency=1.0, format=0.0
    # 0.5*1.0 + 0.3*1.0 + 0.2*0.0 = 0.8
    assert reward.final_confidence == pytest.approx(0.8)


def test_reward_voting_nli_none_uses_consistency(paper_a):
    """When NLI returns None, consistency is used as grounding proxy."""
    with schema_context("demo"):
        with patch("apps.evidence.scoring.reward_voting.answer_question") as mock_aq:
            from apps.evidence.models import AnswerRecord
            rec = AnswerRecord(paper=paper_a, question="Test?", answer="yes",
                               reasoning="", source_sentence="")
            rec._format_ok = True
            mock_aq.return_value = rec
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=None):
                from apps.evidence.scoring.reward_voting import compute_reward
                _, reward = compute_reward(paper_a, "Test?", n_samples=1)
    # nli=None → grounding=consistency=1.0, format=1.0
    # 0.5*1.0 + 0.3*1.0 + 0.2*1.0 = 1.0
    assert reward.final_confidence == pytest.approx(1.0)
    assert reward.faithfulness_score == pytest.approx(1.0)  # format score stored here


def test_reward_voting_four_components(paper_a):
    """Four-component reward returns all fields with correct formula."""
    with schema_context("demo"):
        from apps.evidence.models import AnswerRecord

        yes_record = AnswerRecord(
            paper=paper_a, question="Test?", answer="yes",
            reasoning="The abstract states Drug X reduces tumor size.",
            source_sentence="Drug X reduces tumor size.",
        )
        yes_record._format_ok = True

        with patch("apps.evidence.scoring.reward_voting.answer_question",
                   return_value=yes_record):
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=0.85):
                from apps.evidence.scoring.reward_voting import compute_reward
                ar, reward = compute_reward(
                    paper_a, "Test?", n_samples=1, gold_label="yes"
                )
                assert reward.nli_score == pytest.approx(0.85)
                assert reward.consistency_score == pytest.approx(1.0)
                assert reward.faithfulness_score == pytest.approx(1.0)  # format score
                # outcome=1.0 (yes==yes), grounding=0.85, consistency=1.0, format=1.0
                # 0.4*1.0 + 0.3*0.85 + 0.2*1.0 + 0.1*1.0 = 0.4+0.255+0.2+0.1 = 0.955
                assert reward.final_confidence == pytest.approx(0.955, abs=0.01)


def test_low_confidence_flag(paper_a):
    """Answers below threshold get low_confidence in error_types."""
    with schema_context("demo"):
        from apps.evidence.models import AnswerRecord

        low_conf_record = AnswerRecord(
            paper=paper_a, question="Test?", answer="maybe",
            reasoning="Weak evidence.", source_sentence="Maybe.",
        )
        low_conf_record._format_ok = False

        with patch("apps.evidence.scoring.reward_voting.answer_question",
                   return_value=low_conf_record):
            with patch("apps.evidence.scoring.reward_voting.score_nli_grounding",
                       return_value=0.1):
                from apps.evidence.scoring.reward_voting import compute_reward
                ar, reward = compute_reward(paper_a, "Test?", n_samples=1)
                assert reward.final_confidence < 0.5
