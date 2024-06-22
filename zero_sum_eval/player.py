from abc import ABC, abstractmethod

# Abstract class for players
class Player(ABC):
    def __init__(self, id, role):
        self.id = id
        self.role = role
        self.context = {}

    @abstractmethod
    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        pass

class HumanPlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")
        return move.strip()
