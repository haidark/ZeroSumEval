import csv
import os
from abc import ABC, abstractmethod
from typing import List, Dict

from logging import getLogger
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY, LM_REGISTRY
from .game_manager import GameManager
from tabulate import tabulate
from collections import defaultdict
from copy import copy

import dspy
import time
import itertools
import json


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

class MatchManager:
    def __init__(self, config):
        self.config = config
        self.match_manager_args = config["manager"]["match_manager_args"]
        self.game_manager_args = config["manager"]["game_manager_args"]
        
        self.players = dict()
        self.roles = dict()
        self.logger = getLogger()

        self.max_matches = self.match_manager_args["max_matches"]
        
        self.output_dir = config['logging']['output_dir']

        self.llm_configs = {llm["name"]: llm for llm in config["llms"]}

        # initialize llm_elos from {output_dir}/leaderboard.csv if it exists
        self.initialize_leaderboard()

        # Initialize the matching strategy
        if matching := self.match_manager_args["matching"]:
            if matching == "round_robin":
                self.matcher = RoundRobin(self.llm_elos)
            else:
                raise ValueError(f"Matching strategy {matching} not defined.")
            self.logger.info(f"Scheduled matches: {self.matcher.matches}")
        else:
            # default is round robin
            self.matcher = RoundRobin(self.llm_elos)

    def initialize_leaderboard(self):
        """
        Initializes the leaderboard by reading data from a CSV file and populating the `llm_elos` and `llm_wdl` dictionaries.
        If the CSV file does not exist, the `llm_elos` and `llm_wdl` dictionaries are initialized with default values.
        """
        self.llm_elos = dict()
        self.llm_wdl = dict()

        leaderboard_path = os.path.join(self.output_dir, 'leaderboard.csv')
        if os.path.exists(leaderboard_path):
            with open(leaderboard_path, mode='r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    model, elo, wins, draws, losses = row
                    self.llm_elos[model] = float(elo)
                    self.llm_wdl[model] = {"wins": int(wins), "draws": int(draws), "losses": int(losses)}

        # Initialize llm_elos from config if not already initialized
        for model in self.config["llms"]:
            if model["name"] not in self.llm_elos:
                self.llm_elos[model["name"]] = self.match_manager_args["starting_elo"]
                self.llm_wdl[model["name"]] = {"wins": 0, "draws": 0, "losses": 0}


    def _build_game_manager(self, lms: List[str], turn_dir):
        config = defaultdict(dict)
        config["game"] = copy(self.config["game"])
        self.roles = dict()
        for lm_name, player_config in zip(lms, config["game"]["players"]):
            self.roles[player_config["args"]["roles"][0]] = lm_name
            player_config["args"]["lm"] = self.llm_configs[lm_name]
        
        config["manager"]["args"] = self.config["manager"]["game_manager_args"]
        config["logging"]["output_dir"] = turn_dir

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
        for line in tabulate(table_data, headers, tablefmt="grid").split('\n'):
            self.logger.info(line)
        

    def save_leaderboard(self, path = "leaderboard.csv"):
        headers = ['Model', 'Elo', 'Wins', 'Draws', 'Losses']
        with open(os.path.join(self.output_dir, path), mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for model, elo in self.llm_elos.items():
                wins = self.llm_wdl[model]['wins']
                losses = self.llm_wdl[model]['losses']
                draws = self.llm_wdl[model]['draws']
                writer.writerow([model, f"{elo:.2f}", wins, draws, losses])

    def start(self):
        self.logger.info("Let the games begin!")

        os.makedirs(os.path.join(self.output_dir, "leaderboard_history"), exist_ok=True)
        self.save_leaderboard(f"leaderboard_history/leaderboard_{int(time.time())}.csv")
        
        for _ in range(self.max_matches):
            # Get next matchup
            lms = self.matcher.get_next_match()
            # Reset game
            turn_dir = os.path.join(self.output_dir, f"matches/{lms[0]}_vs_{lms[1]}_{int(time.time())}")
            os.makedirs(turn_dir, exist_ok=True)

            game_manager = self._build_game_manager(lms=lms, turn_dir=turn_dir)

            assert len(lms) == len(game_manager.games[-1].roles), "The number of matched LMs must be the same as the number of players required in the game."
            
            self.logger.info(" VS ".join(lms))
            
            final_game_state = game_manager.start()
            
            # Get which LM's turn the game stopped at
            cur_lm_turn = self.roles[final_game_state.roles[0]]
            gm_message = final_game_state.validate_game()
            if gm_message in game_manager.win_conditions:
                result_a = 1 if cur_lm_turn == lms[0] else 0
                self.llm_wdl[cur_lm_turn]["wins"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["losses"] += 1 
                self.logger.info(f"Match {cur_lm_turn} won! GM message: {gm_message}")
            elif gm_message in game_manager.draw_conditions:
                result_a = 0.5
                self.llm_wdl[cur_lm_turn]["draws"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["draws"] += 1 
                self.logger.info(f"Match ended in a draw! GM message: {gm_message}")
            else:
                # Loss to current LM because they made the state invalid (exceeded max_tries)
                result_a = 0 if cur_lm_turn == lms[0] else 1
                self.llm_wdl[cur_lm_turn]["losses"] += 1
                self.llm_wdl[self.roles[final_game_state.roles[1]]]["wins"] += 1 
                self.logger.info(f"Match {cur_lm_turn} lost! GM message: {gm_message}")

            elos_before = copy(self.llm_elos)

            # Update elos of LMs
            self.llm_elos[lms[0]], self.llm_elos[lms[1]] = self.calculate_elo_rating(self.llm_elos[lms[0]], self.llm_elos[lms[1]], result_a)
            
            with open(os.path.join(turn_dir, "elos_delta.json"), mode='w', newline='') as f:
                obj = {lm: [elos_before[lm], self.llm_elos[lm]] for lm in lms}
                json.dump(obj, f)

            self.display_leaderboard()
            self.save_leaderboard()

        return self.llm_elos, self.llm_wdl
