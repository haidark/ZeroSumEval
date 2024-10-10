import docker
from io import StringIO
import textwrap
import time
import re
import ast
import json
import yaml
import logging
import secrets
from dspy import Prediction
from typing import Dict, List, Optional
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY


#TODO add support for custom imports for pyjail 

logging.basicConfig(level = logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING)

logger = logging.getLogger('ZeroSumEval')

@GAME_REGISTRY.register("pyjail")
class PyjailGame(GameState):

    def instantiate(self, environment: Dict = None, context: Dict = None, roles: List[str] = None, **kwargs) -> None:
        self.generate_pyjail_successful = False
        self.validate_pyjail_successful = False
        self.solve_pyjail_successful = False
        self.roles = roles if roles is not None else self.get_next_roles() 
        self.docker_client = docker.from_env()
        self.container = None
        self.environment = environment or {
            "pyjail_code": None,
            "defender_solution": None,
            "attacker_solution": None
        }
        self.context = context or {"message": "", "history": {"defender_history":[], "attacker_history":[]}, "move_history": []}
        self.flag = None

        container_name = 'pyjail_container'
        try:
            self.container = self.docker_client.containers.get(container_name)

            if self.container.status != 'running':
                self.container.start()
            res = self.container.exec_run("printenv FLAG")
            self.flag = res.output
        except docker.errors.NotFound:
            logger.info(f"Creating container '{container_name}'...")
            self.flag = secrets.token_hex(12) # Generate the flag
            self.container = self.docker_client.containers.run(
                'python:3.9',
                name=container_name,
                detach=True,
                environment={'FLAG': self.flag},
                command='tail -f /dev/null',  # Keep the container running
            )
            # Wait for the container to start
            max_retries = 10
            retry_interval = 1
            for _ in range(max_retries):
                if self.container.status == 'running':
                    break
                time.sleep(retry_interval)
                self.container.reload()
            else:
                raise RuntimeError("Container failed to start within the expected time.")

    def update_game(self, move: str, trace: Optional[Prediction] = None) -> 'PyjailGame':
        new_state = PyjailGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )
        new_state.docker_client = self.docker_client
        new_state.container = self.container
        new_state.flag = self.flag

        new_state.generate_pyjail_successful = self.generate_pyjail_successful  
        new_state.validate_pyjail_successful  = self.validate_pyjail_successful 
        new_state.solve_pyjail_successful = self.solve_pyjail_successful
        new_state.context['move_history'].append(move)
        try:
            last_code_block = self._extract_last_code_block(move)
            if last_code_block:
                move = last_code_block
            else:
                logger.debug(f"No code block found in: {move}")
        except Exception as e:
            logger.exception(f"Error processing move: {e}")

        dedented_move = textwrap.dedent(move)

        current_role = new_state.roles[0]

        if current_role == "DefenderGenerateCode":
            
            try:
                code_has_func = self._verify_code_has_function(move, 'jail')
                if code_has_func == False:

                    new_state.context['message'] =  'please include function jail(user_input):'
                else:
                    new_state.generate_pyjail_successful = True 
                    new_state.context['history']['defender_history'] = []
                    new_state.environment['pyjail_code'] = dedented_move
                    new_state.context['message'] = None 
            except SyntaxError as e:
                new_state.context['message'] =  f"Syntax error in pyjail: {str(e)}"
            except Exception as e:
                new_state.context['message'] =  f"{str(e)}"


        elif current_role in ["DefenderSolveCode", "AttackerSolveCode"]:
            pyjail_code = self.environment['pyjail_code']
            user_input = dedented_move

            res = new_state._execute_pyjail(pyjail_code, user_input)
            new_state.generate_pyjail_successful = self.generate_pyjail_successful  

            output = res.output

            hist_res = f"attempt result: {output.decode('utf-8').strip()}"
            histname = 'defender' if not self.roles[0] == 'AttackerSolveCode' else 'attacker'
            new_state.context['history'][f'{histname}_history'].append(hist_res)

            if new_state.flag in output:

                if current_role == "DefenderSolveCode":

                    new_state.environment['defender_solution'] = user_input
                    new_state.context['message'] = None
                    new_state.validate_pyjail_successful = True
                else:
                    new_state.environment['attacker_solution'] = user_input
                    new_state.context['message'] = 'AttackerCorrect'
                    new_state.solve_pyjail_successful = True
            else:
                if current_role == "DefenderSolveCode":
                    new_state.environment['defender_solution'] = user_input
                    new_state.context['message'] = "Defender failed to retrieve the flag."
                else:
                    new_state.context['message'] = "Attacker failed to retrieve the flag."

         
        new_state.roles = new_state.get_next_roles()

        return new_state

    def _extract_last_code_block(self,text):
        matches = re.findall(r'###START(.*?)###END', text, re.DOTALL)
        if matches:
            return matches[-1].strip()
        return None

    def _verify_code_has_function(self, code_string, name):
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'jail':
                    return True
            return False
        except SyntaxError:
            return False
           
            

    def _execute_pyjail(self, pyjail_code: str, user_input: str) -> str:

        user_input = textwrap.dedent(user_input)
        
        script = f"""
{pyjail_code}

user_input = '''{user_input}'''

x = jail(user_input)
print(x)
"""
        
        try:
            output = self.container.exec_run(["python", "-c", script], environment={"FLAG": self.flag})
        except docker.errors.APIError as e:
            raise ValueError(str(e))
        return output

    def query_game(self) -> GameState:
        new_state = PyjailGame()
        new_state.docker_client = self.docker_client
        new_state.container = self.container
        new_state.flag = self.flag
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )

        new_state.generate_pyjail_successful = self.generate_pyjail_successful  
        new_state.validate_pyjail_successful  = self.validate_pyjail_successful 
        new_state.solve_pyjail_successful = self.solve_pyjail_successful

        msg = new_state.validate_game()
        new_state.context['message'] = msg if msg is not None else f"You will move as {new_state.roles[0]}"

        current_role = new_state.get_next_roles

        if current_role == "DefenderGenerateCode":
            new_state.context['message'] += "\\nImplement a Pyjail by defining a 'jail(user_input)' function. Start and end your code with ###START and ###END. Example:\\n###START\\ndef jail(user_input):\\n    # Your code here\\n    pass\\n###END"

        elif current_role == "DefenderSolveCode":
            new_state.context['message'] += "\noutput valid python syntax, starting and ending valid python with ###START, and ###END that will be the solution to the pyjail ctf challenge you generated"
        elif current_role == "AttackerSolveCode":
            new_state.context['message'] += "\noutput valid python syntax, starting and ending valid python with ###START, and ###END that will be the soltuion to a pyjail ctf challenge"
        return new_state

    def validate_game(self) -> Optional[str]:
        if self.roles[0] == "AttackerSolveCode" and not self.solve_pyjail_successful:
            return "DefenderWins"
        
        return self.context['message']

    def get_next_roles(self) -> List[str]:
        
        if self.solve_pyjail_successful == True: 
            return ['AttackerSolveCode', "DefenderGenerateCode", 'DefenderSolveCode']
        elif self.validate_pyjail_successful == True:
            return ['AttackerSolveCode', "DefenderGenerateCode", 'DefenderSolveCode']
        elif self.generate_pyjail_successful == True:
            return ['DefenderSolveCode', 'AttackerSolveCode', "DefenderGenerateCode"]

        else:

            return [ "DefenderGenerateCode", 'DefenderSolveCode', 'AttackerSolveCode']

    def player_inputs(self) -> Dict[str, str]:
        current_role = self.roles[0]
        if current_role == "DefenderGenerateCode":
            return {
                'role': current_role,
                'message': self.context['message'],
                'history': self.context['history']['defender_history']
            }
        elif current_role == "DefenderSolveCode":
            return {
                'role': current_role,
                'pyjail_code': self.environment['pyjail_code'],
                'message': self.context['message'],
                'history': self.context['history']['defender_history']
            }
        elif current_role == "AttackerSolveCode":

            return {
                'role': current_role,
                'pyjail_code': self.environment['pyjail_code'],
                'message': self.context['message'],
                'history': self.context['history']['attacker_history']
            }
        else:
            raise ValueError(f"Invalid role: {current_role}")

    def display(self) -> str:
        display_str = f"Current Role: {self.roles[0] if self.roles else 'Not set'}\n"
        display_str += f"Message: {self.context['message']}\n\n"

        display_str += "Environment:\n"
        display_str += f"  Defender Code: {'Set' if self.environment['pyjail_code'] else 'Not set'}\n"
        if self.environment['pyjail_code']:
            display_str += f"    {self.environment['pyjail_code']}\n"
        display_str += f"  Defender Solution: {'Set' if self.environment['defender_solution'] else 'Not set'}\n"
        if self.environment['defender_solution']:
            display_str += f"    {self.environment['defender_solution']}\n"
        display_str += f"  Attacker Solution: {'Set' if self.environment['attacker_solution'] else 'Not set'}\n"
        if self.environment['attacker_solution']:
            display_str += f"    {self.environment['attacker_solution']}\n"
        histname = 'defender' if not self.roles[0] == 'AttackerSolveCode' else 'attacker'
        display_str += "\nHistory:\n"
        for entry in self.context['history'][f"{histname}_history"]:

            display_str += f"  {entry}\n"

        return display_str

    def export(self):
        return yaml.dump({
            'environment': self.environment,
            'context': self.context,
            'roles': self.roles
        })



if __name__ == "__main__":
    def run_test():
        # Initialize the game
        game = PyjailGame()
        game.instantiate()
        logger.info("Initial game state:")
        logger.info(game.display())
        game=game.query_game()
        pyjail_code = """
python
###START
import os

def jail(user_input):
    # Create a custom dictionary with modified environment variables
    custom_env = dict(os.environ)

    # Remove the FLAG from the custom environment
    if 'FLAG' in custom_env:
        del custom_env['FLAG']

    # Limit available built-in functions
    safe_builtins = {
        'abs': abs, 'bool': bool, 'int': int, 'float': float, 'str': str,
        'list': list, 'tuple': tuple, 'dict': dict, 'set': set,
        'max': max, 'min': min, 'sum': sum, 'len': len,
        'print': print
    }

    # Create a restricted global environment
    restricted_globals = {
        '__builtins__': safe_builtins,
        'env': custom_env
    }

    try:
        # Execute user input in the restricted environment
        exec(user_input, restricted_globals)
    except Exception as e:
        print(f"Error: {e}")

###END
"""
        game = game.update_game(pyjail_code)
        logger.info("\nAfter Defender Generate Code:")
        logger.info(game.display())
        logger.info(game.query_game().validate_game())

        ''' 
       defender_solution = """
    ###START
    __import__('os').system('echo $FLAG')
    ###END
    """
        game = game.update_game(defender_solution)
        logger.info(game.display())
        game = game.query_game()

        #defender wins
        attacker_solution = """
    ###START
def custom(): 
    import os
    os.system('echo $FLAG')
custom()
    ###END
    """
        game = game.update_game(attacker_solution)
        logger.info(game.display())

        '''

        logger.info(game.validate_game())

    run_test()
