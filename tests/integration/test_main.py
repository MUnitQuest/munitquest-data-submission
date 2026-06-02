"""
Tests main.py, the entry point upon submission of a dataset.
"""

import pytest
import subprocess
import os
import shutil


# create directories before executing the tests and remove directories after tests are done
@pytest.fixture(scope="module", autouse=True)
def output_path():
    path: str = "tests/integration/output"
    os.makedirs(path, exist_ok=True)
    
    yield path

    # cleanup
    shutil.rmtree(path)


def test_main_invalid_args():
    result = subprocess.run(
        ["python", "bundle/scoring/main.py", "only_one_arg"],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "AssertionError" in result.stderr
    assert "Usage: python main.py <input_path> <output_path>" in result.stderr


def test_main_valid_args(output_path):
    result = subprocess.run(
        ["python", "bundle/scoring/main.py", "tests/testdata/testMain", output_path],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert os.path.exists(os.path.join(output_path, "scores.json"))
    assert os.path.exists(os.path.join(output_path, "detailed_results.html"))
    