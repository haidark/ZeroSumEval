from random import randint
from zero_sum_eval.games.mathquiz.mathquiz_player import MathQuizStudent, MathQuizTeacher, STUDENT_KEY, TEACHER_KEY
from zero_sum_eval.core.game_state import Action, GameState, InvalidMoveError, PlayerDefinition
from zero_sum_eval.core.registry import GAME_REGISTRY
from zero_sum_eval.core.player import Move
from typing import List

from logging import getLogger

logger = getLogger()

@GAME_REGISTRY.register("mathquiz")
class MathQuizGame(GameState):
    """
    This is a two player game where the players take turns to answer math questions.
    In each round:
        1. the environment is initialized with a target number
        2. The first player to move creates a math question with the answer as the target number
        and proves that the question is valid.
        3. If the first player succeeds, the second player is given a chance to answer the question.
        4. The game continues for a fixed number of rounds.

    The actions for this game are:
        GenerateQuestion
        AnswerQuestion

    The environment for this game is:
        question: a math question
        teacher_answer: the teacher's answer to the math question
        student_answer: the student's answer to the math question
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.question = None
        self.teacher_answer = None
        self.student_answer = None
        self.scores = {TEACHER_KEY: 0, STUDENT_KEY: 0}
        self.target = kwargs.get('target', str(randint(1, 1000)))
        self.message = f"{TEACHER_KEY} to generate a question"

    def update_game(self, move: Move):
        next_action = self.get_next_action()
        move = move.value
        if next_action.name == "GenerateQuestion":
            self.question = move
            self.message = f"{TEACHER_KEY} to answer the question"
        elif next_action.name == "AnswerQuestion" and next_action.player_key == TEACHER_KEY:
            if not self.verify_answer(move):
                # If the teacher's answer is incorrect, generate a new target number and raise an error to be caught by the game manager
                self.target = str(randint(1, 1000))
                self.question = None
                self.scores = {TEACHER_KEY: 0, STUDENT_KEY: 1}
                self.message = f"{TEACHER_KEY} did not answer the question correctly"
                raise InvalidMoveError("TeacherIncorrect")
            self.message = f"{STUDENT_KEY} to answer the question"
            self.teacher_answer = move
        elif next_action.name == "AnswerQuestion" and next_action.player_key == STUDENT_KEY:
            if not self.verify_answer(move):
                # If the student's answer is incorrect, raise an error to be caught by the game manager
                self.scores = {TEACHER_KEY: 1, STUDENT_KEY: 0}
                self.message = f"{STUDENT_KEY} did not answer the question correctly"
                raise InvalidMoveError("StudentIncorrect")

            self.scores = {TEACHER_KEY: 0, STUDENT_KEY: 1}
            self.message = f"{STUDENT_KEY} correctly answered the question"
            self.student_answer = move
    
    def is_over(self) -> bool:
        return self.student_answer is not None

    def get_scores(self):
        return self.scores

    def get_next_action(self) -> Action:

        if self.question is None:
            return Action(name="GenerateQuestion", player_key=TEACHER_KEY, inputs={'target': self.target})
        elif self.teacher_answer is None:
            return Action(name="AnswerQuestion", player_key=TEACHER_KEY, inputs={'question': self.question})
        else:
            return Action(name="AnswerQuestion", player_key=STUDENT_KEY, inputs={'question': self.question})

    def verify_answer(self, answer: str) -> bool:
        try:
            return int(answer) == int(self.target)
        except:
            return False
        
    @classmethod
    def player_definitions(cls) -> List[PlayerDefinition]:
        return [
            PlayerDefinition(player_key=TEACHER_KEY, actions=["GenerateQuestion", "AnswerQuestion"], default_player_class=MathQuizTeacher),
            PlayerDefinition(player_key=STUDENT_KEY, actions=["AnswerQuestion"], default_player_class=MathQuizStudent),
        ]

    def display(self) -> str:
        display_str = f"Next to Act: {self.get_next_action().player_key}\nMessage: {self.message}\n"
        display_str += f"Target: {self.target}\n"
        display_str += f"Question: {self.question}\n"
        display_str += f"Teacher Answer: {self.teacher_answer}\n"
        display_str += f"Student Answer: {self.student_answer}\n"
        display_str += f"Scores: {self.scores}\n"
        return display_str    
    def export(self):
        return {
            "target": self.target,
            "question": self.question,
            "teacher_answer": self.teacher_answer,
            "student_answer": self.student_answer,
            "message": self.message,
            "scores": self.scores,
        }

