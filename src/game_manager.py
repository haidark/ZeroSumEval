from abc import ABC, abstractmethod

# abstract class for game environments
class GameManager(ABC):
    def __init__(self, players, max_turns, win_conditions):
        self.players = players
        self.max_turns = max_turns
        self.current_turn = 0
        self.win_conditions = win_conditions
        self.game_state = self.initialize_game()

    @abstractmethod
    def initialize_game(self):
        """
        Abstract method for initializing the game with initial conditions.
        
        Returns:
        dict: The initial state of the game
        """
        pass

    @abstractmethod
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

    @abstractmethod
    def check_win_conditions(self):
        """
        Abstract method to check if the win conditions are met.
        
        Returns:
        bool: True if the win conditions are met, otherwise False
        """
        pass

    def run_game(self):
        """
        Method to manage the overall flow of the game.
        
        Returns:
        dict: The final state of the game
        """
        while self.current_turn < self.max_turns:
            for player in self.players:
                move = player.make_move(self.game_state)
                self.update_game_state(player, move)
                if self.check_win_conditions():
                    return self.end_game(player)
                self.current_turn += 1
        return self.end_game(None)

    def end_game(self, winning_player):
        """
        Method to end the game and declare the winner.
        
        Parameters:
        winning_player (Player or None): The winning player, or None if there is no winner
        
        Returns:
        dict: The final state of the game and the winner
        """
        return {
            "game_state": self.game_state,
            "winner": winning_player.name if winning_player else "No winner"
        }