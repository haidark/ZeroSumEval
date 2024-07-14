from typing import Iterable, Iterator
from abc import ABC, abstractmethod
from dspy import Example
from functools import cache


class Dataset(ABC):
    def __init__(self, output_key: str) -> None:
        # the key of the output field for each example
        self.output_key = output_key

    @abstractmethod
    def get_dataset(self) -> Iterable[Example]:
        pass
