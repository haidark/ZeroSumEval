from typing import Iterable, Literal, Union
import json
import re
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY

@DATASET_REGISTRY.register("pyjail_dataset")
class PyJailDataset(Dataset):
    def __init__(self, filename: str, role: Union[Literal["DefenderGenerateCode"], Literal["DefenderSolveCode"], Literal["AttackerSolveCode"]]) -> None:
        super().__init__(output_key="code")
        self.filename = filename
        self.role = role

    def _load_examples(self):
        examples = []
        with open(self.filename, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        return examples

    def _extract_code(self, source_code):
        match = re.search(r'###START(.*?)###END', source_code, re.DOTALL)
        return match.group(1).strip() if match else source_code

    def get_dataset(self) -> Iterable[Example]:
        examples = self._load_examples()
        dataset = []
        for example in examples:
            if self.role == "DefenderGenerateCode":
                example_data = Example(
                    role=self.role,
                    message="Generate PyJail code that makes access harder to the FLAG environment variable",
                    history=[],
                    code=example['source_code']
                ).with_inputs("role", "message", "history")
            elif self.role == "DefenderSolveCode":
                example_data = Example(
                    role=self.role,
                    message="Given PyJail code, generate a solution to access the FLAG environment variable",
                    pyjail_code=example['source_code'],
                    history=[],
                    code=f"###START\n{example['solution']}\n###END"
                ).with_inputs("role", "message", "pyjail_code", "history")
            elif self.role == "AttackerSolveCode":
                example_data = Example(
                    role=self.role,
                    message="Generate a solution to access the FLAG environment variable in a PyJail challenge",
                    history=[],
                    code=f"###START\n{example['solution']}\n###END"
                ).with_inputs("role", "message", "history")
            else:
                continue

            dataset.append(example_data)
        return dataset

