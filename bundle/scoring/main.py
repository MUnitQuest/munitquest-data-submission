import sys
import os
import subprocess

from scoring.data_validation import MUnitQuestDataSubmissionValidator as Validator


def main() -> None:    
    assert len(sys.argv) == 3, "Usage: python main.py <input_path> <output_path>"

    input_path: str = sys.argv[1]
    output_path: str = sys.argv[2]

    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")

    # dataset name will be the only directory at the root of input_path
    dataset_name: str = os.listdir(input_path)[0]
    dataset_path: str = os.path.join(input_path, dataset_name)
    print(f"Dataset path: {dataset_path}")

    validator: Validator = Validator(dataset_path)

    # generate validation config
    config_path: str = "bids_validation_config.json"
    validator.validation_config(config_path)

    errors, warnings, valid = validator.run_bids_validator(
        print_errors=True,
        print_warnings=True,
        config_path=config_path,
    )
    validator.write_scores(os.path.join(output_path, "scores.json"))
    validator.generate_report(os.path.join(output_path, "detailed_results.html"))


if __name__ == "__main__":
    main()
