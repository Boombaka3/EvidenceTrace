# tests/evals/test_schemas.py
import pytest
from pydantic import ValidationError

from apps.evals.schemas import EvalRunIn, EvalSuiteIn

# No DB access needed — pure Pydantic validation tests.


def test_eval_suite_in_valid():
    s = EvalSuiteIn(name="My Suite", version=2)
    assert s.name == "My Suite"
    assert s.version == 2
    assert s.rubric == []
    assert s.regression_threshold == 0.3


def test_eval_suite_in_missing_name():
    with pytest.raises(ValidationError) as exc_info:
        EvalSuiteIn()
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)


def test_eval_run_in_requires_models():
    with pytest.raises(ValidationError) as exc_info:
        EvalRunIn(suite_id=1, model_ids=[])
    errors = exc_info.value.errors()
    assert any("model_ids" in str(e["loc"]) for e in errors)


def test_rubric_weight_structure():
    rubric = [{"criterion": "Correctness", "weight": 0.6}, {"criterion": "Clarity", "weight": 0.4}]
    s = EvalSuiteIn(name="Suite", rubric=rubric)
    assert len(s.rubric) == 2
    assert s.rubric[0]["criterion"] == "Correctness"
    assert s.rubric[1]["weight"] == 0.4
