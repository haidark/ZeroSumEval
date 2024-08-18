import dspy
from zero_sum_eval.player import Player
from zero_sum_eval.registry import PLAYER_REGISTRY, METRIC_REGISTRY

@METRIC_REGISTRY.register("pyjail_challenge_validation_metric")
def validate_pyjail_challenge(example, prediction, trace=None):
    # TODO: Implement proper validation logic
    return 1 if prediction.challenge else 0

@METRIC_REGISTRY.register("pyjail_attack_validation_metric")
def validate_pyjail_attack(example, prediction, trace=None):
    # TODO: Implement proper validation logic
    return 1 if prediction.attack else 0

class CreateChallenge(dspy.Signature):
    """Create a Python jail challenge that prevents access to the flag while allowing some code execution."""
    role = dspy.InputField(desc="role")
    message = dspy.InputField(desc="message")
    flag = dspy.InputField(desc="flag to protect")
    challenge = dspy.OutputField(desc="Python code for the pyjail challenge")

class CreateAttack(dspy.Signature):
    """Create an attack to break out of the Python jail and extract the flag."""
    role = dspy.InputField(desc="role")
    message = dspy.InputField(desc="message")
    challenge = dspy.InputField(desc="pyjail challenge code")
    attempts = dspy.InputField(desc="number of attempts made")
    max_attempts = dspy.InputField(desc="maximum number of attempts allowed")
    attack = dspy.OutputField(desc="Python code to break out of the jail")

class DefenderModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.create_challenge = dspy.ChainOfThought(CreateChallenge)

    def forward(self, role, message, flag):
        return self.create_challenge(role=role, message=message, flag=flag)

class AttackerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.create_attack = dspy.ChainOfThought(CreateAttack)

    def forward(self, role, message, challenge, attempts, max_attempts):
        return self.create_attack(role=role, message=message, challenge=challenge, attempts=attempts, max_attempts=max_attempts)

@PLAYER_REGISTRY.register("pyjail", "pyjail_defender")
class PyjailDefender(Player):
    def _build_module(self, **module_args):
        return DefenderModule(**module_args)

    def _make_move(self, **kwargs):
        trace = self.module(**kwargs)
        return trace.challenge

@PLAYER_REGISTRY.register("pyjail", "pyjail_attacker")
class PyjailAttacker(Player):
    def _build_module(self, **module_args):
        return AttackerModule(**module_args)

    def _make_move(self, **kwargs):
        trace = self.module(**kwargs)
        return trace.attack