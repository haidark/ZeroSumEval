import dspy
from zero_sum_eval.player import Player
from zero_sum_eval.registry import PLAYER_REGISTRY, METRIC_REGISTRY
from typing import List
import ast
import re


@METRIC_REGISTRY.register("pyjail_code_validation_metric")
def validate_pyjail_code(example, prediction, trace=None):
    match = re.search(r'###START(.*?)###END', move.decode('utf-8'), re.DOTALL)
    code = match.group(1).strip()
    try:
        result = ast.parse(prediction.code) 
        return 1
    except Exception:
        return 0

class GenerateCode(dspy.Signature):
    """Generate PyJail code that makes access harder to the FLAG environment variable"""
    role = dspy.InputField(desc="roles of the player")
    message = dspy.InputField(desc="message from the game manager")
    code = dspy.OutputField(desc="PyJail code to limit access to FLAG, start with ###START, end with ###END")

class SolveCode(dspy.Signature):
    """Given PyJail code, generate a solution to access the FLAG environment variable"""
    role = dspy.InputField(desc="roles of the player")
    message = dspy.InputField(desc="message from the game manager")
    defender_code = dspy.InputField(desc="PyJail code to solve")
    code = dspy.OutputField(desc="Solution code to access FLAG start with ###START, end with ###END")

class PyJailModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_code = dspy.ChainOfThought(GenerateCode)
        self.solve_code = dspy.ChainOfThought(SolveCode)
    
    def forward(self, **kwargs):
        role = kwargs.get('role', None)
        if role == "DefenderGenerateCode":
            return self.generate_code(**kwargs)
        elif role in ["DefenderSolveCode", "AttackerSolveCode"]:
            return self.solve_code(**kwargs)
        else:
            raise ValueError(f"Invalid role: {role}")

@PLAYER_REGISTRY.register("pyjail", "pyjail_player")
class PyJailPlayer(Player):
    def __init__(self, id: str, role: str, lm: dict, **kwargs):
        super().__init__(id, [role], lm, **kwargs)
        self.role = role

    def _build_module(self, **module_args):
        return PyJailModule(**module_args)

    def _make_move(self, **kwargs):
        trace = self.module(**kwargs)
        return trace.code
