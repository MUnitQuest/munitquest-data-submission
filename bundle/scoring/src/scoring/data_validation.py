"""
Functionality for validating data submissions.
The submission will be validated against the BIDS validator
(https://github.com/bids-standard/bids-validator).
Further, successful submissions to MUnitQuest require an additional
custom validation layer, applied to BIDS validation results and an
additional scan of the submitted data.
"""


import json
import subprocess
import os
import sys

from scoring.report import MUnitQuestDataSubmissionReport
from dataclasses import dataclass
# from muniverse.utils.bids_routines import *  # type: ignore (import not resolved locally)


@dataclass
class ValidationItem:
    """ data class for custom validation layer error and warning items """
    code: str  # custom code for the type of error/warning
    severity: str  # error or warning
    location: str  # filepath of the issue
    origin: str = "BIDS Validator"  # BIDS validator or MUnitQuest
    rule: str = "N/A"  # TODO


class MUnitQuestDataSubmissionValidator:

    def __init__(self, dataset: str):
        """
        Init for dataset submission class.
        Args:
            dataset (str): root path of BIDS dataset to be validated
        """
        self.metrics: dict[str, float] = {
            "valid": 0.
        }

        self.dataset = dataset
        # quick check if the provided dataset path is valid. If not, the program would throw
        # a JSONDecodeError, which is not very informative.
        if not os.path.exists(os.path.join(self.dataset, "dataset_description.json")):
            raise FileNotFoundError(
                f"Provided dataset path {self.dataset} does not exist. Make sure it is located at the root of the submitted zip-Archive"
            )
        
        self.errors: list = None
        self.warnings: list = None
        self.valid: bool = False

    def run_bids_validator(
        self,
        ignored_codes: list[str] = [],
        ignored_fields: list[str] = [],
        ignored_files: list[str] = [],
        print_errors: bool = False,
        print_warnings: bool = False,
        config_path: str | None = None
    ) -> tuple[list, list, bool]:
        """
        API to the official BIDS validator.
        Heavlily inspired by: https://github.com/dfarinagroup/muniverse/blob/main/src/muniverse/utils/bids_routines.py

        Args:
            ignored_codes (list[str], optional): Ignored error codes (e.g. ["SIDECAR_KEY_RECOMMENDED"]). Defaults to [].
            ignored_fields (list[str], optional): Errors corresponding to that field are ignored (e.g. ["DeviceSerialNumber"]). Defaults to [].
            ignored_files (list[str], optional): Ignored errors in these files (e.g. ["/dataset_description.json"]). Defaults to [].
            print_errors (bool, optional): Decides if errors should be printed. Defaults to False.
            print_warnings (bool, optional): Decides if warnings should be printed. Defaults to False.

        Returns:
            tuple[list, list, bool]: List of detected errors, list of detected warnings, and overall validity of the dataset.
        """
        # more robust towards remote clusters to call the cli tool via it's full path
        validator: str = os.path.join(os.path.dirname(sys.executable), "bids-validator-deno")
        # Run bids validator
        if config_path is None:
            result = subprocess.run(
                [validator, "--format", "json", self.dataset],
                capture_output=True,
                text=True
            )
        else:
            assert os.path.exists(config_path), f"Provided config path {config_path} does not exist."
            result = subprocess.run(
                [validator, "--format", "json", "--config", config_path, self.dataset],
                capture_output=True,
                text=True
            )
        
        # Extract and filter all issues
        validation = json.loads(result.stdout)
        issues = validation["issues"]["issues"]
        issues = [f for f in issues if (not "code" in f or f["code"] not in ignored_codes)]
        issues = [f for f in issues if (not "subCode" in f or f["subCode"] not in ignored_fields)]
        issues = [f for f in issues if (not "location" in f or f["location"] not in ignored_files)]
        # Split issues in errors and warnings
        errors = [f for f in issues if f["severity"] == "error"]
        warnings = [f for f in issues if f["severity"] == "warning"]
        # Print issues
        if print_errors:
            print(f"Number of detected errors: {len(errors)}")
            print(json.dumps(errors, indent=4))
        if print_warnings:    
            print(f"Number of detected warnings: {len(warnings)}")
            print(json.dumps(warnings, indent=4))
        # Check if the folder is BIDS valid
        valid = True if len(errors) == 0 else False

        self.errors, self.warnings, self.valid = errors, warnings, valid  

        return errors, warnings, valid
    
    @staticmethod
    def validation_config(path: str):
        validation_config: dict[str, list[dict]] = {
            "ignore": [],
            "warning": [
                {
                    "code": "SIDECAR_WITHOUT_DATAFILE",  # ignore missing edfs
                }, 
            ],
            "error": [],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(validation_config, f, indent=4)

        return validation_config
    
    def write_scores(self, path: str) -> None:
        # update valid metric
        if self.valid:
            self.metrics["valid"] = 1.
        # has to be written to scores.json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=4)

    def _to_json(self, path: str, data: list) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    
    def generate_report(self, outfile: str) -> None:
        report: MUnitQuestDataSubmissionReport = MUnitQuestDataSubmissionReport(
            valid=self.valid,
            errors=self.errors,
            warnings=self.warnings
        )

        report.write_report(outfile)

        return None
