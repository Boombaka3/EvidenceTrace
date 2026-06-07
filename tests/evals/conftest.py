# tests/evals/conftest.py
import pytest

# All tests in this directory implicitly have DB access.
pytestmark = pytest.mark.django_db
