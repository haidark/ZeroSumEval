# I took inspiration from https://github.com/carlini/chess-llm and https://github.com/mlabonne/chessllm
# Shout out to the maintainers and authors of these repositories!
import chess
from zero_sum_eval.game_manager import GameManager

# TODO: add support for checking that only one move is made by a player at a time
# TODO: add support for checking valid moves
# TODO: add support for checking win/lose/draw

class ChessManager(GameManager):
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
        initial_board_state = \
f"""[Event "ZeroSumEval Chess Game"]
[Site "Online"]
[Date "2024.06.12"]
[Round "1"]
[White "{self.players[0].id}"]
[Black "{self.players[1].id}"]
[Result "*"]

1."""
        return dict(
            board_state=initial_board_state,
        )

    def update_game_state(self, player, move):
        """
        Abstract method for updating the game state based on a player's move.
        
        Parameters:
        player (Player): The player making the move
        move (dict): The move made by the player
        
        Returns:
        None
        """
        self.game_state['board_state'] = move['next_board_state']

    def check_win_conditions(self):
        """
        Abstract method to check if the win conditions are met.
        
        Returns:
        bool: True if the win conditions are met, otherwise False
        """
        return False