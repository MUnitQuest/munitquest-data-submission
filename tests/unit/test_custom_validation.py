"""
Tests the custom validation logic in the data validation module.
"""

import pytest
import os

from scoring.custom_validation import MUnitQuestCustomValidator as Validator


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


@pytest.mark.parametrize(
    ("path", "expected_err"),
    [
        ("tests/testdata/sidecars/valid.json", 0),
        ("tests/testdata/sidecars/invalid_fsamp_preamp.json", 1),
    ]
)
def test_fsamp(path: str, expected_err: int):
    validator: Validator = Validator("tests/testdata/Caillet")
    sidecar: dict = validator._load_json(path)

    fname: str = path.split("/")[-1]
    location: str = f"Caillet/sub-01/emg/{fname}"
    validator.validate_sampling_frequency(sidecar, location)

    errors: list[dict] = validator.errors

    assert len(errors) == expected_err

    if len(errors) > 0:
        assert errors[0].get("code") == "INSUFFICIENT_SAMPLING_FREQUENCY"


def test_validate_cede_missing_requirements():
    validator: Validator = Validator("tests/testdata/Caillet")

    sidecar: dict = validator._load_json("tests/testdata/sidecars/invalid_cede.json")

    validator.validate_cede(
        sidecar=sidecar,
        path="dummy/path"
    )

    assert len(validator.errors) == 1

    error_codes = [
        error["code"] for error in validator.errors
    ]

    assert "CEDE_REQUIREMENTS_MISSING" in error_codes

    validator.errors = []
    sidecar: dict = validator._load_json("tests/testdata/sidecars/invalid_fsamp_preamp.json")

    validator.validate_cede(
        sidecar=sidecar,
        path="dummy/path"
    )

    assert len(validator.errors) == 0
    assert len(validator.warnings) == 1
    assert validator.warnings[0].get("code") == "CEDE_REQUIREMENT_MISSING_PREAMPLIFICATION"

    validator.errors = []
    validator.warnings = []
    sidecar: dict = validator._load_json("tests/testdata/sidecars/invalid_cede_type.json")

    validator.validate_cede(
        sidecar=sidecar,
        path="dummy/path"
    )

    assert len(validator.errors) == 1
    assert len(validator.warnings) == 1
    assert "CEDE_REQUIREMENT_MISSING_GAIN" == validator.warnings[0].get("code")
    assert "CEDE_REQUIREMENT_INVALID_TYPE_PREAMPLIFICATION" == validator.errors[0].get("code")


def test_validate_cede_all_requirements_present():
    validator = Validator("tests/testdata/Caillet")

    sidecar: dict = validator._load_json("tests/testdata/sidecars/valid.json")

    validator.validate_cede(
        sidecar=sidecar,
        path="dummy/path"
    )

    assert len(validator.errors) == 0
