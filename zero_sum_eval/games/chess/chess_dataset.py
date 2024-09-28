from typing import Iterable, Literal, Union
import json
from dspy import Example
import re
import chess
from datasets import load_dataset
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
    
@DATASET_REGISTRY.register("chess_puzzle_dataset")
class ChessPuzzleDataset(Dataset):
    def __init__(self, role: Union[Literal["White"], Literal["Black"]], num_samples: int = 20) -> None:
        super().__init__(output_key="move")
        self.role = role
        self.num_samples = num_samples

    def _get_board(self, ex: dict) -> chess.Board:
        board = chess.Board()
        moves = re.findall(r"\d+\.+\s(.+?)\s", ex["ctx"])
        for move in moves:
            board.push_san(move)
        return board

    def get_dataset(self) -> Iterable[Example]:
        ds = load_dataset("EleutherAI/lichess-puzzles", streaming=True)
        examples = []
        for ex in ds["train"].take(self.num_samples):
            board = self._get_board(ex)
            if board.turn == (self.role == "White"):
                example = Example(  message=f"You will move as {self.role}",
                                    board_state=board.fen(),
                                    role=f"{self.role}",
                                    history=ex["ctx"],
                                    move=ex["target"]
                                    ).with_inputs("message", "board_state", "role", "history")
                examples.append(example)
        return examples
