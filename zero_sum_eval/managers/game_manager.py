"""Game manager module for handling game execution and state management."""

import os
import dspy
from collections import defaultdict
from logging import getLogger
from typing import Dict, List

import jsonlines

from zero_sum_eval.core.game_state import GameState, InvalidMoveError
from zero_sum_eval.core.player import Player, Move

class GameManager:
    def __init__(self, max_rounds: int, max_player_attempts: int, output_dir: str):
        """
        Initialize the GameManager with the given configuration.

        Args:
            max_rounds (int): The maximum number of rounds to play in the game.
            max_player_attempts (int): The maximum number of attempts a player can make to generate a valid move.
            output_dir (str): The directory to save game logs and outputs.
        """
        self.max_rounds: int = max_rounds
        self.max_player_attempts: int = max_player_attempts
        self.turns_log_file = os.path.join(output_dir, "turns.jsonl")
        self.player_attempts = defaultdict(int)

    def start(self, game_state: GameState) -> Dict:
        """
        Start the game with the given state.

        Args:
            game_state (GameState): The initial state of the game.

        Returns:
            Dict: A dictionary containing the final game state, the list of turns, and the player attempts.
        """
        logger = getLogger()
        turns: List[Dict] = []
        round_count = 0
        retrying = False
        while round_count <= self.max_rounds:
            if game_state.is_over():
                break
            action = game_state.get_next_action()
            player: Player = game_state.players[action.player_key]
            if not retrying:
                round_count +=1
            logger.info(f"\t\t--- Start Turn {round_count} ---")
            logger.info(f"\t\t--- {player.id} (attempt # {self.player_attempts[player]}) ---")
            logger.info(f"Game State:\n{game_state.display()}\n")

            move = player.act(action)
            try:
                game_state.update_game(move)
                retrying = False
                logger.info(f"\nPlayer {player.id} made move:\n{move.value}\n\n")
            except InvalidMoveError as e:
                # If the move was invalid, log the error and increment the player's attempts
                logger.error(f"Invalid move: {e}")
                self.player_attempts[player] += 1
                retrying = True
                if self.player_attempts[player] >= self.max_player_attempts:
                    logger.info(f"Player {player.id} has reached the maximum number of attempts. Ending game.")
                    break
            turns.append(game_state.export())
            
        self._log_game_turns(turns)
        
        return {
            "game_state": game_state,
            "turns": turns,
            "player_attempts": self.player_attempts,
        }

    def _log_game_turns(self, turns):
        with jsonlines.open(self.turns_log_file, "w") as f:
            for turn in turns:
                f.write(turn)

