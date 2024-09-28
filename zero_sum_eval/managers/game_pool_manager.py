
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import copy
from glob import glob
import json
from logging import getLogger
import os
import time
from typing import List

from zero_sum_eval.managers.game_manager import GameManager
from zero_sum_eval.managers.match_manager import RoundRobin


class GamePoolManager:
    def __init__(self, config):
        self.config = config
        self.pool_manager_args = config["manager"]["game_pool_manager_args"]
        self.game_manager_args = config["manager"]["game_manager_args"]
        self.players = dict()
        self.roles = dict()
        self.logger = getLogger()

        self.max_matches = self.pool_manager_args["max_matches"]
        
        self.output_dir = config['logging']['output_dir']
        self.llm_configs = {llm["name"]: llm for llm in config["llms"]}

        self.matcher = RoundRobin({llm["name"]: 1000 for llm in self.config["llms"]})
        self.logger.info(f"Scheduled matches: {self.matcher.matches}")
        self.llm_wdl = {llm["name"]: {"wins": 0, "draws": 0, "losses": 0} for llm in self.config["llms"]}

        self.match_freq = dict()
        for matchup in self.matcher.matches:
            self.match_freq[matchup] = 0
        for match in glob(f"{self.output_dir}/matches/*"):
            # don't consider empty dirs
            if not os.path.exists(os.path.join(match, "results.json")):
                continue
            model_names = match.split("/")[-1].split("_vs_")
            model_names[1] = model_names[1].split("_")[0]
            model_names = tuple(model_names)
            if model_names in self.match_freq:
                self.match_freq[model_names] += 1


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

    def get_next_min_match(self):
        """Gets the match with the least number of games played"""
        print(self.match_freq)
        return min(self.match_freq.keys(), key=lambda k: self.match_freq[k])

    def run_match(self, lms):
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
            self.logger.info(f"Match {cur_lm_turn} won! GM message: {gm_message}")
        elif gm_message in game_manager.draw_conditions:
            result_a = 0.5
            self.logger.info(f"Match ended in a draw! GM message: {gm_message}")
        else:
            # Loss to current LM because they made the state invalid (exceeded max_tries)
            result_a = 0 if cur_lm_turn == lms[0] else 1
            self.logger.info(f"Match {cur_lm_turn} lost! GM message: {gm_message}")
        
        elos_delta = {}
        if result_a == 1:
            elos_delta[lms[0]] = [0, 1]
            elos_delta[lms[1]] = [0, -1]
        elif result_a == 0:
            elos_delta[lms[0]] = [0, -1]
            elos_delta[lms[1]] = [0, 1]
        else:
            elos_delta[lms[0]] = [0, 0]
            elos_delta[lms[1]] = [0, 0]

        with open(os.path.join(turn_dir, "results.json"), mode='w', newline='') as f:
            obj = {
                lms[0]: {
                    "elos_delta": elos_delta[lms[0]],
                    "result": result_a
                },
                lms[1]: {
                    "elos_delta": elos_delta[lms[1]],
                    "result": 1 - result_a
                }
            }
            json.dump(obj, f)
        
        return lms, result_a

    def start(self):
        self.logger.info("Let the games begin!")

        os.makedirs(os.path.join(self.output_dir, "leaderboard_history"), exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.pool_manager_args.get("max_concurrent_matches", 4)) as executor:
            future_to_match = {}
            for _ in range(self.max_matches):
                lms = self.get_next_min_match()
                future = executor.submit(self.run_match, lms)
                self.match_freq[tuple(lms)] += 1
                future_to_match[future] = lms

            for future in as_completed(future_to_match):
                lms, result_a = future.result()

                if result_a == 1:
                    self.llm_wdl[lms[0]]["wins"] += 1
                    self.llm_wdl[lms[1]]["losses"] += 1
                elif result_a == 0:
                    self.llm_wdl[lms[0]]["losses"] += 1
                    self.llm_wdl[lms[1]]["wins"] += 1
                else:
                    self.llm_wdl[lms[0]]["draws"] += 1
                    self.llm_wdl[lms[1]]["draws"] += 1

        return self.llm_wdl
