from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY


@DATASET_REGISTRY.register("gandalf_dataset")
class GandalfDataset(Dataset):
    def __init__(self, 
                 role: Union[Literal["Infiltrator"], Literal["Sentinel"]], 
                 filename: str,
                 num_examples: int) -> None:
        super().__init__(output_key="message")
        self.role = role
        self.filename = filename
        self.num_examples = num_examples

    def _load_examples(self):
        examples = []
        
        with open(self.filename, 'r') as f:
            counter = 0
            for line in f:
                examples.append(json.loads(line))
                counter += 1
                if counter >= self.num_examples:
                    break
        
        return examples

    def get_dataset(self) -> Iterable[Example]:
        examples = self._load_examples()
        dataset = []
        for example in examples:
            if self.role == "Sentinel":
                example = Example(role=self.role,
                                  message=f"You will move as {self.role}",
                                  conversation=example['conversation'],
                                  secret_password=example['secret_password'],
                                  response=example['sentinel_response']
                                  ).with_inputs("role", "message", "conversation", "secret_password")
            else:  # Infiltrator
                example = Example(role=self.role,
                                  message=f"You will move as {self.role}",
                                  conversation=example['conversation'],
                                  response=example['infiltrator_response']
                                  ).with_inputs("role", "message", "conversation")
            dataset.append(example)
        return dataset