'''
Abstract class to define minimum API to represent a game
'''
import yaml
from abc import ABC, abstractmethod
from typing import Dict, List, Self, Optional 

class GameState(ABC):
    def __init__(self, **kwargs) -> Self:
       environment = None         
       context = None          
       roles = None
       self.instantiate(environment, context, roles, **kwargs)

    @abstractmethod
    def instantiate(self, environment: Dict, context: Dict, roles: List[str], **kwargs) -> None:
        """
        Initialize the game state with the given environment, context, and roles.

        Args:
            environment (Dict): A representation of the game state.
            context (Dict): A dictionary with required key "message" and other additional keys.
            roles (List[str]): A queue of players.
        """
        raise NotImplementedError
        
    @abstractmethod
    def update_game(self, move: str) -> Self:
        """
        Update the game state based on the given move.

        Args:
            move (str): The move to be applied to the game state.

        Returns:
            GameState: A new GameState object representing the updated game state.

        Raises:
            ValueError if the GameState cannot be updated

        This method advances the game given a move compatible with the current environment.
        If the move is invalid, the game state remains the same and the context is updated.
        """
        raise NotImplementedError

    @abstractmethod
    def query_game(self) -> Self:
        """
        Get the game state relevant to the next role to move.

        Returns:
            GameState: A GameState object containing all information needed by the role-to-move.

        This method returns a game state with all information relevant to the game's next role-to-move.
        Any context["message"] in self will be relevant to the role.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_game(self) -> str | None:
        """
        Check if the game should continue or end based on the current state.

        Returns:
            str | None: A string describing the reason if the game should end, or None if it should continue.

        This method forwards non-continue conditions from the last move or returns new non-continue conditions
        in the environment, specific to the game implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_next_roles(self) -> List[str]:
        """
        Determine the list of roles given the current state of the game.

        Returns:
            List[str]: A valid ordered list of roles.
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
        Provide a complete representation of the current game state in a compatible game config format.

        Returns:
            str: A YAML-formatted string representation of the game state.
        """
        return yaml.dump(self.__dict__)
    
    




