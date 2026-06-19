import os
import re
import json
import pandas as pd
import numpy as np

from scoring.base import Validator, ValidationItem
from dataclasses import asdict


class MUnitQuestCustomValidator(Validator):
    """ class for custom validation on top of BIDS validation results."""

    def __init__(self, dataset: str):
        super().__init__(dataset)
        self.dataset_sidecar: dict = self._load_json(os.path.join(self.dataset, "dataset_description.json"))
        self.derivative_events: list[str] = self._list_derivative_events()
        
        # As an additional metric, we investigate the average number of detected
        # MUs per recording. Therefore, we are curating a list of all detected unique
        # MU ids accross the derivative events files, which we can then relate to the number of recordings.
        self.labelled_mus: list[int] = []

    def _itemize(self, code: str, severity: str, location: str, message: str) -> dict[str, str]:
        item: ValidationItem = ValidationItem(
            code=code,
            severity=severity,
            location=self._relative_path(location),
            origin="MUnitQuest Custom Validator",
            issueMessage=message
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
                    severity="error",
                    message="Derivative file does not match any recording. The filename needs to adhere to BIDS"
                )
            )
        
        component_dict: dict[str, str] = matched.groupdict()
        bids_components: list[str] = []
        for k, v in component_dict.items():
            if v is not None:
                bids_components.append(f"{k}-{v}")
        bids_filename: str = ("_").join(bids_components)

        return bids_filename
    
    def _list_derivative_events(self) -> list[str]:
        """
        Helper method to list all derivative events files in the dataset.

        Returns:
            list[str]: list of paths to derivative events files.
        """
        events: list[str] = []
        for root, _, files in os.walk(self.dataset):
            for file in files:
                full_path: str = os.path.join(root, file)
                if "derivatives/" in full_path and full_path.endswith("_events.tsv"):
                    events.append(full_path)
        
        return events
    
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
                    location=path,
                    message=f"Sampling frequency must be at least 2000 Hz. Your sampling frequency: {fsamp}"
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
                    location="/dataset_description.json",
                    message="MUnitQuest submissions require Ethics Approval(s)"
                )
            )
        elif not isinstance(ethics_approvals, list):
            self.errors.append(
                self._itemize(
                    code="INVALID_ETHICS_APPROVAL_TYPE",
                    severity="error",
                    location="/dataset_description.json",
                    message="EthicsApprovals must be of JSON type array"
                )
            )
        elif len(ethics_approvals) == 0:
            self.errors.append(
                self._itemize(
                    code="MISSING_ETHICS_APPROVAL",
                    severity="error",
                    location="/dataset_description.json",
                    message="EthicsApproval is empty"
                )
            )
        
        return None
    
    def validate_cede(self, sidecar: dict, path: str, requirements: list[str] = ["Gain", "Preamplification"]) -> None:
        """
        Validates for existence of CEDE requirements. In our case, we are
            validating towards Gain and Preamplification. Thereof, at least one of the
            requirements needs to be provided to adhere to the CEDE Matrix.

        Args:
            sidecar (dict): sidecar to check.
            path (str): location for export.
            requirements (list[str]): keys to check existence for. Defaults to ["Gain", "Preamplification"].
        """
        exists: list[str] = [req for req in requirements if req in sidecar and sidecar[req] is not None]
        if len(exists) == 0:
            self.errors.append(
                self._itemize(
                    code="CEDE_REQUIREMENTS_MISSING",
                    severity="error",
                    location=path,
                    message=f"To adhere to CEDE Matrix, at least one of the following keys needs to be provided: {requirements}"
                )
            )

            return None
        
        for cede in exists:
            value = sidecar[cede]
            if not isinstance(value, (int, float)):
                self.errors.append(
                    self._itemize(
                        code=f"CEDE_REQUIREMENT_INVALID_TYPE_{cede.upper()}",
                        severity="error",
                        location=path,
                        message=f"{cede} must be of JSON type number (int, float)"
                    )
                )

        if len(exists) == 1:
            missing: str = list(set(requirements) - set(exists))[0]
            self.warnings.append(
                self._itemize(
                    code=f"CEDE_REQUIREMENT_MISSING_{missing.upper()}",
                    severity="warning",
                    location=path,
                    message=f"To adhere to CEDE Matrix, it is recommended to provide {missing} in addition to {cede}"
                )
            )
        
        return None
    
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

            warnings : list of str
                List of validation warning messages.    
        """
        errors: list[dict] = []
        warnings: list[dict] = []
        # Define required column names
        required_columns: set[str] = {
            "onset",
            "duration",
            "sample",
            "unit_id",
            "description",
        }

        # Load the file
        try:
            df: pd.DataFrame = pd.read_table(file)
        except:
            errors.append(
                self._itemize(
                    code="UNREADABLE_EVENTS_TSV_FORMAT",
                    location=file,
                    severity="error",
                    message=f"Error when reading {file}. Please validate file format"
                )
            )
            return False, errors
        
        # Check if required columns are present
        missing: set[str] = required_columns - set(df.columns)

        if missing:
            errors.append(
                self._itemize(
                    code="DERIVATIVES_MISSING_EVENT_COLUMN",
                    location=file,
                    severity="error",
                    message=f"Missing required columns: {sorted(missing)}"
                )
            )

            # Cannot continue safely
            return False, errors, warnings
        
        # Check if the events.tsv file is empty
        if len(df) == 0:
            warnings.append(
                self._itemize(
                    code="EMPTY_LABEL_FILE",
                    location=file,
                    severity="warning",
                    message="The spike label file is empty. Make sure that this is correct."
                )
            )
            return True, errors, warnings


        # Check if the file includes motor unit spike events
        mu_df: pd.DataFrame = df[df["description"] == "motor-unit-spike"]

        if len(mu_df) == 0:
            errors.append(
                self._itemize(
                    code="DERIVATIVES_MISSING_MU_SPIKE_EVENTS",
                    location=file,
                    severity="error",
                    message="motor-unit-spike missing in event description column"
                )
            )
            return False, errors, warnings

        # Check if all onset values are numeric values and larger than zero
        if not pd.api.types.is_numeric_dtype(mu_df["onset"]):
            errors.append(
                self._itemize(
                    code="DERIVATIVES_ONSET_MUST_BE_NUMERIC",
                    location=file,
                    severity="error",
                    message="Onset must be numeric"
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
                        location=file,
                        message="Onset must be >= 0"
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
                    location=file,
                    message="Duration for MU spikes must always be 0"
                )
            )

        # Check if the sample columns contains only integers
        if not pd.api.types.is_integer_dtype(mu_df["sample"]):

            errors.append(
                self._itemize(
                    code="DERIVATIVES_SAMPLE_MUST_BE_INTEGER",
                    location=file,
                    severity="error",
                    message="Sample must be of type Integer"
                )
            )
        else:
            invalid: pd.Series[bool] = mu_df["sample"] < 0
            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="DERIVATIVES_SAMPLE_NOT_LARGER_ZERO",
                        severity="error",
                        location=file,
                        message="Sample must be >= 0"
                    )
                )    

        # Check if the unit_id is always an integer
        if not pd.api.types.is_integer_dtype(mu_df["unit_id"]):

            errors.append(
                self._itemize(
                    code="DERIVATIVES_ID_MUST_BE_INTEGER",
                    location=file,
                    severity="error",
                    message="Unit ID must be of type Integer"
                )
            )
        else:
            invalid: pd.Series[bool] = mu_df["unit_id"] < 0
            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="UNIT_ID_NOT_LARGER_ZERO",
                        severity="error",
                        location=file,
                        message="Unit id must be >= 0"
                    )
                )      

        # Final validation
        is_valid: bool = len(errors) == 0

        # extract unique identifies MUs
        if is_valid:
            n_mus: int = mu_df["unit_id"].nunique()
            self.labelled_mus.append(n_mus)

        return is_valid, errors, warnings
    
    def validate_events(self, path: str) -> None:
        """
        Validates existence and contents of events.tsv.
        In essence, for every non-derivative recording-sidecar (*_emg.json), there needs to 
        exist a *_events.tsv file containing at least the values muscle_on muscle_off
        in the column event_type. Further, for every sidecar, there needs to exist a label file
        as a BIDS derivative.

        Args:
            sidecar_path (str): sidecar path from which the corresponding events path is derived.
        """
        # noise recordings do not require event-files
        # noise recording are identified by the presence of rest in task label
        sidecar: dict = self._load_json(path)
        task: str = sidecar.get("TaskName", "")
        if "rest" in task.lower():
            return None
        
        # check "regular" events file
        events_path: str = path.replace("_emg.json", "_events.tsv")
        if not os.path.exists(events_path):
            self.errors.append(
                self._itemize(
                    code="MISSING_EVENTS_FILE",
                    severity="error",
                    location=path,
                    message="MUnitQuest submissions require eventfiles for every recording (if recording is not baseline noise)"
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
                        severity="error",
                        message=f"Error when reading {events_path}. Please validate file format"
                    )
                )
                return None

            values: list[str] = list(df["event_type"].unique())
            if len(df) == 0:
                self.errors.append(
                    self._itemize(
                        code="EVENT_TSV_WITHOUT_DATA",
                        location=events_path,
                        severity="error",
                        message=f"{events_path} is an empty file"
                    )
                )
            # TODO might already be caught by BIDS Validator
            elif not "muscle_on" in values and not "muscle_off" in values:
                self.errors.append(
                    self._itemize(
                        code="EVENT_TSV_MISSING_EVENT_TYPE",
                        location=events_path,
                        severity="error",
                        message="Event files must at least be containing muscle_on and muscle_off in event_type"
                    )
                )
        
        # check for corresponding label file as derivative
        # extract core filename that must also be contained in derivative filename to create a match
        core_filename: str = path.split("/")[-1].replace("_emg.json", "")
        matching_derivatives: list[str] = [der for der in self.derivative_events if core_filename in der]
        if len(matching_derivatives) == 0:
            self.errors.append(
                self._itemize(
                    code="LABELS_MISSING_FOR_RECORDING",
                    location=path,
                    severity="error",
                    message="No derivative events file detected matching the recording. Please check file naming conventions"
                )
            )
        elif len(matching_derivatives) > 1:
            self.errors.append(
                self._itemize(
                    code="MULTIPLE_LABELS_MATCHING_RECORDING",
                    location=path,
                    severity="error",
                    message="Multiple derivative events files detected matching the recording. Please check file naming conventions"
                )
            )
        else:
            # validate the matching label file
            _, errors, warnings = self._validate_label_file(matching_derivatives[0])
            self.errors += errors
            self.warnings += warnings
        
        return None
    
    def validate_electrodes(self, path: str):
        """
        Validates if a coordinate system is provided, which is enforced
        in the competition. Note, that if an electrodes.tsv file is provided,
        the corresponding metadata-file *coordsystem.json is already inspected
        by the BIDS validator.

        Args:
            path (str): path to check existence
        """
        pattern: re.Pattern = re.compile(r".*_electrodes\.tsv$")
        files: list[str] = [fname for fname in os.listdir(path) if pattern.match(fname)]

        has_electrodes: bool = len(files) > 0
        if not has_electrodes:
            self.errors.append(
                self._itemize(
                    code="ELECTRODES_TSV_MISSING",
                    severity="error",
                    location=path,
                    message="MUnitQuest submissions require definition of electrode coordinates"
                )
            )
        
        for file in files:
            # check readability
            try:
                df: pd.DataFrame = pd.read_csv(os.path.join(path, file), sep="\t")
                if not len(df) > 0:
                    self.errors.append(
                        self._itemize(
                            code="ELECTRODES_TSV_EMPTY",
                            severity="error",
                            location=path,
                            message=f"{file} is an empty file"
                        )
                    )
            except:
                self.errors.append(
                    self._itemize(
                        code="ELECTRODES_TSV_UNREADABLE",
                        severity="error",
                        location=path,
                        message=f"Error when reading {file}. Please validate file format"
                    )
                )

    def validate(self, print_errors: bool=False) -> tuple[list, list, bool]:
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
                    # validate event files: "regular" and labels as derivatives
                    self.validate_events(path=full_path)
            
            # check for existence of electrodes.tsv for non-derivatives
            # electrodes.tsv should exist per subject/session
            if root.split("/")[-1] == "emg" and not "derivatives" in root:
                self.validate_electrodes(path=root)
        
        if print_errors:
            print(f"\nNumber of detected errors (Custom Validator): {len(self.errors)}")
            print(json.dumps(self.errors, indent=4))

        return self.errors, self.warnings, self.valid
