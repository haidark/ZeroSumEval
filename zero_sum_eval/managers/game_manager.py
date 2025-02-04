# file: game_manager.py
# TODO: ADD SUPPORT FOR MULTIPLE KINDS OF PLAYERS
from collections import defaultdict
from typing import List, Dict, Optional

from logging import getLogger
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY, LM_REGISTRY
from zero_sum_eval.game_state import GameState, InvalidMoveError
from zero_sum_eval.player import Player

import jsonlines

import os


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
    
    def _process_turn(self, game_state: GameState, player: Player) -> GameState:
        """
        Process a single turn for a player.

        Args:
            game_state (GameState): The current state of the game.
            player (Player): The player whose turn it is.

        Returns:
            GameState: The updated game state after the player's move.

        This method attempts to make a valid move for the player, handling invalid moves
        and win conditions. It returns the original state if all attempts fail.
        """
        logger = getLogger()
        
        while self.player_attempts[player] < self.max_player_attempts:
            move = player.make_move(game_state)
            
            logger.info(f"\t\t--- {player.id} (attempt # {self.player_attempts[player]}) ---")
            logger.info(f"{game_state.display()}Move:\n{move.value}\n\n")
            try:
                game_state.update_game(move)
                # If the game state was updated successfully, break the loop
                break
            except InvalidMoveError as e:
                # If the move was invalid, log the error and increment the player's attempts
                logger.error(f"Invalid move: {e}")
                self.player_attempts[player]+=1
            self.player_attempts[player]+=1
        return game_state


    def _run_game_loop(self, game_state: GameState) -> GameState:
        """
        Run the main game loop.

        Args:
            game_state (GameState): The initial state of the game.

        Returns:
            GameState: The final state of the game after the loop ends.

        This method runs the game for a maximum number of rounds or until a win condition is met.
        It processes turns for each player and logs the game state after each turn.
        """
        logger = getLogger()
        round_count: int = 0
        turns: List[Dict] = []
        prev_player = None
        while round_count < self.max_rounds:
            if game_state.is_over():
                break
            player: Player = game_state.players[game_state.get_next_action()]
            if prev_player != player:
                self.player_attempts[player] = 0
                round_count+=1
            logger.info(f"\t\t--- Start Turn {round_count} ---")
            game_state = self._process_turn(game_state, player)
            turns.append(game_state.export())
            prev_player = player
            if self.player_attempts[player] >= self.max_player_attempts:
                logger.info(f"Player {player.id} has reached the maximum number of attempts. Ending game.")
                break
            
        with jsonlines.open(self.turns_log_file, "w") as f:
            for turn in turns:
                f.write(turn)
        
        return game_state

    def start(self, game: GameState) -> GameState:
        """
        Start the game with the given state.

        Args:
            game (GameState): The initial state of the game.

        Returns:
            GameState: The final state of the game after the game loop ends.
        """

        return self._run_game_loop(game)

