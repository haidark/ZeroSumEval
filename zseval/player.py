#file: player.py
'''
example of how an llm player might be structured. This has not been tested yet
'''

import openai
import yaml

class Player:
    def __init__(self, config):
        self.id = config['id']
        self.role = config['role']
        self.llm_model = config.get('llm_model')
        self.dspy_module = config.get('dspy_module')
        self.context = {}
        self.api_key = config.get('api_key')
        self.max_tries = config.get('max_tries', 1)  # Default to 1 if not provided

        if self.api_key:
            openai.api_key = self.api_key

    def initialize(self, role, llm_model, dspy_module, api_key, max_tries=1):
        self.role = role
        self.llm_model = llm_model
        self.dspy_module = dspy_module
        self.api_key = api_key
        self.max_tries = max_tries

        if self.api_key:
            openai.api_key = self.api_key

    def make_move(self, game_state):
        # Prepare the prompt for the OpenAI API based on game_state
        prompt = self.create_prompt(game_state)
        
        # Call the OpenAI API to generate a move
        response = openai.Completion.create(
            engine=self.llm_model,
            prompt=prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        # Extract the move from the response
        move = response.choices[0].text.strip()
        return move

    def create_prompt(self, game_state):
        return f"{game_state.export()}"

class Role:
    def __init__(self, role_name, permissions):
        self.roleName = role_name
        self.permissions = permissions

    def initialize(self, game_state):
        # Logic to initialize role-specific state
        pass


'''import dspy

class Player:
    def __init__(self, config):
        self.id = config['id']
        self.role = config['role']
        self.llm_model = config['llm_model']
        self.dspy_module = config['dspy_module']
        self.context = {}

    def initialize(self, role, llm_model, dspy_module):
        self.role = role
        self.llm_model = llm_model
        self.dspy_module = dspy_module

    def make_move(self, game_state):
        # Use dspy module to generate a move
        module = getattr(dspy, self.dspy_module)
        move = module.generate_move(game_state, self.llm_model)
        return move

class Role:
    def __init__(self, role_name, permissions):
        self.roleName = role_name
        self.permissions = permissions

    def initialize(self, game_state):
        # Logic to initialize role-specific state
        pass

# Example usage with configuration
if __name__ == "__main__":
    config = {
        'id': 'gpt3.5_white',
        'role': 'White',
        'llm_model': 'path/to/llm_model',
        'dspy_module': 'CoT'
    }
    player = Player(config)
    # Assuming a game_state object is available
    move = player.make_move(game_state)
    print(f"Player {player.id} made move: {move}")
'''
