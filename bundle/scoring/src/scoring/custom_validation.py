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
                        location=path,
                        message=f"To adhere to CEDE Matrix, please provide key: {requirement}"
                    )
                )
            elif not isinstance(cede, (int, float)):
                self.errors.append(
                    self._itemize(
                        code=f"CEDE_REQUIREMENT_INVALID_TYPE_{requirement.upper()}",
                        severity="error",
                        location=path,
                        message=f"{requirement} must be of JSON type number (int, float)"
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
                    severity="error",
                    message="No EMG sidecar detected for derivative. Please check file naming conventions"
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
            return False, errors

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
            return False, errors

        # Check if all onset values are numeric values and larger than zero
        if not np.issubdtype(mu_df["onset"].dtype, np.number):
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
                        message="Onset must be > 0"
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
        if not np.issubdtype(mu_df["sample"].dtype, np.integer):

            invalid: pd.Series[bool] = np.mod(mu_df["sample"], 1) != 0

            if invalid.any():
                # bad_idx = mu_df.index[invalid].tolist()
                errors.append(
                    self._itemize(
                        code="DERIVATIVES_SAMPLE_MUST_BE_INTEGER",
                        location=file,
                        severity="error",
                        message="Sample must be of type Integer"
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
                        severity="error",
                        message="Unit ID must be of type Integer"
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
        # noise recording are identified by the presence of rest in task label
        with open(path, "r", encoding="utf-8") as f:
            sidecar: dict = json.load(f)
        task: str = sidecar.get("TaskName", "")
        if "rest" in task.lower():
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
            elif not "muscle_on" and not "muscle_off" in values:
                self.errors.append(
                    self._itemize(
                        code="EVENT_TSV_MISSING_EVENT_TYPE",
                        location=events_path,
                        severity="error",
                        message="Event files must at least be containing muscle_on and muscle_off in event_type"
                    )
                )
        
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

    def validate(self, print_errors: bool=False) -> tuple[list, bool]:
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
            
            # check for existence of electrodes.tsv for non-derivatives
            # electrodes.tsv should exist per subject/session
            if root.split("/")[-1] == "emg" and not "derivatives" in root:
                self.validate_electrodes(path=root)
        
        if print_errors:
            print(f"Number of errors detected by custom validation: {len(self.errors)}")
            print(json.dumps(self.errors, indent=4))

        return self.errors, self.valid
