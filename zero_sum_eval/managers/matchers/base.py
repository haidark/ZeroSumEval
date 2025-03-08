from abc import ABC, abstractmethod
from typing import Dict, List

class Matcher(ABC):
    def __init__(self, llm_elos: List[Dict[str, int]]):
        # llm_elos is a dictionary of model names and their corresponding ELO ratings
        self.llm_elos = llm_elos

    @abstractmethod
    def get_next_match():
        raise NotImplementedError()
