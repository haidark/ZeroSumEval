# I took inspiration from https://github.com/carlini/chess-llm and https://github.com/mlabonne/chessllm
# Shout out to the maintainers and authors of these repositories!

from zero_sum_eval.player import Player
import dspy
import chess
from chess import IllegalMoveError, InvalidMoveError, AmbiguousMoveError
from zero_sum_eval.registry import PLAYER_REGISTRY, METRIC_REGISTRY

# TODO: add support for resigning

@METRIC_REGISTRY.register("chess_move_validation_metric")
def validate_move(example, prediction, trace=None):
    pred_move = prediction.move
    true_move = example.move
    board_state = example.board_state
    board = chess.Board(board_state)
    if true_move is not None and pred_move == true_move:
        return 1
    elif board.is_legal(board.parse_san(pred_move)):
        return 0
    else:
        return -1

class NextMove(dspy.Signature):
    """Given a board state, role, and move history, produce the next best valid move"""
    message = dspy.InputField(desc="Message from the game manager")
    board_state = dspy.InputField(desc="FEN formatted current board state")
    role = dspy.InputField(desc="role of the player making the next move")
    history = dspy.InputField(desc="move history")
    move = dspy.OutputField(desc="a valid SAN formatted move without move number or elipses")

class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_move = dspy.ChainOfThought(NextMove)

    def forward(self, message, board_state, role, history):
        cot_out = self.cot_move(
            message=message,
            board_state=board_state,
            role=role,
            history=history
        )
        cot_out.move = cot_out.move.replace(".", "")
        try:
            board = chess.Board(board_state)
            move = board.parse_san(cot_out.move)
        except (IllegalMoveError, InvalidMoveError, AmbiguousMoveError) as e:
            error_messages = {
                IllegalMoveError: "illegal",
                InvalidMoveError: "invalid",
                AmbiguousMoveError: "ambiguous"
            }
            error_type = type(e)
            dspy.Suggest(
                False,
                f"{cot_out.move} is an {error_messages[error_type]} move, choose a different move."
            )
        return cot_out


@PLAYER_REGISTRY.register("chess", "chess_player")
class ChessPlayer(Player):
    def _build_modules(self, **module_args):
        self.main_module = ChessCoT(**module_args)
        return [self.main_module]

    def _make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        trace = self.main_module(**game_state.player_inputs()) 
        return trace.move
    