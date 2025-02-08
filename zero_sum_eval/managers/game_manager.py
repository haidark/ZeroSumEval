"""Game manager module for handling game execution and state management."""

import os
import dspy
from collections import defaultdict
from logging import getLogger
from typing import Dict, List

import jsonlines

from zero_sum_eval.game_state import GameState, InvalidMoveError
from zero_sum_eval.player import Player, Move

class GameManager:
    def __init__(self, config: Dict):
        """
        Initialize the GameManager with the given configuration.

        Args:
            config (Dict): Configuration dictionary containing game and player settings.
        """
        self.config: Dict = config
        self.max_rounds: int = self.config["manager"]["args"]["max_rounds"]
        self.max_player_attempts: int = self.config["manager"]["args"]["max_player_attempts"]
        self.turns_log_file = os.path.join(self.config["logging"]["output_dir"], "turns.jsonl")
        self.player_attempts = defaultdict(int)

    def start(self, game_state: GameState) -> GameState:
        """
        Start the game with the given state.

        Args:
            game_state (GameState): The initial state of the game.

        Returns:
            GameState: The final state of the game after the game loop ends.
        """
        logger = getLogger()
        turns: List[Dict] = []
        round_count = 0
        prev_player = None # to detect when the player to act has changed (end of round and attempts reset)
        while round_count <= self.max_rounds:
            if game_state.is_over():
                break
            action = game_state.get_next_action()
            inputs = game_state.player_inputs()
            player: Player = action.player
            if prev_player != player:
                self.player_attempts[player] = 0
                prev_player = player
                round_count +=1
            logger.info(f"\t\t--- Start Turn {round_count} ---")
            logger.info(f"\t\t--- {player.id} (attempt # {self.player_attempts[player]}) ---")
            logger.info(f"Game State:\n{game_state.display()}\n")
            with dspy.context(lm=action.player.llm_model):
                trace = player.module_dict[action.name](**inputs)
            # the final value in the prediction is assumed to be the output of the module
            output = trace.items()[-1][1]

            move = Move(value=output, trace=trace)
            try:
                game_state.update_game(move)
                logger.info(f"\nPlayer {player.id} made move:\n{move.value}\n\n")
            except InvalidMoveError as e:
                # If the move was invalid, log the error and increment the player's attempts
                logger.error(f"Invalid move: {e}")
                if self.player_attempts[player] >= self.max_player_attempts:
                    logger.info(f"Player {player.id} has reached the maximum number of attempts. Ending game.")
                    break
                self.player_attempts[player] += 1
                continue
            prev_player = player
            turns.append(game_state.export())
            
        self._log_game_turns(turns)
        
        return game_state

    def _log_game_turns(self, turns):
        with jsonlines.open(self.turns_log_file, "w") as f:
            for turn in turns:
                f.write(turn)

