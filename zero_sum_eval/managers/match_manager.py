import csv
from abc import ABC, abstractmethod
from typing import List, Dict

from logging import getLogger
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY, LM_REGISTRY
from .game_manager import GameManager
from tabulate import tabulate
from collections import defaultdict
from copy import copy

import dspy


class Matcher(ABC):
    def __init__(self, llm_elos: List[Dict[str, int]]):
        self.llm_elos = llm_elos
    
    @abstractmethod
    def get_next_match():
        raise NotImplementedError()
    
# TODO: only handles 2 player games for now
class RoundRobin(Matcher):
    def __init__(self, llm_elos: Dict[str, int], max_rounds: int = 5):
        super().__init__(llm_elos=llm_elos)
        self.max_rounds = max_rounds
        self.round = 0
        self.pair_index = 0
        self.matches = self._generate_round_robin_pairs()

    def _generate_round_robin_pairs(self):
        participants = list(self.llm_elos.keys())
        num_participants = len(participants)
        if num_participants % 2 == 1:
            participants.append(None)  # Add a dummy participant for odd numbers

        schedule = []
        for round in range(num_participants):
            round_pairs = []
            for i in range(num_participants // 2):
                if participants[i] is not None and participants[-(i+1)] is not None:
                    round_pairs.append((participants[i], participants[-(i+1)]))
            participants.insert(0, participants.pop())  # Rotate
            schedule.extend(round_pairs)

        return schedule

    def get_next_match(self):
        if self.pair_index >= len(self.matches):
            # Reset matches
            self.pair_index = 0
            self.round += 1

        next_match = self.matches[self.pair_index]
        self.pair_index += 1
        return next_match

class MatchManager:
    def __init__(self, config):
        self.config = config
        self.match_manager_args = config["manager"]["match_manager_args"]
        self.game_manager_args = config["manager"]["game_manager_args"]
        self.llm_elos = {llm["name"]: self.match_manager_args["starting_elo"] for llm in config["llms"]}
        self.llm_configs = {llm["name"]: llm for llm in config["llms"]}
        self.llm_wdl = {llm["name"]: {"wins": 0, "losses": 0, "draws": 0} for llm in config["llms"]}
        
        self.players = dict()
        self.roles = dict()
        
        if matching := self.match_manager_args["matching"]:
            if matching == "round_robin":
                self.matcher = RoundRobin(self.llm_elos)
            else:
                raise ValueError(f"Matching strategy {matching} not defined.")
        else:
            # default is round robin
            self.matcher = RoundRobin(self.llm_elos)

        self.max_matches = self.match_manager_args["max_matches"]
        
        self.out_csv_path = self.match_manager_args["out_csv_path"]

    def _build_game_manager(self, lms: List[str]):
        config = defaultdict(dict)
        config["game"] = copy(self.config["game"])
        for lm_name, player_config in zip(lms, config["game"]["players"]):
            player_config["args"]["lm"] = self.llm_configs[lm_name]
        
        config["manager"]["args"] = self.config["manager"]["game_manager_args"]

        return GameManager(config)

    def calculate_elo_rating(self, rating_a, rating_b, result_a, k=32):
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

    def display_leaderboard(self):
        table_data = []
        headers = ['Model', 'Elo', 'Wins', 'Draws', 'Losses']
        
        for model, elo in self.llm_elos.items():
            wins = self.llm_wdl[model]['wins']
            losses = self.llm_wdl[model]['losses']
            draws = self.llm_wdl[model]['draws']
            table_data.append([model, f"{elo:.2f}", wins, draws, losses])
        
        print(tabulate(table_data, headers, tablefmt="grid"))
        

    def save_leaderboard(self):
        headers = ['Model', 'Elo', 'Wins', 'Draws', 'Losses']
        with open(self.out_csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for model, elo in self.llm_elos.items():
                wins = self.llm_wdl[model]['wins']
                losses = self.llm_wdl[model]['losses']
                draws = self.llm_wdl[model]['draws']
                writer.writerow([model, f"{elo:.2f}", wins, draws, losses])

    def start(self):
        print("Let the games begin!")
        for _ in range(self.max_matches):
            # Get next matchup
            lms = self.matcher.get_next_match()

            # Reset game
            game_manager = self._build_game_manager(lms)

            assert len(lms) == len(game_manager.games[-1].roles), "The number of matched LMs must be the same as the number of players required in the game."
            
            print(" VS ".join(lms))
            
            final_game_state = game_manager.start()
            
            # Get which LM's turn the game stopped at
            cur_lm_turn = self.roles[final_game_state.roles[0]]
            
            if final_game_state.is_win():
                result_a = 1 if cur_lm_turn == lms[0] else 0
                self.llm_wdl[cur_lm_turn]["wins"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["losses"] += 1 
            elif final_game_state.is_draw():
                result_a = 0.5
                self.llm_wdl[cur_lm_turn]["draws"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["draws"] += 1 
            else:
                # Loss to current LM because they made the state invalid (exceeded max_tries)
                result_a = 0 if cur_lm_turn == lms[0] else 1
                self.llm_wdl[cur_lm_turn]["losses"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["wins"] += 1 

            # Update elos of LMs
            self.llm_elos[lms[0]], self.llm_elos[lms[1]] = self.calculate_elo_rating(self.llm_elos[lms[0]], self.llm_elos[lms[1]], result_a)
            
            self.display_leaderboard()
            self.save_leaderboard()

        return self.llm_elos, self.llm_wdl
