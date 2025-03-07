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
    def __init__(self, max_rounds: int, max_player_attempts: int, output_dir: str, max_time_per_player: float = None):
        """
        Initialize the GameManager with the given configuration.

        Args:
            max_rounds (int): The maximum number of rounds to play in the game.
            max_player_attempts (int): The maximum number of attempts a player can make to generate a valid move.
            output_dir (str): The directory to save game logs and outputs.
            max_time_per_player (float, optional): The maximum time in seconds allocated to each player.
                                                  If None, no time limit is enforced.
        """
        self.max_rounds: int = max_rounds
        self.max_player_attempts: int = max_player_attempts
        self.max_time_per_player: float = max_time_per_player
        self.turns_log_file = os.path.join(output_dir, "turns.jsonl")
        self.player_attempts = defaultdict(int)
        self.player_time_used = defaultdict(float)

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
            
            # Update the player's time usage
            self.player_time_used[player] += move.time
            
            # Check if player has exceeded their time limit
            if self.max_time_per_player is not None and self.player_time_used[player] > self.max_time_per_player:
                logger.info(f"Player {player.id} has exceeded the maximum time limit of {self.max_time_per_player} seconds. Ending game.")
                game_state.set_timeout_loss(player.id)
                break
                
            logger.info(f"Move took {move.time:.2f} seconds. Total time used by {player.id}: {self.player_time_used[player]:.2f} seconds")
            
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
            "player_time_used": self.player_time_used,
        }

    def _log_game_turns(self, turns):
        with jsonlines.open(self.turns_log_file, "w") as f:
            for turn in turns:
                f.write(turn)

