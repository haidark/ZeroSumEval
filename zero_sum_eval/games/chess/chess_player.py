# I took inspiration from https://github.com/carlini/chess-llm and https://github.com/mlabonne/chessllm
# Shout out to the maintainers and authors of these repositories!

from zero_sum_eval.player import Player
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import LabeledFewShot, BootstrapFewShot, MIPROv2, BootstrapFewShotWithRandomSearch
import copy
import chess
from chess import IllegalMoveError, InvalidMoveError, AmbiguousMoveError
import functools, json
from random import shuffle
from zero_sum_eval.registry import PLAYER_REGISTRY, LM_REGISTRY

# TODO: add support for resigning

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
    
    board_state = dspy.InputField(desc="FEN formatted current board state")
    role = dspy.InputField(desc="role of the player making the next move")
    history = dspy.InputField(desc="move history")
    move = dspy.OutputField(desc="a valid SAN formatted move without move number or elipses")


class ChessCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_move = dspy.ChainOfThought(NextMove)


    def forward(self, board_state, role, history):
        cot_out = self.cot_move(board_state=board_state,
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
    def __init__(self, lm, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        lm_args = lm["args"] if "args" in lm else {}
        self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
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
                                              role=export['roles'][0], 
                                              history=game_state.formatted_move_history())
            else:
                trace = self.module(board_state=export['environment'],
                                    role=export['roles'][0], 
                                    history=game_state.formatted_move_history())
        return trace.move
    
    def optimize_prompts(self):
        filename = 'data/chess/stockfish_examples.jsonl'
        dataset = self.create_dataset(filename)
        shuffle(dataset)
        # config = dict(max_bootstrapped_demos=4, max_labeled_demos=16)
        # teleprompter = BootstrapFewShot(metric=validate_move, **config)
        with dspy.context(lm=self.llm_model):
            
            teleprompter = MIPROv2(metric=validate_move, prompt_model=self.llm_model, task_model=self.llm_model,
                                   num_candidates=5, minibatch_size=20, minibatch_full_eval_steps=10, 
                                   verbose=True)
            return teleprompter.compile(self.module, max_bootstrapped_demos=1, max_labeled_demos=1, 
                                        trainset=dataset, eval_kwargs={})

    def load_examples(self, filename):
        examples = []
        with open(filename, 'r') as f:
            for line in f:
                examples.append(json.loads(line))
        return examples

    def create_dataset(self, filename):
        examples = self.load_examples(filename)
        dataset = []
        for example in [examples[i] for i in range(0, len(examples), len(examples)//10)]:
            if self.role =="White": # white to move
                if not example['turn']:
                    continue
            else:                   # black to move
                if example['turn']:
                    continue
            example = dspy.Example(board_state=example['board_state'],
                                   role=f"{self.role}",
                                   history=example['history'],
                                   move=example['move']
                                   ).with_inputs("board_state", "role", "history")
            dataset.append(example)
        return dataset
