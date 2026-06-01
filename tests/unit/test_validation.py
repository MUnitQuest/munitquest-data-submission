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


@pytest.mark.parametrize(("path", "expected_dataset_name", "expected_rel_path"), [
    ("tests/testdata/CailletNoEthicsApproval", "CailletNoEthicsApproval", "CailletNoEthicsApproval/some/random/path.json"),
    ("tests/testdata/Caillet", "Caillet", "Caillet/some/random/path.json"),
])
def test_relative_path(path: str, expected_dataset_name: str, expected_rel_path: str):
    validator: Validator = Validator(dataset=path)
    full_path: str = os.path.join(path, "some/random/path.json")
    rel_path: str = validator._relative_path(full_path)
    assert validator.dataset_name == expected_dataset_name
    assert rel_path == expected_rel_path
