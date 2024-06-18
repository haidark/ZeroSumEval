#file main.py
import chess
from game_manager import GameManager
from chess_game import ChessGame
from human_player import Player

def main():
    # Configuration to play a full chess game, for now just store here
    config = {
        'game': {
            'args': {
                'max_rounds': 100,  # enough rounds for a full game
                'win_conditions': 'Checkmate',  # Max rounds for a full game
                'players': [
                     {'role': 'White', 'max_tries': 4, 'id': 'Player1'},
                    {'role': 'Black', 'max_tries': 4, 'id': 'Player2'}
                ]
            }
        }
    }

    # Initialize the GameManager
    game_manager = GameManager(config)

    # Register players
    for player_args in config['game']['args']['players']:
        player = Player(player_args)
        game_manager.register_player(player)

    game_state = ChessGame().initialize(chess.Board().fen())
    print("Starting a new game of chess.")
    final_state = game_manager.do_eval(game_state)
    print(f"\nGame over. Final state: {final_state.validate_game()}\n {final_state.export()}")

if __name__ == "__main__":
    main()
