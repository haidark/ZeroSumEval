# file: game_manager.py
# TODO: ADD SUPPORT FOR MULTIPLE KINDS OF PLAYERS
from typing import List, Dict, Optional

from logging import getLogger
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY, LM_REGISTRY
from zero_sum_eval.game_state import GameState
from zero_sum_eval.player import Player
from collections import defaultdict



class GameManager:
    def __init__(self, config: Dict):
        """
        Initialize the GameManager with the given configuration.

        Args:
            config (Dict): Configuration dictionary containing game and player settings.
        """
        self.config: Dict = config
        self.games: List[GameState] = []
        self.players: Dict[str, Player] = {}
        self.max_rounds: int = self.config["manager"]["args"]["max_rounds"]
        self.win_conditions: List[str] = self.config["manager"]["args"]["win_conditions"]
        self._init_game()
        self._init_players()

    def _init_game(self) -> None:
        """
        Initialize the game based on the configuration.

        Creates a game instance using the GAME_REGISTRY and appends it to the games list.
        """
        game_config: Dict = (
            self.config["game"]["args"] if "args" in self.config["game"] else {}
        )
        game: GameState = GAME_REGISTRY.build(self.config["game"]["name"], **game_config)
        self.games.append(game)

    def _init_players(self) -> None:
        """
        Initialize players based on the configuration.

        Creates player instances using the PLAYER_REGISTRY and adds them to the players dictionary.
        Raises a ValueError if a player's role is not defined in the game.
        """
        for player_config in self.config["game"]["players"]:
            player: Player = PLAYER_REGISTRY.build(
                self.config["game"]["name"],
                player_config["name"],
                **player_config["args"],
            )
            if player.roles[0] not in self.games[0].roles: 
                raise ValueError(f"Role {player.role} is not defined in {self.games[0].__class__.__name__}")
            for role in player.roles:
                self.players[role] = player

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
        
        player_attempts = 0
        for _ in range(player.max_tries):
            new_state: GameState = game_state.query_game()
            move: str = player.make_move(new_state)
            player_attempts+=1
            game_state: GameState = game_state.update_game(move)
            val: Optional[str] = game_state.validate_game()
            if val is None:
                return game_state, player_attempts
            if val in self.win_conditions:
                #
                # Here maybe call the scoring function?
                #
                return game_state, player_attempts
        return game_state, player_attempts  # Return the original state if all tries fail

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
        attempts: int = 0
        while round_count < self.max_rounds:
            turn_count: int = round_count // len(self.players) + 1
            player: Player = self.players[game_state.roles[0]]
            logger.info(f"{player.id} (attempts {attempts}) turn {turn_count}:\n{game_state.display()}")
            if game_state.validate_game():
                break
            game_state, attempts = self._process_turn(game_state, player)
            round_count += 1
        return game_state

    def start(self) -> GameState:
        """
        Start the game.

        Returns:
            GameState: The final state of the game after it has ended.

        This method initiates the game by calling the _run_game_loop method with the initial game state.
        """
        return self._run_game_loop(self.games[0])

