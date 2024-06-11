from abc import ABC, abstractmethod

# Abstract class for players
class Player(ABC):
    def __init__(self, id, llm_model, name):
        self.id = id
        self.llm_model = llm_model
        self.name = name

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

    # @abstractmethod
    # def receive_feedback(self, feedback):
    #     """
    #     Abstract method to receive feedback or updates from the game environment.
        
    #     Parameters:
    #     feedback (dict): Feedback or update information
        
    #     Returns:
    #     None
    #     """
    #     pass