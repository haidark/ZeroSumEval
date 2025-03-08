from typing import Dict, List, Tuple

from zero_sum_eval.managers.matchers.base import Matcher
import itertools

class RoundRobin(Matcher):
    def __init__(self, llm_elos: Dict[str, int], players_per_match: int = 2, max_rounds: int = 5):
        super().__init__(llm_elos=llm_elos)
        self.max_rounds = max_rounds
        self.round = 0
        self.match_index = 0
        self.players_per_match = players_per_match
        self.matches = self._generate_round_robin_matches()

    def _generate_round_robin_matches(self) -> List[Tuple[str, ...]]:
        participants = list(self.llm_elos.keys())
        # Assumes the order matters
        schedule = list(itertools.permutations(participants, self.players_per_match))
        return schedule

    def get_next_match(self) -> Tuple[str, ...]:
        if self.match_index >= len(self.matches):
            self.match_index = 0
            self.round += 1

        next_match = self.matches[self.match_index]
        self.match_index += 1
        return next_match
