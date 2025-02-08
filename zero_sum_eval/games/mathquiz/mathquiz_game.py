from random import randint
from zero_sum_eval.games.mathquiz.mathquiz_player import MathQuizStudent, MathQuizTeacher
from zero_sum_eval.game_state import Action, GameState, InvalidMoveError, PlayerDefinition
from zero_sum_eval.registry import GAME_REGISTRY
from zero_sum_eval.player import Move
from typing import Dict, List

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
        self.scores = {"teacher": 0, "student": 0}
        self.target = kwargs.get('target', str(randint(1, 1000)))
        self.message = "Teacher to generate a question"

    def update_game(self, move: Move):
        next_action = self.get_next_action()
        move = move.value
        if next_action.name == "GenerateQuestion":
            self.question = move
            self.message = "Teacher to answer the question"
        elif next_action.name == "AnswerQuestion" and next_action.player.player_key == "teacher":
            if not self.verify_answer(move):
                # If the teacher's answer is incorrect, generate a new target number and raise an error to be caught by the game manager
                self.target = str(randint(1, 1000))
                self.question = None
                self.scores = {"teacher": 0, "student": 1}
                self.message = "Teacher did not answer the question correctly"
                raise InvalidMoveError("TeacherIncorrect")
            self.message = "Student to answer the question"
            self.teacher_answer = move
        elif next_action.name == "AnswerQuestion" and next_action.player.player_key == "student":
            if not self.verify_answer(move):
                # If the student's answer is incorrect, raise an error to be caught by the game manager
                self.scores = {"teacher": 1, "student": 0}
                self.message = "Student did not answer the question correctly"
                raise InvalidMoveError("StudentIncorrect")

            self.scores = {"teacher": 0, "student": 1}
            self.message = "Student correctly answered the question"
            self.student_answer = move
    
    def is_over(self) -> bool:
        return self.student_answer is not None

    def get_scores(self):
        return self.scores

    def get_next_action(self) -> Action:
        if self.question is None:
            return Action("GenerateQuestion", self.players["teacher"])
        elif self.teacher_answer is None:
            return Action("AnswerQuestion", self.players["teacher"])
        else:
            return Action("AnswerQuestion", self.players["student"])

    def player_inputs(self) -> Dict[str, str]:
        next_action = self.get_next_action().name
        if next_action == "GenerateQuestion":
            return {'target': self.target}
        elif next_action == "AnswerQuestion":
            return {'question': self.question}
        else:
            raise ValueError("Invalid action")

    def verify_answer(self, answer: str) -> bool:
        try:
            return int(answer) == int(self.target)
        except:
            return False
        
    def player_definitions(self) -> List[PlayerDefinition]:
        return [
            PlayerDefinition(player_key="teacher", actions=["GenerateQuestion", "AnswerQuestion"], default_player_class=MathQuizTeacher),
            PlayerDefinition(player_key="student", actions=["AnswerQuestion"], default_player_class=MathQuizStudent),
        ]

    def display(self) -> str:
        display_str = f"Next to Act: {self.get_next_action().player.player_key}\nMessage: {self.message}\n"
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

