import os
import openai
import dspy
from games.chess import ChessPlayer, ChessManager

if __name__ == "__main__":
    openai.api_type = "azure"
    openai.api_base = "https://allam-swn-gpt-01.openai.azure.com/" # "https://allam-arabic-data-cleaning.openai.azure.com/"  # "https://gpt4rnd.openai.azure.com/"
    openai.api_version = "2023-07-01-preview"  # "2023-07-01-preview"
    api_key = os.getenv("OPENAI_API_KEY")
    api_key2 = os.getenv("OPENAI_API_KEY2")

    # Set up the LM
    white_gpt4 = dspy.AzureOpenAI(
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

    black_gpt4 = dspy.AzureOpenAI(
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

    # initialize the players
    white_player = ChessPlayer("white", white_gpt4)
    black_player = ChessPlayer("black", black_gpt4)

    # initialize the game and run the game
    manager = ChessManager(players=[white_player, black_player], max_turns=3, win_conditions=True)
    manager.run_game()