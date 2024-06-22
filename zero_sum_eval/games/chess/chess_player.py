from zero_sum_eval.player import Player
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import copy
import functools

class NextMove(dspy.Signature):
    """Given a board state, produce the next move"""

    board_state = dspy.InputField(desc="move history and FEN formatted current chess board state")
    move = dspy.OutputField(desc="a valid move")


class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(NextMove)

    def forward(self, board_state):
        cot_out = self.cot(board_state=board_state.export())
        new_state = copy.deepcopy(board_state).update_game(cot_out.move)
        val = new_state.validate_game()
        dspy.Assert(
            not (val is not None and "error" in val),
            f"{val}, choose another move that is valid.",
            target_module=self.cot
        )
        return cot_out

class ChessPlayer(Player):
    def __init__(self, llm_model, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        self.llm_model = llm_model
        self.max_tries = max_tries
        self.module = assert_transform_module(ChessCoT(), functools.partial(backtrack_handler, max_backtracks=10))
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
        # print(self.id, self.llm_model.inspect_history(n=10))
        return trace.move