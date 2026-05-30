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
import abc
import re
import warnings

import pandas as pd
import numpy as np

from scoring.report import MUnitQuestDataSubmissionReport
from dataclasses import asdict, dataclass
# from muniverse.utils.bids_routines import *  # type: ignore (import not resolved locally)


@dataclass
class ValidationItem:
    """ data class for custom validation layer error and warning items """
    code: str  # custom code for the type of error/warning
    severity: str  # error or warning
    location: str  # filepath of the issue
    origin: str = "BIDS Validator"  # BIDS validator or MUnitQuest
    rule: str = "N/A"  # TODO


class Validator(abc.ABC):
    """ Base class for validators. """

    def __init__(self, dataset: str):
        self.dataset = dataset
        # quick check if the provided dataset path is valid. If not, the program would throw
        # a JSONDecodeError, which is not very informative.
        if not os.path.exists(os.path.join(self.dataset, "dataset_description.json")):
            raise FileNotFoundError(
                f"Provided dataset path {self.dataset} does not exist. Make sure it is located at the root of the submitted zip-Archive"
            )

        self.dataset_name: str = self.dataset.split("/")[-1]

        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self._valid: bool = False
    
    @property
    def valid(self) -> bool:
        self._valid = True if len(self.errors) == 0 else False
        return self._valid

    def _relative_path(self, path: str) -> str:
        return f"{self.dataset_name}{path.split(self.dataset_name)[-1]}"

    @abc.abstractmethod
    def validate(self, **kwargs):
        pass
    
    @staticmethod
    def _load_json(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    @staticmethod
    def _to_json(path: str, data: list) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


class MUnitQuestBidsValidatior(Validator):
    """ Class for validating BIDS datasets. """

    def __init__(self, dataset: str):
        super().__init__(dataset)

        self._check_bidsignore()
    
    def _check_bidsignore(self) -> None:
        """
        Our validation scheme requires `derivatives/` to be present
        in the .bidsignore file. This function checks if the file
        exists in the root of the data directory. If the file does not
        exist it is created. If the file does exist, but does not contain
        `derivatives/`, the foldername is appended.

        This is because derivative files are not standardized yet in terms
        of BIDS validation. Hence, a lot of false positive errors would
        be generated if derivatives are not ignored.

        Returns:
            None
        """
        bidsignore_path: str = os.path.join(self.dataset, ".bidsignore")
        if not os.path.exists(bidsignore_path):
            with open(bidsignore_path, "w", encoding="utf-8") as f:
                warnings.warn(
                    ".bidsignore file missing and added to the dataset to exclude derivatives from BIDS validator.",
                    UserWarning
                )
                f.write("derivatives/\n")
        else:
            with open(bidsignore_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if "derivatives/\n" not in lines:
                with open(bidsignore_path, "a", encoding="utf-8") as f:
                    warnings.warn(
                        "'derivatives/' missing in .bidsignore file. Added to exclude derivatives from BIDS validator.",
                        UserWarning
                    )
                    f.write("derivatives/\n")

    def validate(
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

        self.errors, self.warnings, self._valid = errors, warnings, valid  

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


class MUnitQuestCustomValidator(Validator):
    """ class for custom validation on top of BIDS validation results."""

    def __init__(self, dataset: str):
        super().__init__(dataset)
        self.dataset_sidecar: dict = self._load_json(os.path.join(self.dataset, "dataset_description.json"))
        self.recording_sidecars: list[str] = self._get_recording_sidecars()
    
    def _get_recording_sidecars(self) -> list[str]:
        """ helper to list all _emg.json-files """
        sidecars: list[str] = []
        for root, _, files in os.walk(self.dataset):
            for file in files:
                full_path: str = os.path.join(root, file)
                if file.endswith("_emg.json") and not "derivatives/" in full_path:
                    sidecars.append(file)
        
        return sidecars

    
    def _itemize(self, code: str, severity: str, location: str) -> dict[str, str]:
        item: ValidationItem = ValidationItem(
            code=code,
            severity=severity,
            location=self._relative_path(location),
            origin="MUnitQuest Custom Validator",
        )
        return asdict(item)
    
    def _bids_filename(self, path: str) -> str:
        """
        Helper method to derive BIDS filename components from
        any file (e.g. derivatives) to create a match between
        derivatives and raw recordings.

        sub-<label>[_ses-<label>]_task-<label>[_acq-<label>][_run-<index>][_recording-<label>]_[events.tsv|emg.json]

        Args:
            path (str): input derivative-path
        
        Returns:
            str: BIDS components of derivative filename
        """
        fname: str = path.split("/")[-1]
        re_pattern: re.Pattern = re.compile(
            r"""
            ^sub-(?P<sub>[^_]+)
            (?:_ses-(?P<ses>[^_]+))?
            _task-(?P<task>[^_]+)
            (?:_acq-(?P<acq>[^_]+))?
            (?:_run-(?P<run>\d+))?
            (?:_recording-(?P<recording>[^_]+))?
            # (?:_(?P<suffix>.+))?
            # \.(?P<ext>[^.]+)$
            """,
            re.VERBOSE,
        )
        matched: re.Match | None = re_pattern.match(fname)

        if matched is None:
            self.errors.append(
                self._itemize(
                    code="DERIVATIVES_INVALID_EVENT_FILENAME",
                    location=path,
                    severity="error"
                )
            )
        
        component_dict: dict[str, str] = matched.groupdict()
        bids_components: list[str] = []
        for k, v in component_dict.items():
            if v is not None:
                bids_components.append(f"{k}-{v}")
        bids_filename: str = ("_").join(bids_components)

        return bids_filename
    
    def validate_sampling_frequency(self, sidecar: dict, path: str, min_freq: int = 2000) -> None:
        """
        Validates towards a minimum sampling frequency in the EMGSideCar.
            Error Code: "INSUFFICIENT_SAMPLING_FREQUENCY"
        Args:
            sidecar (dict): the sidecar json data of the recording
            path (str): the path to the sidecar, used for error location relative to dataset name.
            min_freq (int, optional): applied minimum sampling frequency. Defaults to 2000.
        
        Returns:
            None, but adds to self.errors if the sampling frequency is too low.
        """
        # NOTE We do not have to check the existence of SamplingFrequency,
        # as this is already required by the BIDS validator
        fsamp: int = sidecar["SamplingFrequency"]
        if fsamp < min_freq:
            self.errors.append(
                self._itemize(
                    code="INSUFFICIENT_SAMPLING_FREQUENCY",
                    severity="error",
                    location=path
                )
            )
        
        return None

    def validate_ethics_approval(self) -> None:
        """
        Validates towards non-empty existance of ethics approval.
            Error Code: "MISSING_ETHICS_APPROVAL"
        
        Returns:
            None, but adds to self.errors if ethics approval is missing.
        """
        ethics_approvals: list | None = self.dataset_sidecar.get("EthicsApprovals", None)
        if ethics_approvals is None:
            self.errors.append(
                self._itemize(
                    code="MISSING_ETHICS_APPROVAL",
                    severity="error",
                    location="/dataset_description.json"
                )
            )
        elif not isinstance(ethics_approvals, list):
            self.errors.append(
                self._itemize(
                    code="INVALID_ETHICS_APPROVAL_TYPE",
                    severity="error",
                    location="/dataset_description.json"
                )
            )
        elif len(ethics_approvals) == 0:
            self.errors.append(
                self._itemize(
                    code="MISSING_ETHICS_APPROVAL",
                    severity="error",
                    location="/dataset_description.json"
                )
            )
        
        return None
    
    def validate_cede(self, sidecar: dict, path: str, requirements: list[str] = ["Gain", "Preamplification"]) -> None:
        """
        Validates for existence of CEDE requirements. In our case, we are
            validating towards Gain and Preamplification.

        Args:
            sidecar (dict): sidecar to check.
            path (str): location for export.
            requirements (list[str]): keys to check existence for. Defaults to ["Gain", "Preamplification"].
        """
        # TODO content check, e.g. data type and validity
        for requirement in requirements:
            cede = sidecar.get(requirement, None)
            if cede is None:
                self.errors.append(
                    self._itemize(
                        code=f"CEDE_REQUIREMENT_MISSING_{requirement.upper()}",
                        severity="error",
                        location=path
                    )
                )
            elif not isinstance(cede, (int, float)):
                self.errors.append(
                    self._itemize(
                        code=f"CEDE_REQUIREMENT_INVALID_TYPE_{requirement.upper()}",
                        severity="error",
                        location=path
                    )
                )
    
    def _validate_label_file(self, file: str) -> None:
        """
        Validate a BIDS-like motor unit events table.
        Adapted from: https://github.com/klotz-t/munitquest-algorithm-submission/blob/scoring_function/bundle/scoring/isometric/scoring.py

        Required columns:
        - onset       : float >= 0
        - duration    : must be 0
        - sample      : integer
        - unit_id     : integer
        - description : must include "motor-unit-spike"

        Args
        ----
            file : str
                Path to the file   

        Returns
        -------
            is_valid : bool
                True if file is valid.

            errors : list of str
                List of validation error messages.
        """
        errors: list[dict] = []
        # Define required column names
        required_columns: set[str] = {
            "onset",
            "duration",
            "sample",
            "unit_id",
            "description",
        }

        # check if corresponding recording exists
        sidecar_filename: str = f"{self._bids_filename(path=file)}_emg.json"
        if not sidecar_filename in self.recording_sidecars:
            self.errors.append(
                self._itemize(
                    code="DERIVATIVES_EVENTS_NOT_MATCHING_SIDECAR",
                    location=file,
                    severity="error"
                )
            )

        # Load the file
        try:
            df: pd.DataFrame = pd.read_table(file)
        except:
            errors.append(
                self._itemize(
                    code="UNREADABLE_EVENTS_TSV_FORMAT",
                    location=file,
                    severity="error"
                )
            )
            return False, errors

        # Check if required columns are present
        missing: set[str] = required_columns - set(df.columns)

        if missing:
            # f"Missing required columns: {sorted(missing)}"
            errors.append(
                self._itemize(
                    code="DERIVATIVES_MISSING_EVENT_COLUMN",
                    location=file,
                    severity="error"
                )
            )

            # Cannot continue safely
            return False, errors

        # Check if the file includes motor unit spike events
        mu_df: pd.DataFrame = df[df["description"] == "motor-unit-spike"]

        if len(mu_df) == 0:
            errors.append(
                self._itemize(
                    code="DERIVATIVES_MISSING_MU_SPIKE_EVENTS",
                    location=file,
                    severity="error"
                )
            )
            return False, errors

        # Check if all onset values are numeric values and larger than zero
        if not np.issubdtype(mu_df["onset"].dtype, np.number):
            errors.append(
                self._itemize(
                    code="DERIVATIVES_ONSET_MUST_BE_NUMERIC",
                    location=file,
                    severity="error"
                )
            )
        else:
            invalid: pd.Series[bool] = mu_df["onset"] < 0

            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="DERIVATIVES_ONSET_NOT_LARGER_ZERO",
                        severity="error",
                        location=file
                    )
                )

        # Check if the duration of all motor unit spikes is zero
        invalid: pd.Series[bool] = mu_df["duration"] != 0

        if invalid.any():
            # bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                self._itemize(
                    code="DERIVATOVES_DURATION_NOT_ZERO",
                    severity="error",
                    location=file
                )
            )

        # Check if the sample columns contains only integers
        if not np.issubdtype(mu_df["sample"].dtype, np.integer):

            invalid: pd.Series[bool] = np.mod(mu_df["sample"], 1) != 0

            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="DERIVATIVES_SAMPLE_MUST_BE_INTEGER",
                        location=file,
                        severity="error"
                    )
                )

        # Check if the unit_id is always an integer
        if not np.issubdtype(mu_df["unit_id"].dtype, np.integer):

            invalid: pd.Series[bool] = np.mod(mu_df["unit_id"], 1) != 0

            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="DERIVATIVES_ID_MUST_BE_INTEGER",
                        location=file,
                        severity="error"
                    )
                )

        # Final validation
        is_valid = len(errors) == 0

        return is_valid, errors
    
    def validate_events(self, path: str, derivative: bool) -> None:
        """
        Validates existence and contents of events.tsv conditioned on whether
        the recording is a derivative (e.g. spike train labels) or raw data.
        In essence, for every non-derivative recording-sidecar (*_emg.json), there needs to 
        exist a *_events.tsv file containing at least the values muscle_on muscle_off
        in the column event_type. In case of the sidecar belonging to a derivative,
        _validate_label_file() is called.

        Args:
            sidecar_path (str): sidecar path from which the corresponding events path is derived.
            derivative (bool): indicates whether to check validity of label files.

        Raises:
            NotImplementedError: _description_
        """
        # noise recordings do not require event-files
        # TODO check filename conventions (degree of adoption)
        if "baselinenoise" in path:
            return None
        
        elif derivative:
            assert path.endswith("_events.tsv"), "Eventsfile not a derivative"
            _, errors = self._validate_label_file(path)
            self.errors += errors
            return None
        
        events_path: str = path.replace("_emg.json", "_events.tsv")
        if not os.path.exists(events_path):
            self.errors.append(
                self._itemize(
                    code="MISSING_EVENTS_FILE",
                    severity="error",
                    location=path
                )
            )
        else:
            try:
                df: pd.DataFrame = pd.read_csv(events_path, sep="\t")
            except:
                self.errors.append(
                    self._itemize(
                        code="UNREADABLE_EVENTS_TSV_FORMAT",
                        location=events_path,
                        severity="error"
                    )
                )
                return None

            values: list[str] = list(df["event_type"].unique())
            if len(df) == 0:
                self.errors.append(
                    self._itemize(
                        code="EVENT_TSV_WITHOUT_DATA",
                        location=events_path,
                        severity="error"
                    )
                )
            # TODO might already be caught by BIDS Validator
            elif not "muscle_on" and not "muscle_off" in values:
                self.errors.append(
                    self._itemize(
                        code="EVENT_TSV_MISSING_EVENT_TYPE",
                        location=events_path,
                        severity="error"
                    )
                )
        
        return None

    def validate(self) -> tuple[list, bool]:
        # dataset level checks
        self.validate_ethics_approval()

        # recording level checks
        for root, _, files in os.walk(self.dataset):
            for file in files:
                full_path: str = os.path.join(root, file)
                relative_path: str = self._relative_path(full_path)
                if file.endswith("emg.json"):
                    sidecar: dict = self._load_json(full_path)
                    self.validate_sampling_frequency(sidecar=sidecar, path=relative_path)
                    self.validate_cede(sidecar=sidecar, path=relative_path)
                    self.validate_events(path=full_path, derivative=False)
                elif "derivatives/" in full_path and full_path.endswith("_events.tsv"):
                    self.validate_events(path=full_path, derivative=True)

        return self.errors, self.valid


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
            warnings=self.warnings
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

        custom_errors, _ = self.custom_validator.validate()

        self.errors = errors + custom_errors
        self.warnings = warnings  # currently no custom warnings implemented

        return self.errors, self.warnings, self.valid
