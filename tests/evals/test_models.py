# tests/evals/test_models.py
import pytest
from django.db import IntegrityError, transaction

from apps.evals.models import EvalRun, EvalSuite, ModelRun, PromptCase, ScoreResult

pytestmark = pytest.mark.django_db


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_suite(tenant_schema, **kwargs) -> EvalSuite:
    defaults = {"name": "Test Suite", "version": 1, "rubric": []}
    defaults.update(kwargs)
    return EvalSuite.objects.create(**defaults)


def _make_run(suite: EvalSuite, **kwargs) -> EvalRun:
    defaults = {"suite": suite, "model_ids": ["test-model"], "score_mode": "llm_judge"}
    defaults.update(kwargs)
    return EvalRun.objects.create(**defaults)


def _make_case(suite: EvalSuite, **kwargs) -> PromptCase:
    defaults = {
        "suite": suite,
        "name": "Test Case",
        "system_prompt": "You are helpful.",
        "user_prompt": "Say hello.",
    }
    defaults.update(kwargs)
    return PromptCase.objects.create(**defaults)


def _make_model_run(eval_run: EvalRun, prompt_case: PromptCase, **kwargs) -> ModelRun:
    defaults = {
        "eval_run": eval_run,
        "prompt_case": prompt_case,
        "model_id": "test-model",
        "status": ModelRun.Status.DONE,
        "raw_output": "hello",
    }
    defaults.update(kwargs)
    return ModelRun.objects.create(**defaults)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_eval_suite_create(tenant_schema):
    suite = _make_suite(
        tenant_schema,
        name="My Suite",
        version=2,
        rubric=[{"criterion": "quality", "weight": 1.0}],
        regression_threshold=0.25,
    )
    suite.refresh_from_db()
    assert suite.name == "My Suite"
    assert suite.version == 2
    assert suite.rubric == [{"criterion": "quality", "weight": 1.0}]
    assert suite.regression_threshold == 0.25
    assert suite.baseline_run is None


def test_prompt_case_requires_suite(tenant_schema):
    with pytest.raises((IntegrityError, Exception)):
        with transaction.atomic():
            PromptCase.objects.create(
                name="orphan",
                system_prompt="x",
                user_prompt="x",
            )


def test_eval_run_status_default(tenant_schema):
    suite = _make_suite(tenant_schema)
    run = _make_run(suite)
    assert run.status == EvalRun.Status.PENDING


def test_score_result_overall_nullable(tenant_schema):
    suite = _make_suite(tenant_schema)
    run = _make_run(suite)
    case = _make_case(suite)
    mr = _make_model_run(run, case)
    sr = ScoreResult.objects.create(
        model_run=mr,
        scores={},
        overall=None,
        passed=None,
    )
    sr.refresh_from_db()
    assert sr.overall is None
    assert sr.passed is None


def test_score_result_str_none_overall(tenant_schema):
    suite = _make_suite(tenant_schema)
    run = _make_run(suite)
    case = _make_case(suite)
    mr = _make_model_run(run, case)
    # Use unsaved instance — __str__ must not raise even without a DB row
    sr = ScoreResult(model_run=mr, scores={}, overall=None, passed=None)
    result = str(sr)
    assert "None" in result
    assert "ModelRun" in result
