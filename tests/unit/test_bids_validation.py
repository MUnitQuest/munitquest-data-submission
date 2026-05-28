"""
Tests the BIDS validation logic in the data validation module.
"""

import pytest
import os

from scoring.data_validation import MUnitQuestBidsValidatior as Validator


def test_validator_valid_path():
    validator: Validator = Validator(dataset="tests/testdata/Caillet")
    _, _, _ = validator.run_bids_validator()
    assert validator.errors is not None
    assert validator.warnings is not None


def test_validator_with_config():
    validator: Validator = Validator(dataset="tests/testdata/Caillet")
    with pytest.raises(AssertionError):
        _, _, _ = validator.run_bids_validator(config_path="nonexist_config.json")
    
    errors_no_config, warnings_no_config, valid_no_config = validator.run_bids_validator()
    
    errors_with_config, warnings_with_config, valid_with_config = validator.run_bids_validator(
        config_path="tests/testdata/validation_config.json"
    )
    assert errors_no_config != errors_with_config
    assert warnings_no_config != warnings_with_config
    assert valid_no_config != valid_with_config
    assert len(errors_with_config) == 0
    assert "SIDECAR_WITHOUT_DATAFILE" in [e["code"] for e in errors_no_config]
    assert "SIDECAR_WITHOUT_DATAFILE" in [e["code"] for e in warnings_with_config]
