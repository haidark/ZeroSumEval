import os
import textwrap
import ast
import secrets
from typing import Dict
from zero_sum_eval.core.game_state import Action, GameState, InvalidMoveError
from zero_sum_eval.core.player import PlayerDefinition
from zero_sum_eval.core.registry import GAME_REGISTRY
from zero_sum_eval.utils.types import Move

from .pyjail_player import PyJailPlayer
import io
import sys


@GAME_REGISTRY.register("pyjail")
class PyJailGame(GameState):
    def __init__(self, show_source_code: bool = True, max_attacks: int = 5, ask_permission: bool = True, **kwargs) -> None:
        """
        Initializes the PyJail game instance.

        Args:
            show_source_code (bool): If True, the source code will be shown to players trying to solve it. Defaults to True.
            max_attacks (int): The maximum number of attacks allowed. Defaults to 5.
            ask_permission (bool): If True, asks for user permission to continue. Defaults to True.
            **kwargs: Additional keyword arguments passed to the superclass initializer.

        Raises:
            ValueError: If the user does not give permission to continue.

        Attributes:
            show_source_code (bool): Indicates whether the source code should be shown.
            history (list): A list to store the history of actions.
            pyjail_code (str or None): The code for the PyJail game.
            defender_solution (str or None): The solution provided by the defender.
            attacker_solution (str or None): The solution provided by the attacker.
            flag (str): A secret flag generated for the game.
            max_attacks (int): The maximum number of attacks allowed.
        """
        super().__init__(**kwargs)
        if ask_permission:
            user_input = input(
                "WARNING: This game is designed to be played with a trusted defender and attacker, as it involves executing arbitrary code. Do you want to continue? (y/n): "
            )
            if user_input.lower() != "y":
                raise ValueError("User did not give permission to continue")

        self.show_source_code = show_source_code
        self.history = []
        self.pyjail_code = None
        self.defender_solution = None
        self.attacker_solution = None
        self.flag = secrets.token_hex(12)
        self.max_attacks = max_attacks

    def update_game(self, move: Move):
        code = move.value

        code = textwrap.dedent(code)

        action = self.get_next_action()

        if action.name == "GeneratePyJail":
            code_has_func = self._check_for_jail_function(code)
            if code_has_func == False:
                raise InvalidMoveError(f"Code does not contain a 'jail' function")
            else:
                self.pyjail_code = code

        elif action.name in "SolvePyJail":
            output = self._execute_pyjail(pyjail_code=self.pyjail_code, user_input=code)

            if self.flag in output:
                if self.defender_solution is None:
                    self.defender_solution = code
                    self.history = []
                else:
                    self.attacker_solution = code

            history_message = f"Executed code:\n{code}\n\nOutput: {output}"
            self.history.append(history_message)

    def get_next_action(self):
        if self.pyjail_code is None:
            return Action(name="GeneratePyJail", player_key="defender", inputs={})
        elif self.defender_solution is None:
            return Action(name="SolvePyJail", player_key="defender", inputs={'pyjail_code': self.pyjail_code, 'history': "\n".join(self.history)})
        elif self.attacker_solution is None:
            return Action(name="SolvePyJail", player_key="attacker", inputs={'pyjail_code': self.pyjail_code, 'history': "\n".join(self.history)})

    def player_definitions(self):
        return [
            PlayerDefinition(player_key="defender", actions=["GeneratePyJail", "SolvePyJail"], default_player_class=PyJailPlayer),
            PlayerDefinition(player_key="attacker", actions=["SolvePyJail"], default_player_class=PyJailPlayer)
        ]

    def is_over(self):
        attacker_won = (
            self.defender_solution is not None
            and self.attacker_solution is not None
            and any(self.flag in output for output in self.history)
        )
        return attacker_won or len(self.history) >= self.max_attacks

    def get_scores(self):
        if self.defender_solution is None:
            return {"defender": 0, "attacker": 0}
        elif self.attacker_solution is None:
            return {"defender": 1, "attacker": 0}
        elif any(self.flag in output for output in self.history):
            return {"defender": 0, "attacker": 1}
        else:
            return {"defender": 1, "attacker": 0}

    def _check_for_jail_function(self, code_string):
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'jail':
                    return True
            return False
        except SyntaxError:
            return False

    def _execute_pyjail(self, pyjail_code: str, user_input: str) -> str:
        # Set the FLAG environment variable
        os.environ['FLAG'] = self.flag
        var_dict = {}

        # Execute the provided PyJail code
        exec(pyjail_code, var_dict)

        # Redirect stdout to capture prints
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout

        try:
            # Execute the 'jail' function with user input
            result = var_dict['jail'](user_input)
        except Exception as e:
            # Handle any exceptions and return an error message
            result = f"Error: {e}"
        finally:
            # Reset stdout to its original state
            sys.stdout = old_stdout

        # Get the captured stdout output
        output = new_stdout.getvalue()
        return output + str(result)

    def display(self) -> str:
        display_str = f"Defender Code: {'Set' if self.pyjail_code else 'Not set'}\n"
        if self.pyjail_code:
            display_str += f"{self.pyjail_code}\n"
        display_str += f"Defender Solution: {'Set' if self.defender_solution else 'Not set'}\n"
        if self.defender_solution:
            display_str += f"{self.defender_solution}\n"
        display_str += f"Attacker Solution: {'Set' if self.attacker_solution else 'Not set'}\n"
        if self.attacker_solution:
            display_str += f"{self.attacker_solution}\n"
        if self.history:
            display_str += "\nHistory:\n"
            for i, entry in enumerate(self.history):
                display_str += f"------ Attack {i + 1} ------\n"
                display_str += f"{entry}\n\n"
        return display_str

    def export(self):
        return {
            "pyjail_code": self.pyjail_code,
            "defender_solution": self.defender_solution,
            "attacker_solution": self.attacker_solution,
            "history": self.history,
            "flag": self.flag
        }
