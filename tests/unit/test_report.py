"""
Test cases for HTML report module.
"""

import pytest
import os

from bundle.scoring.report import MUnitQuestDataSubmissionReport


@pytest.mark.parametrize("valid, expected_status", [
    (True, "Valid"),
    (False, "Invalid")
])
def test_status_property(valid, expected_status):
    report = MUnitQuestDataSubmissionReport(valid=valid, errors=[], warnings=[])
    assert report.validation_status == expected_status
