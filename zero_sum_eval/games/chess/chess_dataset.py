from typing import Iterable, Literal, Optional, Union
import json
from dspy import Example
import re
import chess
from datasets import load_dataset
from zero_sum_eval.dataset import Dataset
from zero_sum_eval.registry import DATASET_REGISTRY


@DATASET_REGISTRY.register("chess_dataset")
class ChessDataset(Dataset):
    def __init__(self, filename: str, player_key: str, num_examples: Optional[int] = None) -> None:
        super().__init__(output_key="move")
        self.filename = filename
        self.player_key = player_key
        self.num_examples = num_examples

    def _load_examples(self):
        examples = []
        with open(self.filename, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        return examples

    def get_dataset(self) -> Iterable[Example]:
        examples = self._load_examples()
        dataset = []
        num_examples = self.num_examples if self.num_examples else len(examples)
        for example in [examples[i] for i in range(0, num_examples, num_examples//10)]:
            if self.player_key == "White": # white to move
                if not example['turn']:
                    continue
            else:                   # black to move
                if example['turn']:
                    continue
            example = Example(message=f"You will move as {self.player_key}",
                                    board_state=example['board_state'],
                                    player_key=f"{self.player_key}",
                                    history=example['history'],
                                    move=example['move']
                                    ).with_inputs("message", "board_state", "player_key", "history")
            dataset.append(example)
        return dataset
    
@DATASET_REGISTRY.register("chess_puzzle_dataset")
class ChessPuzzleDataset(Dataset):
    def __init__(self, player_key: str, num_examples: int = 20) -> None:
        super().__init__(output_key="move")
        self.player_key = player_key
        self.num_examples = num_examples

    def _get_board(self, ex: dict) -> chess.Board:
        board = chess.Board()
        moves = re.findall(r"\d+\.+\s(.+?)\s", ex["ctx"])
        for move in moves:
            board.push_san(move)
        return board

    def get_dataset(self) -> Iterable[Example]:
        ds = load_dataset("EleutherAI/lichess-puzzles", streaming=True)
        examples = []
        for ex in ds["train"].take(self.num_examples):
            board = self._get_board(ex)
            if board.turn == (self.player_key == "White"):
                example = Example(  message=f"You will move as {self.player_key}",
                                    board_state=board.fen(),
                                    player_key=f"{self.player_key}",
                                    history=ex["ctx"],
                                    move=ex["target"]
                                    ).with_inputs("message", "board_state", "player_key", "history")
                examples.append(example)
        return examples
