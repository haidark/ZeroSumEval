from zero_sum_eval.player import Player
import dspy

class NextMove(dspy.Signature):
    """Given a board state, produce a the next move"""

    board_state = dspy.InputField(desc="pgn formatted chess board state")
    next_board_state = dspy.OutputField(desc="pgn formatted chess board state after one move")


class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(NextMove)
        self.predict = dspy.Predict(NextMove)

    def forward(self, board_state):
        next_board_state = self.cot(board_state=board_state)
        # next_board_state = self.predict(board_state=board_state)
        # dspy.Assert(
        #     valid_json(solution_json.solution_json),
        #     "Final output should be parseable json.",
        # )
        return next_board_state

class ChessPlayer(Player):
    def __init__(self, llm_model, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        self.llm_model = llm_model
        self.max_tries = max_tries
        self.module = ChessCoT()
        # dspy.settings.configure(lm=llm_model)
        # dspy.configure(trace=[])

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        with dspy.context(lm=self.llm_model):
            trace = self.module(board_state=game_state)
        # print(self.llm_model.inspect_history(n=2))
        print(self.id, trace)
        return trace.next_board_state