from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY


@DATASET_REGISTRY.register("mathquiz_dataset")
class MathQuizDataset(Dataset):
    def __init__(self, 
                role: Union[Literal["MathQuizTeacher"], Literal["MathQuizStudent"]], 
                filename: str,
                num_examples: int) -> None:
        super().__init__(output_key="math_question" if role == "MathQuizTeacher" else "answer")
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
            if self.role == "MathQuizTeacher":
                example = Example(role=self.role,
                                  message=example['message'],
                                  target=example['target'],
                                  math_question=example['math_question']
                                  ).with_inputs("role", "message", "target")
            else:  # MathQuizStudent
                example = Example(role=self.role,
                                  message=example['message'],
                                  question=example['question'],
                                  answer=example['answer']
                                  ).with_inputs("role", "message", "question")
            dataset.append(example)
        return dataset