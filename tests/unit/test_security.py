import pytest

from app.core.security import InvalidRequest, validate_question


def test_question_is_normalized() -> None:
    assert validate_question("  What   is   AMF? ") == "What is AMF?"


def test_question_length_is_limited() -> None:
    with pytest.raises(InvalidRequest):
        validate_question("x" * 20, max_length=10)
