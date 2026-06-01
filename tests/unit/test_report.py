"""
Test cases for HTML report module.
"""

import pytest

from scoring.report import MUnitQuestDataSubmissionReport as Report


@pytest.mark.parametrize("valid, expected_status", [
    (True, "Valid"),
    (False, "Invalid")
])
def test_status_property(valid, expected_status):
    report: Report = Report(valid=valid, errors=[], warnings=[], dataset_name="TEST")
    assert report.validation_status == expected_status


def test_aggregation():
    items = [
        {"code": "E1", "location": "file1"},
        {"code": "E1", "location": "file2"},
        {"code": "W1", "location": "file3"},
    ]
    counter, grouped = Report.aggregate_by_code(items)
    assert counter["E1"] == 2
    assert counter["W1"] == 1
    assert len(grouped["E1"]) == 2
    assert len(grouped["W1"]) == 1


def test_html_generation_invalid():
    errors: list[dict] = [
        {
            "code": "E1",
            "location": "file1",
            "severity": "error"
        }
    ]
    report: Report = Report(valid=False, errors=errors, warnings=[], dataset_name="TEST")
    report.generate_html()
    assert "<h2>Upload Instructions</h2>" not in report.html


def test_html_generation_valid():
    warnings: list[dict] = [
        {
            "code": "E1",
            "location": "file1",
            "severity": "warning"
        }
    ]
    report: Report = Report(valid=True, errors=[], warnings=warnings, dataset_name="TEST")
    report.generate_html()
    assert "<h2>Upload Instructions</h2>" in report.html
