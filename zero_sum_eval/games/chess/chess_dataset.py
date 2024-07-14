from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY


@DATASET_REGISTRY.register("chess_dataset")
class ChessDataset(Dataset):
    def __init__(self, filename: str, role: Union[Literal["White"], Literal["Black"]]) -> None:
        super().__init__(output_key="move")
        self.filename = filename
        self.role = role

    def _load_examples(self):
        examples = []
        with open(self.filename, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        return examples

    def get_dataset(self) -> Iterable[Example]:
        examples = self._load_examples()
        dataset = []
        for example in [examples[i] for i in range(0, len(examples), len(examples)//10)]:
            if self.role == "White": # white to move
                if not example['turn']:
                    continue
            else:                   # black to move
                if example['turn']:
                    continue
            example = Example(board_state=example['board_state'],
                                    role=f"{self.role}",
                                    history=example['history'],
                                    move=example['move']
                                    ).with_inputs("board_state", "role", "history")
            dataset.append(example)
        return dataset