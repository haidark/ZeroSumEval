import dis
from zero_sum_eval.types import Move
from zero_sum_eval.games.mathquiz.mathquiz_player import MathQuizStudent, MathQuizTeacher
from zero_sum_eval.game_state import GameState, InvalidMoveError, PlayerDescription
from random import randint
from zero_sum_eval.registry import GAME_REGISTRY
from typing import Dict

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
        TeacherGenerateQuestion
        TeacherAnswerQuestion
        StudentAnswerQuestion

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
        self.message = "TeacherGenerateQuestion"

    def update_game(self, move: Move) -> GameState:
        next_action = self.get_next_action()
        move = move.value
        if next_action == "TeacherGenerateQuestion":
            self.question = move
            self.message = self.get_next_action()
        elif next_action == "TeacherAnswerQuestion":
            if not self.verify_answer(move):
                # If the teacher's answer is incorrect, generate a new target number and raise an error to be caught by the game manager
                self.target = str(randint(1, 1000))
                self.question = None
                self.scores = {"teacher": 0, "student": 1}
                self.message = "Teacher did not answer the question correctly"
                raise InvalidMoveError("TeacherIncorrect")
            self.teacher_answer = move
        elif next_action == "StudentAnswerQuestion":
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
        return super().get_scores()

    def get_next_action(self):
        if self.question is None:
            return "TeacherGenerateQuestion"
        elif self.teacher_answer is None:
            return "TeacherAnswerQuestion"
        else:
            return "StudentAnswerQuestion"

    def player_inputs(self) -> Dict[str, str]:
        next_action = self.get_next_action()
        if next_action == "TeacherGenerateQuestion":
            return {'target': self.target}
        elif next_action in ("TeacherAnswerQuestion", "StudentAnswerQuestion"):
            return {'question': self.question}
        else:
            raise ValueError("Invalid action")

    def verify_answer(self, answer: str) -> bool:
        try:
            return int(answer) == int(self.target)
        except:
            return False
        
    def player_descriptions(self):
        return [
            PlayerDescription(name="teacher", actions=["TeacherGenerateQuestion", "TeacherAnswerQuestion"], default_player_class=MathQuizTeacher),
            PlayerDescription(name="student", actions=["StudentAnswerQuestion"], default_player_class=MathQuizStudent),
        ]

    def display(self) -> str:
        display_str = f"Role to Act: {self.get_next_action()}\nMessage: {self.message}\n"
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


if __name__ == "__main__":
    math_quiz = MathQuizGame()
    math_quiz.instantiate(None, None, None)
    print(math_quiz.export())

    # Teacher generates question
    math_quiz = math_quiz.update_game("What is 5 + 7?")
    print(math_quiz.export())

    print(math_quiz.query_game().export())
    # Teacher answers question
    math_quiz = math_quiz.update_game("12")
    print(math_quiz.export())

    # Student answers question
    math_quiz = math_quiz.update_game("12")
    print(math_quiz.export())

    validation_result = math_quiz.validate_game()
    if validation_result:
        print(f"Game validation result: {validation_result}")
    else:
        print("Game is valid.")