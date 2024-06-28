# I took inspiration from https://github.com/carlini/chess-llm and https://github.com/mlabonne/chessllm
# Shout out to the maintainers and authors of these repositories!

from zero_sum_eval.player import Player
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
import copy
import chess
from chess import IllegalMoveError, InvalidMoveError, AmbiguousMoveError
import functools, json

# TODO: add support for resigning
# TODO: add support for checking win/lose/draw

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
            formatted_history+=f"{i}."
            if j < len(history):
                formatted_history+=f"{history[j]} "
            if j+1 < len(history):
                formatted_history+=f"{history[j+1]} "
        return formatted_history.strip()


    def forward(self, board_state, history):
        cot_out = self.cot_move(board_state=board_state,
                           history=self.format_move_history(history))
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

class ChessPlayer(Player):
    def __init__(self, llm_model, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        self.llm_model = llm_model
        self.max_tries = max_tries
        self.module = assert_transform_module(ChessCoT(), functools.partial(backtrack_handler, max_backtracks=max_tries))
        self.optimized_module = self.optimize_prompts() if self.optimize else None
        dspy.configure(trace=[])

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        export = game_state.export()
        with dspy.context(lm=self.llm_model):
            if self.optimize:
                trace = self.optimized_module(board_state=export['environment'], 
                                              history=export['context']['history'])
            else:
                trace = self.module(board_state=export['environment'], 
                                    history=export['context']['history'])
        print(self.id, export, trace)
        # print(self.id, self.llm_model.inspect_history(n=5))
        return trace.move
    
    def optimize_prompts(self):
        filename = 'data/chess/stockfish_examples.jsonl'
        dataset = self.create_dataset(filename)
        config = dict(max_bootstrapped_demos=4, max_labeled_demos=4, num_candidate_programs=10, num_threads=4)
        teleprompter = BootstrapFewShotWithRandomSearch(metric=validate_move, **config)
        with dspy.context(lm=self.llm_model):
            return teleprompter.compile(self.module, trainset=dataset)

    def load_examples(self, filename):
        examples = []
        with open(filename, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        return examples

    def create_dataset(self, filename):
        examples = self.load_examples(filename)
        dataset = []
        for example in examples[-10:]:
            if self.role =="White": # white to move
                if not example['turn']:
                    continue
            else:                   # black to move
                if example['turn']:
                    continue
            example = dspy.Example(board_state=example['board_state'], 
                                history=example['history'],
                                move=example['move']
                                ).with_inputs("board_state", "history")
            dataset.append(example)
        return dataset
    

        
    
