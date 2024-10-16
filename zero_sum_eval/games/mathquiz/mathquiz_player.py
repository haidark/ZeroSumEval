import dspy
from zero_sum_eval.player import Player
from zero_sum_eval.registry import PLAYER_REGISTRY, METRIC_REGISTRY

@METRIC_REGISTRY.register("math_question_validation_metric")
def validate_math_question(example, prediction, trace=None):
    # TODO: Implement proper validation logic
    return 1 if prediction.question else 0

@METRIC_REGISTRY.register("math_answer_validation_metric")
def validate_math_answer(example, prediction, trace=None):
    # TODO: Implement proper validation logic
    return 1 if str(prediction) == str(example.answer) else 0

class GenerateQuestion(dspy.Signature):
    """Given a target number, create a challenging math question with the target number as the answer. Make sure not to include the answer in the question."""
    role = dspy.InputField(desc="role")
    message = dspy.InputField(desc="message")
    target = dspy.InputField(desc="target number")
    question = dspy.OutputField(desc="math question with the target number as the answer")

class AnswerQuestion(dspy.Signature):
    """Given a challenging math question, give the answer to the question as a number only"""
    role = dspy.InputField(desc="role")
    message = dspy.InputField(desc="message")
    question = dspy.InputField(desc="math question")
    answer = dspy.OutputField(desc="answer to the math question with number only")

class GenerateQuestionCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_question = dspy.ChainOfThought(GenerateQuestion)

    def forward(self, role, message, target):
        cot_out = self.cot_question(role=role, message=message, target=target)
        return cot_out

class AnswerQuestionCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_answer = dspy.ChainOfThought(AnswerQuestion)

    def forward(self, role, message, question):
        cot_out = self.cot_answer(role=role, message=message, question=question)
        return cot_out

class TeacherModule(dspy.Module):
    def __init__(self, roles, **kwargs):
        super().__init__()
        self.module_dict = dict()
        for role in roles:
            if role == "TeacherGenerateQuestion":
                 self.module_dict[role] = GenerateQuestionCoT()
            elif role == "TeacherAnswerQuestion":
                self.module_dict[role] = AnswerQuestionCoT()
    
    def forward(self, **kwargs):
        role = kwargs.get('role', None)
        return self.module_dict[role](**kwargs)

class StudentModule(dspy.Module):
    def __init__(self, roles, **kwargs):
        super().__init__()
        self.module_dict = {roles[0]: AnswerQuestionCoT()}
    
    def forward(self, **kwargs):
        role = kwargs.get('role', None)
        return self.module_dict[role](**kwargs)

@PLAYER_REGISTRY.register("mathquiz", "mathquiz_teacher")
class MathQuizTeacher(Player):
    def _build_module(self, roles, **module_args):
        return TeacherModule(roles, **module_args)

    def _make_move(self, **kwargs):
        current_role = kwargs.get('role', None)
        trace = self.module(**kwargs)
        if current_role == "TeacherGenerateQuestion":
            return trace.question, trace
        elif current_role == "TeacherAnswerQuestion":
            return trace.answer, trace
        else:
            raise ValueError(f"Invalid role for teacher: {current_role}")

@PLAYER_REGISTRY.register("mathquiz", "mathquiz_student")
class MathQuizStudent(Player):
    def _build_module(self, roles, **module_args):
        return StudentModule(roles, **module_args)

    def _make_move(self, **kwargs):
        current_role = kwargs.get('role', None)
        if current_role == "StudentAnswerQuestion":
            trace = self.module(**kwargs)
            return trace.answer, trace
        else:
            raise ValueError(f"Invalid role for student: {current_role}")
