import json
import warnings
import os
import sys
import subprocess

from scoring.base import Validator


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
            print(f"Number of detected errors (BIDS Validator): {len(errors)}")
            print(json.dumps(errors, indent=4))
        if print_warnings:    
            print(f"Number of detected warnings (BIDS Validator): {len(warnings)}")
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