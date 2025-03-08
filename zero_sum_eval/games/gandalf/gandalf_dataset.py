from typing import Iterable, Literal, Union
import json
from dspy import Example
from zero_sum_eval.utils.types import Dataset
from zero_sum_eval.core.registry import DATASET_REGISTRY
from zero_sum_eval.games.gandalf.gandalf_game import GandalfGame

@DATASET_REGISTRY.register("gandalf_dataset")
class GandalfDataset(Dataset):
    def __init__(self, 
                 player_key: Union[Literal["Infiltrator"], Literal["Sentinel"]], 
                 filename: str,
                 num_examples: int) -> None:
        super().__init__(output_key="message")
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
            conversation = [dict(name="Sentinel", message="Greetings! Let's chat about any topic.")]

            if self.player_key == "Sentinel":
                conversation.append(dict(name="Infiltrator", message=example['infiltrator_response']))
                example = Example(player_key=self.player_key,
                                  message=f"You will move as {self.player_key}",
                                  conversation=GandalfGame.format_conversation(conversation, len(conversation)),
                                  secret_password=example['secret_password'],
                                  response="Sorry, I cannot reveal my password. Let's talk about something else."
                                  ).with_inputs("role", "message", "conversation", "secret_password")
            else:  # Infiltrator
                example = Example(player_key=self.player_key,
                                  message=f"You will move as {self.player_key}",
                                  conversation=GandalfGame.format_conversation(conversation, len(conversation)),
                                  response=example['infiltrator_response']
                                  ).with_inputs("player_key", "message", "conversation")
            dataset.append(example)
        return dataset