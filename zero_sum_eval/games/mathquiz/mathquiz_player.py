# I took inspiration from https://github.com/carlini/chess-llm and https://github.com/mlabonne/chessllm
# Shout out to the maintainers and authors of these repositories!

from zero_sum_eval.player import Player
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import LabeledFewShot, BootstrapFewShot, MIPROv2, BootstrapFewShotWithRandomSearch
import functools, json
from random import shuffle
from zero_sum_eval.registry import PLAYER_REGISTRY, LM_REGISTRY

class GenerateQuestion(dspy.Signature):
    """Given a target number, generate a challenging math question with the target number as the answer. Make sure not to include the answer in the question."""
    
    target_number = dspy.InputField(desc="target number")
    math_question = dspy.OutputField(desc="math question with the target number as the answer")

class AnswerQuestion(dspy.Signature):
    """Given a math question, give the answer to the question as a number only"""
    
    math_question = dspy.InputField(desc="math question")
    answer = dspy.OutputField(desc="answer to the math question with number only")

class GenerateQuestionCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_question = dspy.ChainOfThought(GenerateQuestion)


    def forward(self, target_number):
        cot_out = self.cot_question(target_number=target_number)
        return cot_out

class AnswerQuestionCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_answer = dspy.ChainOfThought(AnswerQuestion)

    def forward(self, math_question):
        cot_out = self.cot_answer(math_question=math_question)
        return cot_out

@PLAYER_REGISTRY.register("mathquiz", "mathquiz_teacher")
class MathQuizTeacher(Player):
    def _build_module(self, **module_args):
        self.question_module = GenerateQuestionCoT()
        self.answer_module = AnswerQuestionCoT()
        return [self.question_module, self.answer_module]

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        export = game_state.export()
        current_role = game_state.roles[0]
        with dspy.context(lm=self.llm_model):
            if current_role == "TeacherGenerateQuestion":
                trace = self.question_module(export['environment'])
                return trace.math_question
            elif current_role == "TeacherAnswerQuestion":
                trace = self.answer_module(export['environment'])
                return trace.answer
            else:
                raise ValueError(f"Invalid role for teacher: {current_role}")


@PLAYER_REGISTRY.register("mathquiz", "mathquiz_student")
class MathQuizStudent(Player):
    def _build_module(self, **module_args):
        self.answer_module = AnswerQuestionCoT()
        return [self.answer_module]

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """
        export = game_state.export()
        current_role = game_state.roles[0]
        with dspy.context(lm=self.llm_model):
            if current_role == "StudentAnswerQuestion":
                trace = self.answer_module(export['environment'])
                return trace.answer
            else:
                raise ValueError(f"Invalid role for student: {current_role}")

        
    
