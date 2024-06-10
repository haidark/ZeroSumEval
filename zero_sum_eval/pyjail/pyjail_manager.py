from zero_sum_eval.game_manager import GameManager

class PyjailManager(GameManager):
    def __init__(self, players, max_turns, win_conditions):
        self.players = players
        self.max_turns = max_turns
        self.current_turn = 0
        self.win_conditions = win_conditions
        self.game_state = self.initialize_game()

    def initialize_game(self):
        """
        Abstract method for initializing the game with initial conditions.
        
        Returns:
        dict: The initial state of the game
        """
        pass

    def update_game_state(self, player, move):
        """
        Abstract method for updating the game state based on a player's move.
        
        Parameters:
        player (Player): The player making the move
        move (dict): The move made by the player
        
        Returns:
        None
        """
        pass

    def check_win_conditions(self):
        """
        Abstract method to check if the win conditions are met.
        
        Returns:
        bool: True if the win conditions are met, otherwise False
        """
        pass