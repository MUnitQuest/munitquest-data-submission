"""
Functionality for validating data submissions.
The submission will be validated against the BIDS validator
(https://github.com/bids-standard/bids-validator).
Further, successful submissions to MUnitQuest require an additional
custom validation layer, applied to BIDS validation results and an
additional scan of the submitted data.
"""

from scoring.report import MUnitQuestDataSubmissionReport
from scoring.bids_validation import MUnitQuestBidsValidatior
from scoring.custom_validation import MUnitQuestCustomValidator
from scoring.base import Validator
from dataclasses import asdict
# from muniverse.utils.bids_routines import *  # type: ignore (import not resolved locally)


class MUnitQuestDataSubmissionValidator(Validator):

    def __init__(self, dataset: str):
        """
        Init for dataset submission class.
        Args:
            dataset (str): root path of BIDS dataset to be validated
        """
        super().__init__(dataset)

        self.bids_validator = MUnitQuestBidsValidatior(dataset)
        self.custom_validator = MUnitQuestCustomValidator(dataset)
    
    @property
    def metrics(self) -> dict[str, float]:
        metrics: dict[str, float] = {
            "valid": 0. if self.valid else 1.,
            # space for more metrics
        }
        return metrics
    
    def write_scores(self, path: str) -> None:
        # has to be written to scores.json
        self._to_json(path, self.metrics)
    
    def generate_report(self, outfile: str) -> None:
        report: MUnitQuestDataSubmissionReport = MUnitQuestDataSubmissionReport(
            valid=self.valid,
            errors=self.errors,
            warnings=self.warnings,
            dataset_name=self.dataset_name
        )

        report.write_report(outfile)

        return None
    
    def validate(self, **kwargs) -> tuple[list, list, bool]:
        """
        Orchestrates the BIDS validation and the custom validation
        """
        config_path: str | None = kwargs.get("config_path", None)
        if config_path is not None:
            self.bids_validator.validation_config(config_path)  
        
        errors, warnings, _ = self.bids_validator.validate(
            print_errors=kwargs.get("print_errors", False),
            print_warnings=kwargs.get("print_warnings", False),
            config_path=config_path
        )

        custom_errors, _ = self.custom_validator.validate(
            print_errors=kwargs.get("print_errors", False)
        )

        self.errors = errors + custom_errors
        self.warnings = warnings  # currently no custom warnings implemented

        return self.errors, self.warnings, self.valid
