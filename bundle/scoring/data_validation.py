import json

from report import MUnitQuestDataSubmissionReport
from dataclasses import dataclass


@dataclass
class ValidationItem:
    """ data class for custom validation layer error and warning items """
    code: str  # custom code for the type of error/warning
    severity: str  # error or warning
    location: str  # filepath of the issue
    origin: str = "BIDS Validator"  # BIDS validator or MUnitQuest
    rule: str = "N/A"  # TODO


class MUnitQuestDataSubmissionValidator:

    def __init__(self):
        raise NotImplementedError
        self.metrics: dict[str, float] = {
            "valid": 0.
        }
    
    def write_scores(self, path: str) -> None:
        # has to be written to scores.json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=4)
