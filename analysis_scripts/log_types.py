from dataclasses import dataclass
from enum import Enum
from glob import glob
import json
from pathlib import Path
from typing import Dict, List, Optional


class ModelName(Enum):
    llama = "llama3.1-70b"
    claude = "claude-3-5-sonnet"
    gpt4o = "gpt-4o"
    mistral = "mistral-large"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value

class OptimizerName(Enum):
    mipro = "mipro"
    bsfs = "bsfs"

@dataclass
class Model:
    name: ModelName
    is_optimized: bool
    optimizer: Optional[OptimizerName]

    @classmethod
    def from_string(cls, model_string: str) -> 'Model':
        parts = model_string.split('-')
        is_optimized = 'optimized' in parts
        optimizer = None
        if is_optimized:
            for optimizer_name in OptimizerName:
                if optimizer_name.value in parts:
                    optimizer = optimizer_name
            # sometimes the optimizer is not included in the model string, which means it's optimized with mipro
            if not optimizer:
                optimizer = OptimizerName.mipro
                name = ModelName("-".join(parts[:-1]))
            else:
                name = ModelName("-".join(parts[:-2]))
        else:
            optimizer = None
            name = ModelName("-".join(parts[:-1]))
        return cls(name, is_optimized, optimizer)

@dataclass
class Turn:
    environment: Dict
    context: Dict
    roles: List[str]
    formatted_history: str
    validate_game: Optional[str]

    @classmethod
    def from_dict(cls, turn_dict: Dict) -> 'Turn':
        return cls(
            environment=turn_dict['environment'],
            context=turn_dict['context'],
            roles=turn_dict['roles'],
            formatted_history=turn_dict['formatted_history'],
            validate_game=turn_dict['validate_game']
        )

class Match:
    def __init__(self, match_path: str):
        self.path = Path(match_path)
        self.timestamp = int(self.path.name.split('_')[-1])
        self.models = self._parse_models()
        self.results = self._load_results()
        self.turns = self._load_turns()

    def _parse_models(self) -> List[Model]:
        model_strings = self.path.name.split('_vs_')
        # Remove the timestamp from the second model
        model_strings[1] = "_".join(model_strings[1].split("_")[:-1])
        return [Model.from_string(model_string) for model_string in model_strings]

    def _load_results(self) -> Dict:
        try:
            with open(self.path / 'results.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def _load_turns(self) -> List[Turn]:
        turns = []
        try:
            with open(self.path / 'turns.jsonl', 'r') as f:
                for line in f:
                    turn_dict = json.loads(line)
                    turns.append(Turn.from_dict(turn_dict))
        except FileNotFoundError:
            pass
        return turns

    @property
    def winner(self) -> Optional[Model]:
        for model_name, res in self.results.items():
            if res["elos_delta"][1] > res["elos_delta"][0]:
                winner_name = Model.from_string(model_name).name
                return next((model for model in self.models if model.name == winner_name), None)
        return None

    @property
    def loser(self) -> Optional[Model]:
        return next((model for model in self.models if model.name != self.winner), None)

    @property
    def optimized_model(self) -> Optional[Model]:
        return next((model for model in self.models if model.is_optimized), None)

    @staticmethod
    def load_matches(directory: str) -> List["Match"]:
        matches = []
        for match_path in glob(f"{directory}/*/"):
            match = Match(match_path)
            if match.results:
                matches.append(match)
        return matches

    def __str__(self) -> str:
        return f"Match({self.models[0].name} vs {self.models[1].name}, timestamp: {self.timestamp})"
