import json
import abc
import os

from dataclasses import dataclass


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
