from zero_sum_eval.game_state import GameState
from random import randint
from zero_sum_eval.registry import GAME_REGISTRY
from typing import Dict, List, Optional

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

    def instantiate(self, environment: Dict, context: Dict, roles: List[str], **kwargs) -> None:
        self.environment = environment if environment else {
            "question": None,
            "teacher_answer": None,
            "student_answer": None
        }
        self.context = context if context else {"history": [], "message": None}
        self.roles = roles if roles else self.get_next_roles()
        self.target = kwargs.get('target', str(randint(1, 1000)))

    def update_game(self, move: str) -> GameState:
        new_state = MathQuizGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy(),
            target=self.target
        )
        current_role = new_state.roles[0]
        new_state.context['message'] = None   
        if current_role == "TeacherGenerateQuestion":
            new_state.environment['question'] = move
            new_state.roles = new_state.get_next_roles()
        elif current_role == "TeacherAnswerQuestion":
            new_state.environment['teacher_answer'] = move
            if self.verify_answer(move):
                new_state.roles = new_state.get_next_roles()
            else:
                new_state.context['message'] = f"Teacher's previous answer ({move})was incorrect."
        elif current_role == "StudentAnswerQuestion":
            new_state.environment['student_answer'] = move
            if self.verify_answer(move):
                new_state.roles = new_state.get_next_roles()
            else:
                new_state.context['message'] = f"Student's previous answer ({move}) was incorrect."
        return new_state

    def query_game(self) -> GameState:
        new_state = MathQuizGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy(),
            target=self.target
        )
        
        msg = new_state.validate_game()
        new_state.context['message'] = msg if msg else f"You will move as {new_state.roles[0]}"
        return new_state

    def validate_game(self) -> Optional[str]:
        if self.environment['student_answer']: # student attempted to answer
            if self.verify_answer(self.environment['student_answer']):
                return "StudentCorrect"
            else:
                return "StudentIncorrect"
        if self.environment['teacher_answer']: # teacher attempted to answer
            if self.verify_answer(self.environment['teacher_answer']):
                return None
            else:
                return "TeacherIncorrect"
        return None

    def get_next_roles(self) -> List[str]:
        if self.environment['question'] is None:
            return ['TeacherGenerateQuestion', 'TeacherAnswerQuestion', 'StudentAnswerQuestion']
        elif self.environment['teacher_answer'] is None:
            return ['TeacherAnswerQuestion', 'StudentAnswerQuestion']
        else:
            return ['StudentAnswerQuestion']

    def player_inputs(self) -> Dict[str, str]:
        current_role = self.roles[0]
        if current_role == "TeacherGenerateQuestion":
            return {
                'role': self.roles[0],
                'target': self.target,
                'message': self.context['message']
            }
        elif current_role in ("TeacherAnswerQuestion", "StudentAnswerQuestion"):
            return {
                'role': self.roles[0],
                'question': self.environment['question'],
                'message': self.context['message']
            }
        else:
            raise ValueError("Invalid role")

    def verify_answer(self, answer: str) -> bool:
        return str(answer) == str(self.target)

    def display(self) -> str:
        display_str = f"Role to Act: {self.roles[0]}\nMessage: {self.context['message']}\n"
        display_str += f"Environment: {self.environment}\n"
        display_str += f"Target: {self.target}\n"
        return display_str


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