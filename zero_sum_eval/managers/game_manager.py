# file: game_manager.py
# TODO: ADD SUPPORT FOR MULTIPLE KINDS OF PLAYERS
from typing import List

from logging import getLogger
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY, LM_REGISTRY
from zero_sum_eval.game_state import GameState
from collections import defaultdict

import dspy


class GameManager:
    def __init__(self, config):
        self.config = config
        self.games: List[GameState] = []
        self.players = {}
        self.max_rounds = self.config["manager"]["args"]["max_rounds"]
        self.win_conditions = self.config["manager"]["args"]["win_conditions"]
        self._init_game()
        self._init_players()

    def _init_game(self):
        game_config = (
            self.config["game"]["args"] if "args" in self.config["game"] else {}
        )
        game = GAME_REGISTRY.build(self.config["game"]["name"], **game_config)
        self.games.append(game)

    def _init_players(self):
        for player_config in self.config["game"]["players"]:
            player = PLAYER_REGISTRY.build(
                self.config["game"]["name"],
                player_config["name"],
                **player_config["args"],
            )
            if player.role not in self.games[0].roles: 
                raise ValueError(f"Role {player.role} is not defined in {self.games[0].__class__.__name__}")

            self.players[player.role] = player

    def start(self):
        return self.do_eval(self.games[0])

    def do_eval(self, game_state):
        logger = getLogger()
        round_count = 0
        while round_count < self.max_rounds:
            turn_count = round_count // len(self.players) + 1
            game_status = game_state
            if game_status.validate_game():
                break
            game_status = game_state.query_game()
            player = self.players[game_status.roles[0]]
            logger.info(f"{player.id} turn {turn_count}:\n{game_state.display()}")
            game_state = self.do_turn(game_status, player)
            round_count += 1
        return game_state

    def do_turn(self, game_state, player):
        logger = getLogger()
        new_state = game_state
        for _ in range(player.max_tries):
            with dspy.context(lm=player.llm_model):
                move = player.make_move(new_state)
            new_state = new_state.update_game(move)
            val = new_state.validate_game()
            if val is None:
                return new_state
            if val in self.win_conditions:
                #
                # Here maybe call the scoring function?
                #
                return new_state.query_game()
            else:
                logger.warn(f"Player {player.id} made an invalid move: {move}")
                new_state = game_state

        logger.error(
            f"Player {player.id} failed to make a valid move after {player.max_tries} tries."
        )

        return game_state  # Return the original state if all tries fail
