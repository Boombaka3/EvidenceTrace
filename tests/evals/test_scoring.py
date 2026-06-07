# tests/evals/test_scoring.py
import pytest
from unittest.mock import MagicMock, patch

from apps.evals.models import EvalRun, EvalSuite, ModelRun, PromptCase, ScoreResult
from apps.evals.scoring.exact_match import score_exact_match
from apps.evals.scoring.regression import score_regression

pytestmark = pytest.mark.django_db


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def suite(tenant_schema) -> EvalSuite:
    return EvalSuite.objects.create(
        name="Score Test Suite",
        version=1,
        rubric=[{"criterion": "quality", "weight": 1.0}],
        regression_threshold=0.3,
    )


@pytest.fixture
def baseline_run(suite) -> EvalRun:
    return EvalRun.objects.create(
        suite=suite,
        model_ids=["test-model"],
        score_mode=EvalRun.ScoreMode.REGRESSION,
    )


@pytest.fixture
def current_run(suite) -> EvalRun:
    return EvalRun.objects.create(
        suite=suite,
        model_ids=["test-model"],
        score_mode=EvalRun.ScoreMode.REGRESSION,
    )


@pytest.fixture
def prompt_case(suite) -> PromptCase:
    return PromptCase.objects.create(
        suite=suite,
        name="Test Case",
        system_prompt="You are helpful.",
        user_prompt="Say hello.",
        expected_output="Hello",
    )


def _make_model_run(eval_run, prompt_case, output="Hello") -> ModelRun:
    return ModelRun.objects.create(
        eval_run=eval_run,
        prompt_case=prompt_case,
        model_id="test-model",
        status=ModelRun.Status.DONE,
        raw_output=output,
    )


def _make_score(model_run, overall) -> ScoreResult:
    return ScoreResult.objects.create(
        model_run=model_run,
        scores={"quality": overall * 5 if overall is not None else None},
        overall=overall,
        passed=overall is not None and overall >= 0.6,
    )


# ── exact_match tests ─────────────────────────────────────────────────────────

def test_exact_match_pass(tenant_schema, suite, baseline_run, prompt_case):
    mr = _make_model_run(baseline_run, prompt_case, output="Hello")
    result = score_exact_match(mr)
    assert result.passed is True
    assert result.overall >= 0.95


def test_exact_match_fail(tenant_schema, suite, baseline_run, prompt_case):
    mr = _make_model_run(baseline_run, prompt_case, output="Goodbye, world!")
    result = score_exact_match(mr)
    assert result.passed is False
    assert result.overall < 0.95


def test_exact_match_no_expected(tenant_schema, suite, baseline_run):
    case_no_expected = PromptCase.objects.create(
        suite=suite,
        name="No Expected",
        system_prompt="x",
        user_prompt="y",
        expected_output=None,
    )
    mr = _make_model_run(baseline_run, case_no_expected, output="anything")
    result = score_exact_match(mr)
    assert result.passed is True
    assert result.overall == 1.0


# ── regression tests ──────────────────────────────────────────────────────────

def test_regression_none_guard(tenant_schema, suite, baseline_run, current_run, prompt_case):
    """current_overall=None (judge failed) must set delta=None, passed=True."""
    baseline_mr = _make_model_run(baseline_run, prompt_case, output="Good answer")
    _make_score(baseline_mr, overall=0.8)

    current_mr = _make_model_run(current_run, prompt_case, output="Some answer")

    # Mock score_llm_judge to simulate a judge failure
    failed_result = ScoreResult(
        model_run=current_mr,
        scores={},
        overall=None,
        passed=None,
        judge_reasoning="judge_unavailable: timeout",
    )
    with patch("apps.evals.scoring.regression.score_llm_judge", return_value=failed_result):
        result = score_regression(current_mr, baseline_run.id)

    assert result.regression_delta is None
    assert result.passed is True


def test_regression_positive_delta(tenant_schema, suite, baseline_run, current_run, prompt_case):
    """current > baseline by more than threshold => passed=True."""
    baseline_mr = _make_model_run(baseline_run, prompt_case, output="OK answer")
    _make_score(baseline_mr, overall=0.7)

    current_mr = _make_model_run(current_run, prompt_case, output="Great answer")

    improved_result = ScoreResult(
        model_run=current_mr,
        scores={"quality": 4},
        overall=0.9,
        passed=True,
    )
    with patch("apps.evals.scoring.regression.score_llm_judge", return_value=improved_result):
        result = score_regression(current_mr, baseline_run.id)

    # delta = 0.9 - 0.7 = 0.2; threshold=0.3; 0.2 >= -0.3 => passed
    assert result.regression_delta == pytest.approx(0.2, abs=1e-4)
    assert result.passed is True


def test_regression_negative_delta_below_threshold(
    tenant_schema, suite, baseline_run, current_run, prompt_case
):
    """current drops more than threshold below baseline => passed=False."""
    baseline_mr = _make_model_run(baseline_run, prompt_case, output="Good answer")
    _make_score(baseline_mr, overall=0.8)

    current_mr = _make_model_run(current_run, prompt_case, output="Bad answer")

    degraded_result = ScoreResult(
        model_run=current_mr,
        scores={"quality": 1},
        overall=0.2,
        passed=False,
    )
    with patch("apps.evals.scoring.regression.score_llm_judge", return_value=degraded_result):
        result = score_regression(current_mr, baseline_run.id)

    # delta = 0.2 - 0.8 = -0.6; threshold=0.3; -0.6 < -0.3 => failed
    assert result.regression_delta == pytest.approx(-0.6, abs=1e-4)
    assert result.passed is False
