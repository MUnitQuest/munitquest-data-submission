"""
Tests the validation logic in the data validation module.
This includes both BIDS validation and custom validation.
"""

import pytest
import os

from scoring.data_validation import MUnitQuestDataSubmissionValidator as Validator


@pytest.fixture(scope="module", autouse=True)
def cleanup_bidsignore():
    yield
    os.remove("tests/testdata/bidsignore/missing/.bidsignore")
    os.remove("tests/testdata/bidsignore/exists_but_missing/.bidsignore")

    with open("tests/testdata/bidsignore/exists_but_missing/.bidsignore", "w", encoding="utf-8") as f:
        f.write("foo\nbar\n")


@pytest.mark.parametrize("path", [
    "nonexist",
    "tests/testdata/invalidDirStructure"
])
def test_validator_invalid_path(path):
    with pytest.raises(FileNotFoundError):
        validator: Validator = Validator(dataset=path)
        _, _, _ = validator.validate()


@pytest.mark.parametrize("path", [
    "tests/testdata/bidsignore/valid",
    "tests/testdata/bidsignore/missing",
    "tests/testdata/bidsignore/exists_but_missing",
])
def test_validator_bidsignore(path: str):
    bids_ignore_path: str = os.path.join(path, ".bidsignore")
    
    if path == "tests/testdata/bidsignore/missing":
        with pytest.warns(
            UserWarning,
            match=".bidsignore file missing and added to the dataset to exclude derivatives from BIDS validator."
        ):
            validator: Validator = Validator(dataset=path)
    elif path == "tests/testdata/bidsignore/exists_but_missing":
        with pytest.warns(
            UserWarning,
            match="'derivatives/' missing in .bidsignore file. Added to exclude derivatives from BIDS validator."
        ):
            validator: Validator = Validator(dataset=path)
    else:
        validator: Validator = Validator(dataset=path)

    assert os.path.exists(bids_ignore_path)
    # assert last line is 'derivatives/', ignoring trailing newlines
    with open(bids_ignore_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
        assert lines[-1] == "derivatives/"
    


