import dspy
import re
import logging
from zero_sum_eval.core.player import Player
from zero_sum_eval.core.registry import PLAYER_REGISTRY 

logger = logging.getLogger(__name__)

class GenerateCode(dspy.Signature):
    """Generate PyJail code that makes access harder to the FLAG environment variable"""
    code = dspy.OutputField(desc="PyJail code to limit access to FLAG, start with ###START, end with ###END. Make sure to define a function with the signature 'def jail(user_input: str) -> str:'")

class SolveCode(dspy.Signature):
    """Given PyJail code, generate a solution to access the FLAG environment variable"""
    pyjail_code = dspy.InputField(desc="PyJail code to solve")
    history = dspy.InputField(desc="History of previous attempts and outputs")
    code = dspy.OutputField(desc="Solution code to access FLAG start with ###START, end with ###END")

class GeneratePyjailCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_generate = dspy.ChainOfThought(GenerateCode)

    def forward(self):
        cot_out = self.cot_generate()
        matches = re.findall(r'###START(.*?)###END', cot_out.code, re.DOTALL)
        if matches:
            cot_out.code = matches[-1].strip()
        else:
            dspy.Suggest(False, "Parsing Error: Code is not wrapped in ###START and ###END")
        
        if "def jail(" not in cot_out.code:
            dspy.Suggest(False, "Parsing Error: Code does not contain a 'jail' function")

        return cot_out
        
class SolvePyjailCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot_solve = dspy.ChainOfThought(SolveCode)

    def forward(self, pyjail_code, history):
        cot_out = self.cot_solve(pyjail_code=pyjail_code, history=history)
        matches = re.findall(r'###START(.*?)###END', cot_out.code, re.DOTALL)

        if matches:
            cot_out.code = matches[-1].strip()
        else:
            dspy.Suggest(False, "Parsing Error: Code is not wrapped in ###START and ###END")

        return cot_out

@PLAYER_REGISTRY.register("pyjail", "pyjail_player")
class PyJailPlayer(Player):
    def init_actions(self):
        return {
            "GeneratePyJail": GeneratePyjailCoT(),
            "SolvePyJail": SolvePyjailCoT()
        }
