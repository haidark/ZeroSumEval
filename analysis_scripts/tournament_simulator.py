from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import itertools
from typing import Dict, List, Optional
from log_types import Match, Model, ModelName, OptimizerName
import argparse
import sys

@dataclass
class ModelFilter:
    model_name: ModelName
    with_non_optimized: bool = True
    optimizers: List[OptimizerName] = field(default_factory=lambda: [optimizer.value for optimizer in OptimizerName])

    def is_valid_model(self, model: Model) -> bool:
        if model.name == self.model_name:
            if model.is_optimized:
                return model.optimizer in self.optimizers
            else:
                return self.with_non_optimized
        else:
            return False

class RoleFilter:
    def __init__(self, model_filters: Optional[List[ModelFilter]] = None):
        if model_filters is None:
            self.model_filters = []
            for model_name in ModelName:
                self.model_filters.append(ModelFilter(model_name=model_name))
        else:
            self.model_filters = model_filters
    
    def is_valid_model(self, model: Model) -> bool:
        for model_filter in self.model_filters:
            if model_filter.is_valid_model(model):
                return True
        return False

    @property
    def model_names(self):
        return [model_filter.model_name for model_filter in self.model_filters]

class Matcher(ABC):
    def __init__(self, llm_elos: List[Dict[str, int]]):
        self.llm_elos = llm_elos
    
    @abstractmethod
    def get_next_match():
        raise NotImplementedError()

class RoundRobin(Matcher):
    def __init__(self, llm_elos: Dict[str, int], max_rounds: int = 5):
        super().__init__(llm_elos=llm_elos)
        self.max_rounds = max_rounds
        self.round = 0
        self.pair_index = 0
        self.matches = self._generate_round_robin_pairs()

    def _generate_round_robin_pairs(self):
        participants = list(self.llm_elos.keys())
        schedule = list(itertools.permutations(participants, 2))
        return schedule

    def get_next_match(self):
        if self.pair_index >= len(self.matches):
            # Reset matches
            self.pair_index = 0
            self.round += 1

        next_match = self.matches[self.pair_index]
        self.pair_index += 1
        return next_match

def calculate_elo_rating(rating_a, rating_b, result_a, k=32):
    """
    Calculate new Elo ratings for two players after a match.

    :param rating_a: Current rating of player A
    :param rating_b: Current rating of player B
    :param result_a: Result for player A (1 = win, 0 = loss, 0.5 = draw)
    :param k: K-factor, which determines the impact of the match outcome on the players' ratings
    :return: Tuple of new ratings (new_rating_a, new_rating_b)
    """
    # Calculate expected scores
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))
    
    # Actual scores
    result_b = 1 - result_a  # result_a is 1 if A wins, 0 if A loses, 0.5 if draw
    
    # Calculate new ratings
    new_rating_a = rating_a + k * (result_a - expected_a)
    new_rating_b = rating_b + k * (result_b - expected_b)
    
    return new_rating_a, new_rating_b


class Tournament:
    def __init__(self, match_logs_path: str, role_1_filter: RoleFilter = RoleFilter(), role_2_filter: RoleFilter = RoleFilter(), max_rounds: int = 5):
        self.matches = Match.load_matches(match_logs_path)
        self.role_1_filter = role_1_filter
        self.role_2_filter = role_2_filter
        self.max_rounds = max_rounds
        self.played_matches = set()
        self.llm_elos = {name: 1000 for name in set([*self.role_1_filter.model_names, *self.role_2_filter.model_names])}

    def run(self):
        failed = False
        # for match in self.matches:
        #     if self.model_1_filter.is_valid_model(match.models[0]) and self.model_2_filter.is_valid_model(match.models[1]):
        #         print("Match", match.models[0].name, match.models[1].name, "is valid")
        for i in range(self.max_rounds):
            matcher = RoundRobin(self.llm_elos)
            scheduled_matchups = matcher.matches
            scheduled_matchups = [matchup for matchup in scheduled_matchups if matchup[0] in self.role_1_filter.model_names and matchup[1] in self.role_2_filter.model_names]
            rnd = []
            for matchup in scheduled_matchups:
                non_played_matches = []
                for match in self.matches:
                    if self.role_1_filter.is_valid_model(match.models[0]) and self.role_2_filter.is_valid_model(match.models[1]) and match not in self.played_matches:
                        non_played_matches.append(match)

                if non_played_matches:
                    match = non_played_matches[0]
                    rnd.append(match)
                    self.played_matches.add(match)
                else:
                    print("No more matches to play after round", i)
                    print(f"Failed to find a match for", matchup)
                    print("With filters", self.role_1_filter, self.role_2_filter)
                    failed = True
                    break
            if failed:
                break
            new_llm_elos = self.llm_elos.copy()
            for match in rnd:
                new_rating_winner, new_rating_loser = calculate_elo_rating(self.llm_elos[match.winner.name], self.llm_elos[match.loser.name], 1)
                new_llm_elos[match.winner.name] += new_rating_winner - self.llm_elos[match.winner.name]
                new_llm_elos[match.loser.name] += new_rating_loser - self.llm_elos[match.loser.name]

            print("Round", i+1)
            print(new_llm_elos)
            print()
            self.llm_elos = new_llm_elos

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-path", "-p", help="Path to the match logs file")
    parser.add_argument("--max-rounds", "-r", help="Maximum number of rounds to run the tournament", type=int, default=5)
    args = parser.parse_args()

    # Example: matches between MIPRO-optimized llama, non-optimized Claude, and BSFS-optimized Mistral
    filter_1 = RoleFilter(
        model_filters=[
            ModelFilter(
                model_name=ModelName.llama,
                with_non_optimized=False,
                optimizers=[OptimizerName.mipro]
            ),
            ModelFilter(
                model_name=ModelName.claude,
                with_non_optimized=True,
                optimizers=[]
            ),
            ModelFilter(
                model_name=ModelName.mistral,
                with_non_optimized=False,
                optimizers=[OptimizerName.mipro]
            ),
        ]
    )

    filter_2 = filter_1

    tournament = Tournament(args.logs_path, role_1_filter=filter_1, role_2_filter=filter_2, max_rounds=args.max_rounds)
    tournament.run()