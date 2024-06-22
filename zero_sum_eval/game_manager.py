#file: game_manager.py
#TODO: ADD SUPPORT FOR MULTIPLE KINDS OF PLAYERS
from game_state import GameState

class GameManager:
    def __init__(self, config):
        self.config = config
        self.games = []
        self.players = {}
        self.max_rounds = config['game']['args']['max_rounds']

    def initialize_game(self, game_class):
        environment = self.config['game']['args'].get('environment', None)
        game = game_class().initialize(environment)
        self.roles = game.query_game()  
        self.games.append(game)
        return game

    def do_eval(self, game_state):
        round_count = 0
        while round_count < self.max_rounds:
            game_status = game_state
            if game_status.validate_game():
                break
            game_status = game_state.query_game()
            player = self.players[game_status.roles[0]]
            game_state = self.do_turn(game_status, player)
            round_count += 1
        return game_state

    def do_turn(self, game_state, player):
        new_state = game_state
        for _ in range(player.max_tries):
            move = player.make_move(new_state)
            new_state = new_state.update_game(move)
            val = new_state.validate_game()
            if val is None:
                return new_state
            if val in self.config['game']['args']['win_conditions']:
                #
                # Here maybe call the scoring function?
                #
                return new_state.query_game()
            else:
                print(f"Player {player.id} made an invalid move: {move}")
        
        print(f"Player {player.id} failed to make a valid move after {player.max_tries} tries.")
        
        return game_state  # Return the original state if all tries fail


    def register_player(self, player):
        self.players[player.role] = player


