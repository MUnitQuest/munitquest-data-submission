"""
Tests the validation logic in the data validation module.
This includes both BIDS validation and custom validation.
"""

import pytest
import os

from scoring.data_validation import MUnitQuestDataSubmissionValidator as Validator


@pytest.mark.parametrize("path", [
    "nonexist",
    "tests/testdata/invalidDirStructure"
])
def test_validator_invalid_path(path):
    with pytest.raises(FileNotFoundError):
        validator: Validator = Validator(dataset=path)
        _, _, _ = validator.validate()
