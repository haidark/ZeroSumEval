import chess
import dspy
import os
import openai

from game_manager import GameManager
from games.chess import ChessGame, ChessPlayer

import logging

GAMES = {
    "chess": {
        "class!": ChessGame,
        "chess player": {
            "class!": ChessPlayer,
        }
    }
}



def main():
    openai.api_type = "azure"
    openai.api_base = "https://allam-swn-gpt-01.openai.azure.com/"
    openai.api_version = "2023-07-01-preview"  
    api_key = os.getenv("OPENAI_API_KEY")

    # Set up the LM
    player1_gpt4 = dspy.AzureOpenAI(
        api_base=openai.api_base,
        api_version=openai.api_version,
        api_key=api_key,
        deployment_id='gpt-4-900ptu',  # "gpt-35-haidar",
        max_tokens=800,
        temperature=0.8,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )

    player2_gpt4 = dspy.AzureOpenAI(
        api_base=openai.api_base,
        api_version=openai.api_version,
        api_key=api_key,
        deployment_id='gpt-4-900ptu',  # "gpt-35-haidar",
        max_tokens=800,
        temperature=0.8,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )

    # Configuration to play a full chess game, for now just store here
    config = {
        'game': {
            'name': "chess",
            'args': {
                'max_rounds': 200,  # enough rounds for a full game
                'win_conditions': 'Checkmate',  # Max rounds for a full game
                'players': [
                    {'name': "chess player", 
                     'args':{'role': 'White', 'max_tries': 40, 'id': 'Player1', "llm_model": player1_gpt4, "optimize": True}},
                    {'name': "chess player", 
                     'args':{'role': 'Black', 'max_tries': 40, 'id': 'Player2', "llm_model": player2_gpt4, "optimize": False}}
                ]
            }
        }
    }
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)    # Initialize the GameManager
    game_manager = GameManager(config)
    # Register players
    for player_args in config['game']['args']['players']:
        player = GAMES[config['game']['name']][player_args['name']]['class!'](**player_args['args'])
        game_manager.register_player(player)

    game_state = GAMES[config['game']['name']]['class!']().initialize(chess.Board().fen())
    logger.info("Starting a new game of chess.")
    final_state = game_manager.do_eval(game_state)
    logger.info(f"\nGame over. Final state: {final_state.validate_game()}\n{final_state.display()}")

if __name__ == "__main__":
    main()