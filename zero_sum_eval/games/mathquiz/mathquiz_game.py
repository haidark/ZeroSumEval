from zero_sum_eval.game_state import GameState
from random import randint
from zero_sum_eval.registry import GAME_REGISTRY


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

    The roles for this game are:
        TeacherGenerateQuestion
        TeacherAnswerQuestion
        StudentAnswerQuestion

    The environment for this game is:
        question: a math question
        teacher_answer: the teacher's answer to the math question
        student_answer: the student's answer to the math question
    """
    def __init__(self, roles=None, environment=None, context=None, target=None):
        super().__init__()
        self.environment = environment if environment is not None else \
            {"question": None, "teacher_answer": None, "student_answer": None}
        self.roles = self.get_next_roles(self.environment) if roles is None else roles
        self.context = context if context is not None else {"history": [], "message": None}
        self.target = target if target is not None else str(randint(1, 1000))

    def initialize(self, roles=None, environment=None, context=None, target=None):
        return MathQuizGame(
            roles=roles,
            environment=environment,
            context=context,
            target=target
        )

    def update_game(self, move):
        new_context = self.context.copy()
        new_environment = self.environment.copy()
        if self.roles[0] == "TeacherGenerateQuestion":
            new_environment['question'] = move
        elif self.roles[0] == "TeacherAnswerQuestion":
            new_environment['teacher_answer'] = move
        elif self.roles[0] == "StudentAnswerQuestion":
            new_environment['student_answer'] = move

        return self.initialize(
            roles=self.roles,
            environment=new_environment,
            context=new_context,
            target=self.target
        )

    def query_game(self):  
        new_context = self.context.copy()
        new_roles = self.get_next_roles(self.environment)
        msg = self.validate_game() 
        new_context['message'] = msg if msg is not None else f"You will move as {new_roles[0]}" 

        return self.initialize(
            environment=self.environment,
            context=new_context,
            roles=new_roles,
            target=self.target
        )

    def verify_answer(self, answer):
        return str(answer) == str(self.target)

    def validate_game(self):
        current_role = self.roles[0]
        if current_role == "TeacherGenerateQuestion":
            return None
        elif current_role == "TeacherAnswerQuestion":
            if self.verify_answer(self.environment['teacher_answer']):
                return None
            else:
                return "TeacherIncorrect"
        elif current_role == "StudentAnswerQuestion":
            if self.verify_answer(self.environment['teacher_answer']):
                return "StudentCorrect"
            else:
                return "StudentIncorrect"

    def get_next_roles(self, environment):
        if environment['question'] is None:
            return ['TeacherGenerateQuestion', 'TeacherAnswerQuestion', 'StudentAnswerQuestion']
        elif environment['teacher_answer'] is None:
            return ['TeacherAnswerQuestion', 'StudentAnswerQuestion']
        else:
            return ['StudentAnswerQuestion']

    def export(self):
        current_role = self.roles[0]
        if current_role == "TeacherGenerateQuestion":
            return {
                'role': self.roles[0],
                'environment': self.target,
                'context': self.context
            }
        elif current_role  in ("TeacherAnswerQuestion", "StudentAnswerQuestion"):
            return {
                'role': self.roles[0],
                'environment': self.environment['question'],
                'context': self.context
            }
        else:
            raise ValueError("Invalid role")
    
    def display(self):
        display_str = f"Role to Act: {self.roles[0]}\nMessage: {self.context['message']}\n"
        display_str += f"{self.environment}\n"
        display_str += f"Target: {self.target}\n"
        return display_str


if __name__ == "__main__":
    pass