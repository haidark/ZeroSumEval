from zero_sum_eval.player import Player
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import copy
from chess import IllegalMoveError, InvalidMoveError, AmbiguousMoveError
import functools


class NextMove(dspy.Signature):
    """Given a board state, analysis, and move history, produce the next best valid move"""
    
    board_state = dspy.InputField(desc="FEN formatted current board state")
    history = dspy.InputField(desc="move history")
    move = dspy.OutputField(desc="a valid SAN formatted move without move number or elipses")


class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_move = dspy.ChainOfThought(NextMove)

    def format_move_history(self, history):
        formatted_history = ""
        moves = len(history)//2+1
        for i in range(1, moves+1):
            j = (i-1)*2
            formatted_history+=f"{i}. "
            if j < len(history):
                formatted_history+=f"{history[j]} "
            if j+1 < len(history):
                formatted_history+=f"{history[j+1]} "
        return formatted_history.strip()


    def forward(self, board_state):
        export = board_state.export()
        cot_out = self.cot_move(board_state=export['environment'],
                           history=self.format_move_history(export['context']['history']))
        cot_out.move = cot_out.move.replace(".", "")
        try:
            move = board_state.board.parse_san(cot_out.move)
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

class ChessPlayer(Player):
    def __init__(self, llm_model, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        self.llm_model = llm_model
        self.max_tries = max_tries
        self.module = assert_transform_module(ChessCoT(), functools.partial(backtrack_handler, max_backtracks=max_tries))
        dspy.configure(trace=[])

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        with dspy.context(lm=self.llm_model):
            trace = self.module(board_state=game_state)
        print(self.id, game_state.export(), trace)
        # print(self.id, self.llm_model.inspect_history(n=5))
        return trace.move