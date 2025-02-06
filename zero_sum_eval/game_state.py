'''
Abstract class to define minimum API to represent a game
'''
import logging

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Dict, List, Type

import dspy

from zero_sum_eval.types import ActionConfig
from zero_sum_eval.player import Move, Player

class InvalidMoveError(Exception):
    pass

@dataclass
class Action:
    name: str
    player: Player

@dataclass
class PlayerDescription:
    name: str
    actions: List[str]
    default_player_class: Type[Player]


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
        loaded_roles = []
        for role, config in players_config.items():
            # get the player description for the specified role
            description = [desc for desc in self.player_descriptions() if desc.name == role][0]
            
            # fill in the non-specified actions with the default actions
            config["args"]["actions"] = config["args"].get("actions", [])
            names = [action["name"] for action in config["args"].get("actions", [])]
            for action in description.actions:
                if action not in names:
                    config["args"]["actions"].append(ActionConfig(name=action))

            # create the player instance for the role
            # if a class is specified in the config, use it, otherwise use the default player class
            if "class" in config:
                player = PLAYER_REGISTRY.build(game_name=self.__class__.__name__, player_name=config["class"], role=role, **config["args"])
            else:
                player = PLAYER_REGISTRY.build(game_name=self.__class__.__name__, player_name=description.default_player_class.__name__, role=role, **config["args"])


            if set(player.module_dict.keys()) != set(description.actions):
                raise ValueError(f"Player {role} does not support all actions {description.actions}. Missing actions: {set(description.actions) - set(player.module_dict.keys())}")

            self.players[role] = player

            loaded_roles.append(role)           

        for role in self.player_descriptions():
            if role.name in loaded_roles:
                continue

            logging.warning(f"Player for role {role.name} not specified. Using default player with GPT-4o.")
            player = role.default_player_class(id=f"GPT-4o_{role.name}", role=role.name, actions=role.actions, lm={"model": "openai/gpt-4o"}, max_tries=5)
            self.players[role.name] = player

    @abstractmethod
    def get_scores(self):
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
            trace (dspy.Prediction, optional): The trace of the move made by the player, to save in the state.

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
        Provides a representation of the game state according to the current role

        Returns:
            dict
        """
        raise NotImplementedError

    def export(self):
        """
        Export the game state to a dictionary.

        Returns:
            dict: A dictionary representation of the game state.
        """
        new_dict = copy(self.__dict__)
        new_dict.pop("players")
        return self.__dict__
    
    @abstractmethod
    def player_descriptions(self) -> List[PlayerDescription]:
        """
        Get the descriptions of the players in the game.

        Returns:
            List[PlayerDescription]: A list of player descriptions.
        """
        raise NotImplementedError

    def step(self) -> Move:
        """
        Perform a single step in the game. Updates the game state and returns the move made by the player.

        Returns:
            Move: The move made by the player.

        Raises:
            InvalidMoveError: If the move is not compatible with the current game state.
        """
        if self.is_over():
            raise InvalidMoveError("Game is already over")

        inputs = self.player_inputs()
        action: Action = self.get_next_action()
        
        with dspy.context(lm=action.player.llm_model):
            trace = action.player.module_dict[action.name](**inputs)

        # the final value in the prediction is assumed to be the output of the module
        output = trace.items()[-1][1]

        move = Move(value=output, trace=trace)

        self.update_game(move)

        return move


    def __init_subclass__(cls):
        """
        Wrapper to log moves and traces in the game state when the game is updated
        """
        super().__init_subclass__()
        
        def move_logging_wrapper(fn):
            def wrapped(self, move: Move):
                new_state = fn(self, move)
                if not self.log_moves:
                    return new_state
                self._log = {"last_move": move.value, "last_trace": move.trace.toDict()}

                return new_state
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
