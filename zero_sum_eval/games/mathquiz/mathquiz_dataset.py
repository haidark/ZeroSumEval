from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY
from zero_sum_eval.games.mathquiz.mathquiz_player import TEACHER_KEY, STUDENT_KEY

@DATASET_REGISTRY.register("mathquiz_dataset")
class MathQuizDataset(Dataset):
    def __init__(self, 
                player_key: Union[Literal[TEACHER_KEY], Literal[STUDENT_KEY]], 
                filename: str,
                num_examples: int) -> None:
        super().__init__(output_key="math_question" if player_key == TEACHER_KEY else "answer")
        self.player_key = player_key
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
            if self.player_key == TEACHER_KEY:
                example = Example(target=example['answer'],
                                  question=example['question']
                                  ).with_inputs("target")
            else: 
                example = Example(question=example['question'],
                                  answer=example['answer']
                                  ).with_inputs("question")
            dataset.append(example)
        return dataset