# file: chess_challenge.py
import chess
from zero_sum_eval.managers.game_manager import GameManager
from zero_sum_eval.games.chess.chess_game import ChessGame
from zero_sum_eval.player import Player


def main():

    # Configuration for chess challenges
    """
    A simple example for playing single move challenge boards with the goal of getting checkmate 
    Each game will end after one turn, but multiple environments can be run in a row 
    """

    # for now just define config here instead of loading from a file
    config = {
        "game": {
            "name": "chess_challenge",
            "args": {
                "win_conditions": ["Checkmate"],
                "max_rounds": 1,
                "players": [
                    {"role": "White", "max_tries": 3, "id": "player1"},
                    {"role": "Black", "max_tries": 3, "id": "player2"},
                ],
                "challenges": [
                    {
                        "environment": "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2"
                    },  # Black mates in 1 with Qh4#
                    # more environments can be added
                ],
            },
        }
    }

    game_manager = GameManager(config)

    for player_config in config["game"]["args"]["players"]:
        player = Player(config)
        game_manager.register_player(player)

        for challenge in config["game"]["args"]["challenges"]:
            environment = challenge["environment"]
            game_state = ChessGame().initialize(chess.Board(environment).fen())
            game_state = game_state.query_game()
            print(f"Starting challenge with environment: {environment}")

            game_state = game_manager.do_turn(game_state, player)

            print(game_state.validate_game())


if __name__ == "__main__":
    main()
