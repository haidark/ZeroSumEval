from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY


@DATASET_REGISTRY.register("mathquiz_dataset")
class MathQuizDataset(Dataset):
    def __init__(self, 
                role: Union[Literal["TeacherGenerateQuestion"], Literal["TeacherAnswerQuestion"], Literal["StudentAnswerQuestion"]], 
                filename: str,
                num_examples: int) -> None:
        super().__init__(output_key="math_question" if role == "TeacherGenerateQuestion" else "answer")
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
            if self.role == "TeacherGenerateQuestion":
                example = Example(role=self.role,
                                  message=f"You will move as {self.role}",
                                  target=example['answer'],
                                  question=example['question']
                                  ).with_inputs("role", "message", "target")
            else: 
                example = Example(role=self.role,
                                  message=f"You will move as {self.role}",
                                  question=example['question'],
                                  answer=example['answer']
                                  ).with_inputs("role", "message", "question")
            dataset.append(example)
        return dataset