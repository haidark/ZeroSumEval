import docker
import time
import re
import ast
import json
import yaml
import secrets
from typing import Dict, List, Optional
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY

@GAME_REGISTRY.register("pyjail")
class PyJailGame(GameState):

    def instantiate(self, environment: Dict = None, context: Dict = None, roles: List[str] = None, **kwargs) -> None:
        self.docker_client = docker.from_env()
        self.container = None
        self.environment = environment or {
            "defender_code": None,
            "defender_solution": None,
            "attacker_solution": None
        }
        self.context = context or {"message": "", "history": {"defender_history":[], "attacker_history":[]}, "move_history": []}
        self.roles = roles or ['DefenderGenerateCode', 'DefenderSolveCode', 'AttackerSolveCode']
        self.flag = None
        self.last_move_successful = False

        container_name = 'pyjail_container'
        try:
            self.container = self.docker_client.containers.get(container_name)
            res = self.container.exec_run("printenv FLAG")
            self.flag = res.output
        except docker.errors.NotFound:
            print(f"Creating container '{container_name}'...")
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
    
    def update_game(self, move: str) -> 'PyJailGame':
        new_state = PyJailGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )
        new_state.docker_client = self.docker_client
        new_state.container = self.container
        new_state.flag = self.flag
        
        new_state.context['move_history'].append(move)
        try:
            match = re.search(r'###START(.*?)###END', move, re.DOTALL)
            move = match.group(1).strip()
        except Exception as e:
            move = move.strip()
        current_role = new_state.roles[0]

        if current_role == "DefenderGenerateCode":
            try:
                ast.parse(move)
                new_state.environment['defender_code'] = move
                new_state.last_move_successful = True
                new_state.context['message'] = None
            except SyntaxError as e:
                new_state.context['message'] =  f"Syntax error in pyjail: {str(e)}" 
                

        elif current_role in ["DefenderSolveCode", "AttackerSolveCode"]:
            defender_code = new_state.environment['defender_code']
            user_input = move

            res = new_state._execute_pyjail(defender_code, user_input)
            output = res.output
            new_state.context['message'] = new_state.context['message'] or ''
            
            hist_res = f"attempt result: {output.decode('utf-8').strip()}"
            histname = 'defender' if not self.roles[0] == 'AttackerSolve' else 'attacker'
            new_state.context['history'][f'{histname}_history'].append(hist_res)

            if new_state.flag in output: 

                new_state.last_move_successful = True

                if current_role == "DefenderSolveCode":

                    new_state.environment['defender_solution'] = user_input
                    new_state.context['message'] = None 
                else:  
                    new_state.environment['attacker_solution'] = user_input
                    new_state.context['message'] = 'AttackerWins'
                    self.last_move_successful = True
            else:
                if current_role == "DefenderSolveCode":
                    new_state.environment['defender_solution'] = user_input
                    new_state.context['message'] += "\nDefender failed to retrieve the flag."
                else:  
                    new_state.context['message'] += "\nAttacker failed to retrieve the flag."

        new_state.roles = new_state.get_next_roles()
        return new_state

    def _execute_pyjail(self, pyjail_code: str, user_input: str) -> str:
    #TODO: manually set the indent of user code 
        script = f"""
import os

{pyjail_code}

try:
    jail({user_input!r})
except Exception as e:
    print(f"Error in jail execution: {{e}}")

"""
        cmd = ["python", "-c", script]
        output = self.container.exec_run(cmd, stream=False)
        return output

    def query_game(self) -> GameState:
        new_state = PyJailGame()
        new_state.docker_client = self.docker_client
        new_state.container = self.container
        new_state.flag = self.flag
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )
        
        msg = new_state.validate_game()
        new_state.context['message'] = msg if msg is not None else f"You will move as {new_state.roles[0]}"

        current_role = new_state.roles[0]

        if current_role == "DefenderGenerateCode":
            new_state.context['message'] += "\nImplement a PyJail by defining a 'jail(user_input)' function. Start and end your code with ###START and ###END. Example:\n###START\ndef jail(user_input):\n    # Your code here\n    pass\n###END"

        elif current_role == "DefenderSolveCode":
            new_state.context['message'] += "\noutput valid python syntax, starting and ending valid python with ###START, and ###END that will be the solution to the pyjail ctf challenge you generated"
        elif current_role == "AttackerSolveCode":
            new_state.context['message'] += "\noutput valid python syntax, starting and ending valid python with ###START, and ###END that will be the soltuion to a pyjail ctf challenge"
        return new_state

    def validate_game(self) -> Optional[str]:
        if self.roles[0] == "AttackerSolveCode" and not self.last_move_successful:
            return "DefenderWins"
        return self.context['message']

    def get_next_roles(self) -> List[str]:
        if not self.last_move_successful:
            return self.roles.copy()

        if self.roles[0] == "DefenderGenerateCode":
            return ['DefenderSolveCode', 'AttackerSolveCode', "DefenderGenerateCode"]
        elif self.roles[0] == "DefenderSolveCode":
            return ['AttackerSolveCode', "DefenderGenerateCode",'DefenderSolveCode']
        else:  
            return ['DefenderGenerateCode', 'DefenderSolveCode', 'AttackerSolveCode']  # Reset the game


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
                'defender_code': self.environment['defender_code'],
                'message': self.context['message'],
                'history': self.context['history']['defender_history']
            }
        elif current_role == "AttackerSolveCode":
            
            return {
                'role': current_role,
                'defender_code': self.environment['defender_code'],
                'message': self.context['message'],
                'history': self.context['history']['attacker_history']
            }
        else: 
            raise ValueError(f"Invalid role: {current_role}")

    def display(self) -> str:
        display_str = f"Current Role: {self.roles[0] if self.roles else 'Not set'}\n"
        display_str += f"Message: {self.context['message']}\n\n"
        
        display_str += "Environment:\n"
        display_str += f"  Defender Code: {'Set' if self.environment['defender_code'] else 'Not set'}\n"
        if self.environment['defender_code']:
            display_str += f"    {self.environment['defender_code']}\n"
        display_str += f"  Defender Solution: {'Set' if self.environment['defender_solution'] else 'Not set'}\n"
        if self.environment['defender_solution']:
            display_str += f"    {self.environment['defender_solution']}\n"
        display_str += f"  Attacker Solution: {'Set' if self.environment['attacker_solution'] else 'Not set'}\n"
        if self.environment['attacker_solution']:
            display_str += f"    {self.environment['attacker_solution']}\n"
        histname = 'defender' if not self.roles[0] == 'AttackerSolve' else 'attacker'
        display_str += "\nHistory:\n"
        for entry in self.context['history'][f"{histname}_history"][-5:]:  

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
        docker_client = docker.from_env()
        container_name = 'pyjail_container'
        try:
            container = docker_client.containers.get(container_name)
            print(f"Container '{container_name}' already exists.")
        except docker.errors.NotFound:
            print(f"Creating container '{container_name}'...")
            container = docker_client.containers.run(
                'python:3.9',
                name=container_name,
                detach=True,
                environment={'FLAG': secrets.token_hex(12)},
                command='tail -f /dev/null'  # Keep the container running
            )
        # Initialize the game
        game = PyJailGame()
        game.instantiate()
        print("Initial game state:")
        print(game.display())

        # Test Defender Generate Code
        defender_code = """
    ```python
    ###START
    def jail(user_input):
        eval(user_input)
    ###END
    ```
    """
        game = game.update_game(defender_code)
        print("\nAfter Defender Generate Code:")
        print(game.display())

        # Test Defender Solve Code (should fail)
        defender_solution = """
    ###START
    __import__('os').system('echo $FLAG')
    ###END
    """
        game = game.update_game(defender_solution)
        game = game.query_game()
        print(game.display())

        #defender wins
        attacker_solution = """
    ###START
    __import__('os').system('echo $NOPE')
    ###END
    """
        game = game.update_game(attacker_solution).query_game()
        print(game.display())

         
        print(game.validate_game())

        print("\nCleaning up...")
        container.stop()
        container.remove()
        docker_client.close()

    run_test()

