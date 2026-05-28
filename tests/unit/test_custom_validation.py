"""
Tests the custom validation logic in the data validation module.
"""

import pytest
import os

from scoring.data_validation import MUnitQuestCustomValidator as Validator


def test_valid_ethics_approval():
    path: str = "tests/testdata/EthicsApprovals/Correct"
    validator: Validator = Validator(dataset=path)
    validator.validate_ethics_approval()
    assert len(validator.errors) == 0
    assert validator.valid == True


@pytest.mark.parametrize(
    "path",
    [
        "tests/testdata/EthicsApprovals/Empty",
        "tests/testdata/EthicsApprovals/Missing",
    ]
)
def test_empty_nonexist_ethics_approval(path: str):
    validator: Validator = Validator(dataset=path)
    validator.validate_ethics_approval()
    assert len(validator.errors) == 1
    assert validator.valid == False
    assert validator.errors[0]["code"] == "MISSING_ETHICS_APPROVAL"


def test_invalid_ethics_approval():
    path: str = "tests/testdata/EthicsApprovals/InvalidType"
    validator: Validator = Validator(dataset=path)
    validator.validate_ethics_approval()
    assert len(validator.errors) == 1
    assert validator.valid == False
    assert validator.errors[0]["code"] == "INVALID_ETHICS_APPROVAL_TYPE"
