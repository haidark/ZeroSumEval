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
    
    board_visualization = dspy.InputField(desc="visualization of the board")
    board_state = dspy.InputField(desc="FEN formatted current board state")
    role = dspy.InputField(desc="role of the player making the next move")
    history = dspy.InputField(desc="move history")
    move = dspy.OutputField(desc="a valid SAN formatted move without move number or elipses")

class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_move = dspy.ChainOfThought(NextMove)

    def forward(self, board_visualization, board_state, role, history):
        cot_out = self.cot_move(board_visualization=board_visualization,
                                board_state=board_state,
                                role=role,
                                history=history)
        cot_out.move = cot_out.move.replace(".", "")
        try:
            board = chess.Board(board_state)
            move = board.parse_san(cot_out.move)
        except IllegalMoveError:
            dspy.Suggest(
                False,
                f"{cot_out.move} is an illegal move, choose a different move.",
            )
        except InvalidMoveError:
            dspy.Suggest(
                False,
                f"{cot_out.move} is an invalid move, choose a different move."
            )
        except AmbiguousMoveError:
            dspy.Suggest(
                False,
                f"{cot_out.move} is an ambiguous move, choose a different move."
            )
        return cot_out


@PLAYER_REGISTRY.register("chess", "chess_player")
class ChessPlayer(Player):
    def _build_module(self, **module_args):
        return ChessCoT(**module_args)

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        export = game_state.export()
        trace = self.module(board_visualization="BLACK SIDE\n" + str(game_state.board) + "\nWHITE SIDE\n",
                                    board_state=export['environment'],
                                    role=export['roles'][0], 
                                    history=game_state.formatted_move_history()) 
        return trace.move
    