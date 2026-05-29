"""
Tests the BIDS validation logic in the data validation module.
"""

import pytest
import os

from scoring.data_validation import MUnitQuestBidsValidatior as Validator


@pytest.fixture(scope="module", autouse=True)
def cleanup_bidsignore():
    yield
    os.remove("tests/testdata/bidsignore/missing/.bidsignore")
    os.remove("tests/testdata/bidsignore/exists_but_missing/.bidsignore")

    with open("tests/testdata/bidsignore/exists_but_missing/.bidsignore", "w", encoding="utf-8") as f:
        f.write("foo\nbar\n")


def test_validator_valid_path():
    validator: Validator = Validator(dataset="tests/testdata/Caillet")
    _, _, _ = validator.validate()
    assert validator.errors is not None
    assert validator.warnings is not None


def test_validator_with_config():
    validator: Validator = Validator(dataset="tests/testdata/Caillet")
    with pytest.raises(AssertionError):
        _, _, _ = validator.validate(config_path="nonexist_config.json")
    
    errors_no_config, warnings_no_config, valid_no_config = validator.validate()
    
    errors_with_config, warnings_with_config, valid_with_config = validator.validate(
        config_path="tests/testdata/validation_config.json"
    )
    assert errors_no_config != errors_with_config
    assert warnings_no_config != warnings_with_config
    assert valid_no_config != valid_with_config
    assert len(errors_with_config) == 0
    assert "SIDECAR_WITHOUT_DATAFILE" in [e["code"] for e in errors_no_config]
    assert "SIDECAR_WITHOUT_DATAFILE" in [e["code"] for e in warnings_with_config]


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
