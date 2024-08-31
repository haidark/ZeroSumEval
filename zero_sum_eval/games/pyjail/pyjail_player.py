from zero_sum_eval.player import Player

class PlayerAttacker(Player):
    def __init__(self, id, llm_model, name):
        self.id = id
        self.llm_model = llm_model
        self.name = name

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        pass

    def receive_feedback(self, feedback):
        """
        Abstract method to receive feedback or updates from the game environment.
        
        Parameters:
        feedback (dict): Feedback or update information
        
        Returns:
        None
        """
        pass

class PlayerDefender(Player):
    def __init__(self, id, llm_model, name):
        self.id = id
        self.llm_model = llm_model
        self.name = name

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        pass

    def receive_feedback(self, feedback):
        """
        Abstract method to receive feedback or updates from the game environment.
        
        Parameters:
        feedback (dict): Feedback or update information
        
        Returns:
        None
        """
        pass
