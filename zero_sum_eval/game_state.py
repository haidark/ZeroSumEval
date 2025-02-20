'''
Abstract class API to represent a game
'''
import logging

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Dict, List

from zero_sum_eval.type_definitions import ActionConfig
from zero_sum_eval.player import Move, Player, PlayerDefinition

class InvalidMoveError(Exception):
    pass


@dataclass
class Action:
    name: str
    player: Player


class GameState(ABC):
    def __init__(self, players: Dict, log_moves: bool = True):
        self._init_players(players)
        self.log_moves = log_moves

    def _init_players(self, players_config: Dict):
        """
        Initialize players based on the configuration.
        
        Creates player instances using the PLAYER_REGISTRY and adds them to the players dictionary.

        Args:
            players_config (Dict): Configuration dictionary containing player settings.
        """
        from zero_sum_eval.registry import PLAYER_REGISTRY
        self.players = {}
        loaded_player_keys = []
        for player_key, config in players_config.items():
            # get the player definition for the specified player key
            definition = [desc for desc in self.player_definitions() if desc.player_key == player_key][0]
            
            # fill in the non-specified actions with the default actions
            config["args"]["actions"] = config["args"].get("actions", [])
            names = [action.name if isinstance(action, ActionConfig) else action["name"] for action in config["args"].get("actions", [])]
            for action in definition.actions:
                if action not in names:
                    config["args"]["actions"].append(ActionConfig(name=action))

            # create the player instance for the player key
            # if a class is specified in the config, use it, otherwise use the default player class
            if "class" in config:
                player = PLAYER_REGISTRY.build(game_name=self.__class__.__name__, player_name=config["class"], player_key=player_key, **config["args"])
            else:
                player = PLAYER_REGISTRY.build(game_name=self.__class__.__name__, player_name=definition.default_player_class.__name__, player_key=player_key, **config["args"])

            if set(player.module_dict.keys()) != set(definition.actions):
                raise ValueError(f"Player {player_key} does not support all actions {definition.actions}. Missing actions: {set(definition.actions) - set(player.module_dict.keys())}")

            self.players[player_key] = player

            loaded_player_keys.append(player_key)           

        for definition in self.player_definitions():
            if definition.player_key in loaded_player_keys or definition.optional:
                continue

            logging.warning(f"Player for player key {definition.player_key} not specified. Using default player with GPT-4o.")
            player = definition.default_player_class(id=f"GPT-4o_{definition.player_key}", player_key=definition.player_key, actions=definition.actions, lm={"model": "openai/gpt-4o"}, max_tries=5)
            self.players[definition.player_key] = player

    @abstractmethod
    def get_scores(self) -> Dict[str, float]:
        """
        Get the current scores of the players in the game.

        Returns:
            Dict[str, float]: A dictionary of player scores.
        """
        raise NotImplementedError
        

    @abstractmethod
    def update_game(self, move: Move):
        """
        Update the game state based on the given move.

        Args:
            move (str): The move to be applied to the game state.

        Raises:
            InvalidMoveError: If the move is not compatible with the current game state.

        This method advances the game given a move compatible with the current environment.
        """
        raise NotImplementedError

    @abstractmethod
    def is_over(self) -> bool:
        """
        Check if the game is in a terminal state.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        return NotImplementedError
    
    @abstractmethod
    def get_next_action(self) -> Action:
        """
        Get the next action to be taken in the game.

        Returns:
            Action: The next action to be taken.
        """
        raise NotImplementedError
    
    @abstractmethod
    def player_inputs(self) -> Dict[str, str]:
        """
        Provides a representation of the game state according to the current player_key

        Returns:
            dict
        """
        raise NotImplementedError

    def export(self) -> Dict:
        """
        Export the game state to a dictionary.

        Returns:
            dict: A dictionary representation of the game state.
        """
        new_dict = copy(self.__dict__)
        new_dict.pop("players")
        return self.__dict__
    
    @classmethod
    @abstractmethod
    def player_definitions(cls) -> List[PlayerDefinition]:
        """
        Get the definitions of all players in the game.

        Returns:
            List[PlayerDefinition]: A list of player definitions.
        """
        raise NotImplementedError

    def __init_subclass__(cls):
        """
        Wrapper to log moves and traces in the game state when the game is updated
        """
        super().__init_subclass__()
        
        def move_logging_wrapper(fn):
            def wrapped(self, move: Move):
                try:
                    new_state = fn(self, move)
                    if not self.log_moves:
                        return new_state
                    self._log = {"last_move": move.value, "last_trace": move.trace.toDict()}
                    return new_state
                except InvalidMoveError as e:
                    if not hasattr(self, '_log'):
                        self._log = {}
                    self._log.update({"last_move": move.value, "last_trace": move.trace.toDict(), "error": str(e)})
                    raise
            return wrapped
        
        cls.update_game = move_logging_wrapper(cls.update_game)

        def export_logging_wrapper(fn):
            def wrapped(self):
                new_dict = fn(self)
                if not self.log_moves:
                    return new_dict
                new_dict.update(self._log)
                return new_dict
            return wrapped
        
        cls.export = export_logging_wrapper(cls.export)
