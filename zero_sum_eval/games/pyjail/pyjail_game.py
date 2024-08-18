from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY
from typing import Dict, List, Optional
import subprocess
import docker

@GAME_REGISTRY.register("pyjail")
class PyjailGame(GameState):
    """
    This is a two-player game where one player (Defender) creates a Python jail,
    and the other player (Attacker) tries to break out of it.

    The roles for this game are:
        Defender
        Attacker

    The environment for this game is:
        challenge: the pyjail challenge code
        flag: the flag to be extracted (only known to Defender)
        max_attempts: maximum number of attempts allowed for the Attacker
    """

    def instantiate(self, environment: Dict, context: Dict, roles: List[str], **kwargs) -> None:
        self.environment = environment if environment else {
            "challenge": kwargs.get('challenge', ""),
            "flag": kwargs.get('flag', "flag{dummy_flag}"),
            "max_attempts": kwargs.get('max_attempts', 3)
        }
        self.context = context if context else {"attempts": 0, "message": None}
        self.roles = roles if roles else self.get_next_roles()
        self.setup_docker_container()

    def setup_docker_container(self):
        try:
            client = docker.from_env()
            self.container = client.containers.run(
                "pyjail-challenge",  # This should be the name of your pre-built Docker image
                detach=True,
                remove=True,
                command="tail -f /dev/null"  # Keep the container running
            )
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Failed to set up Docker container: {str(e)}")

    def update_game(self, move: str) -> GameState:
        new_state = PyjailGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )
        current_role = new_state.roles[0]
        if current_role == "Defender":
            new_state.environment['challenge'] = move
            new_state.roles = new_state.get_next_roles()
        elif current_role == "Attacker":
            new_state.context['attempts'] += 1
            result = self.execute_attack(move)
            if self.environment['flag'] in result:
                new_state.context['message'] = "Flag extracted successfully!"
            else:
                new_state.context['message'] = f"Attempt failed. Output: {result}"
            if new_state.context['attempts'] >= new_state.environment['max_attempts']:
                new_state.roles = []  # End the game if max attempts reached
            else:
                new_state.roles = new_state.get_next_roles()
        return new_state

    def query_game(self) -> GameState:
        new_state = PyjailGame()
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy()
        )
        
        msg = new_state.validate_game()
        new_state.context['message'] = msg if msg else f"You will move as {new_state.roles[0]}"
        return new_state

    def validate_game(self) -> Optional[str]:
        if not self.roles:
            return "GameOver"
        if self.environment['flag'] in self.context.get('message', ''):
            return "AttackerWon"
        if self.context['attempts'] >= self.environment['max_attempts']:
            return "DefenderWon"
        return None

    def get_next_roles(self) -> List[str]:
        if not self.environment['challenge']:
            return ['Defender', 'Attacker']
        return ['Attacker', 'Defender']

    def player_inputs(self) -> Dict[str, str]:
        current_role = self.roles[0]
        if current_role == "Defender":
            return {
                'role': current_role,
                'message': self.context['message'],
                'flag': self.environment['flag']
            }
        elif current_role == "Attacker":
            return {
                'role': current_role,
                'message': self.context['message'],
                'challenge': self.environment['challenge'],
                'attempts': self.context['attempts'],
                'max_attempts': self.environment['max_attempts']
            }
        else:
            raise ValueError(f"Invalid role: {current_role}")

    def execute_attack(self, attack_code: str) -> str:
        try:
            process = subprocess.Popen(
                ['docker', 'exec', self.container.id, 'python', '-c', self.environment['challenge']],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=attack_code, timeout=5)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            return "Execution timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    def display(self) -> str:
        display_str = f"Role to Act: {self.roles[0]}\n"
        display_str += f"Message: {self.context['message']}\n"
        display_str += f"Attempts: {self.context['attempts']}/{self.environment['max_attempts']}\n"
        if self.roles[0] == "Attacker":
            display_str += f"Challenge:\n{self.environment['challenge']}\n"
        return display_str

if __name__ == "__main__":
    pyjail_game = PyjailGame()
    pyjail_game.instantiate(None, None, None, challenge="print(input('Enter code: '))")
    print(pyjail_game.export())

    # Defender sets the challenge
    pyjail_game = pyjail_game.update_game("import sys\nuser_input = input('Enter code: ')\nif 'flag' in user_input:\n    print('Nice try!')\nelse:\n    exec(user_input)")
    print(pyjail_game.export())

    # Attacker attempts to break out
    print(pyjail_game.query_game().export())
    pyjail_game = pyjail_game.update_game("print(open('/flag.txt').read())")
    print(pyjail_game.export())

    validation_result = pyjail_game.validate_game()
    if validation_result:
        print(f"Game validation result: {validation_result}")
    else:
        print("Game is ongoing.")