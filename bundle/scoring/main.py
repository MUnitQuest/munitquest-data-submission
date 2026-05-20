import sys
import os
import subprocess

from data_validation import MUnitQuestDataSubmissionValidator


def INSTALL(dep: str) -> None:
    """
    (HELPER) Installs a dependency at runtime.
    Args:
        dep (str): name of python package to be installed
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])


if __name__ == "__main__":
    # important on remote server
    try:
        import bids_validator
    except ImportError as ie:
        print("bids_validator not found, installing...")
        INSTALL("bids-validator-deno")
    
    assert len(sys.argv) == 3, "Usage: python main.py <input_path> <output_path>"

    input_path: str = sys.argv[1]
    output_path: str = sys.argv[2]

    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")

    dataset_path: str = os.path.join(input_path, "Caillet")
    print(f"Dataset path: {dataset_path}")

    validator: MUnitQuestDataSubmissionValidator = MUnitQuestDataSubmissionValidator(dataset_path)
    errors, warnings, valid = validator.run_bids_validator(
        print_errors=True,
        print_warnings=True,
        # config_path="bidsValidatorConfig.json",
        config_path=None,
    )
    validator.write_scores(os.path.join(output_path, "scores.json"))
    validator.generate_report(os.path.join(output_path, "detailed_results.html"))
