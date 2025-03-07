import argparse
import json
import logging

from collections import defaultdict
import os

import yaml

from zero_sum_eval.calculate_ratings import calculate_ratings
from zero_sum_eval.managers.game_pool_manager import GamePoolManager
from zero_sum_eval.registry import GAME_REGISTRY
from zero_sum_eval.logging_utils import cleanup_logging, setup_logging
from zero_sum_eval.config_utils import load_yaml_with_env_vars
from zero_sum_eval.managers import GameManager

logger = logging.getLogger(__name__)

def setup_parser() -> argparse.ArgumentParser:
    """
    Set up and return the command-line argument parser.
    
    The script supports three main modes of operation:
    1. Single game mode: Run a single game between specified players
    2. Pool mode: Run multiple games between different models
    3. ELO calculation mode: Calculate ELO ratings from existing game logs
    
    Returns:
        argparse.ArgumentParser: The configured argument parser
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="""\
This script supports three modes of operation:
1. Single game mode: Run a single game between specified players
   Example: zseval --game chess --players "white=openai/gpt-4o" "black=anthropic/claude-3-opus"
   
2. Pool mode: Run multiple games between different models and optionally calculate ELOs at the end
   Example: zseval --game chess --pool --models "openai/gpt-4o" "anthropic/claude-3-opus" --max_matches 10

   
3. ELO calculation mode: Calculate ELO ratings from existing game logs without running any games
   Example: zseval --calculate_ratings --output_dir ./zse_outputs/chess_pool
"""
    )
    parser.add_argument("-c", "--config", type=str, default=None, help="Optional path to a YAML config file. This overwrites other arguments if passed.")
    parser.add_argument("-g", "--game", type=str, default=None, help="The game to play (e.g., chess, debate, etc.)")
    parser.add_argument("-o", "--output_dir", type=str, default='./zse_outputs', help="Output directory for logs and results.")

    parser.add_argument("-p", "--players", type=str, nargs="+", help='List of models to evaluate and their roles. (LiteLLM model names, for example, "white=openai/gpt-4o" or "black=openrouter/meta-llama/llama-3.3-70b-instruct")')
    parser.add_argument("--game_kwargs", type=str, nargs="+", default="", help="Arguments to pass to the game constructor as a string. For example, 'rebuttal_rounds=2', 'topics=topics.txt' for the debate game.")
    parser.add_argument("--max_rounds", type=int, default=100, help="Maximum number of rounds to play.")
    parser.add_argument("--max_player_attempts", type=int, default=5, help="Maximum number of attempts to generate a valid player move.")
    
    # Pool mode arguments
    parser.add_argument("--pool", action="store_true", help="Run a pool of matches instead of a single game.")
    parser.add_argument("-m", "--models", type=str, nargs="+", help="List of models to evaluate. (Only for pool mode)")
    parser.add_argument("--max_matches", type=int, default=10, help="Maximum number of matches to play. (Only for pool mode)")

    # Calculate ELOs arguments
    parser.add_argument("--calculate_ratings", action="store_true", help="Calculate ratings for the models.")
    parser.add_argument("--bootstrap_rounds", type=int, default=100, help="Number of bootstrap rounds to calculate ELOs.")

    # TODO: Add Player arguments. It only works with the default players for now.
    return parser

def read_config(path):
    config = load_yaml_with_env_vars(path)
    return defaultdict(dict, config)

def config_from_args(args):
    if args.pool:
        config = {
            "game": {"name": args.game, "args": {"players": {}}},
            "manager": {
                "max_matches": args.max_matches,
                "max_rounds_per_match": args.max_rounds,
                "max_player_attempts": args.max_player_attempts,
                "output_dir": args.output_dir,
            },
            "llms": [
                {"name": model.split('/')[-1], "model": model} for model in args.models
            ]
        }
    else:
        game_args = dict([arg.split("=") for arg in args.game_kwargs])
        config = {
            "game": {"name": args.game, "args": {"players": {}, **game_args}},
            "manager": {
                "max_player_attempts": args.max_player_attempts,
                "max_rounds": args.max_rounds,
                "output_dir": args.output_dir,
            },
        }
        role_model_pairs = [model.split("=") for model in args.players]
        for role, model in role_model_pairs:
            config["game"]["args"]["players"][role] = {
                "args": {
                    "id": f"{role}_{model.split('/')[-1]}",
                    "lm": {"model": model},
                }
            }
    return config

def run_single_game(config):
    game_name = config.get("game", {})["name"]
    game_args = config.get("game", {}).get("args", {})
    # Set up logging with 'game' prefix
    handlers = setup_logging('game', output_dir=config["manager"]["output_dir"])

    try:
        game = GAME_REGISTRY.build(game_name, **game_args)
        game_manager = GameManager(
            max_rounds=config["manager"]["max_rounds"], 
            max_player_attempts=config["manager"]["max_player_attempts"], 
            output_dir=config["manager"]["output_dir"]
        )
        logger.info("Starting a new game")
        final_state = game_manager.start(game)
        logger.info(
            f"\nGame over. Final state:\n{final_state['game_state'].display()}"
        )
    finally:
        # Clean up logging
        cleanup_logging(logger, handlers)

def run_pool_matches(config):
    # Set up logging with 'match_series' prefix
    handlers = setup_logging(config["game"]["name"], 'match_series')

    match_manager = GamePoolManager(
        **config["manager"],
        game=config["game"]["name"],
        game_args=config["game"]["args"],
        llm_configs=config["llms"],
    )
    logger.info("Starting a new match pool series!")
    wdl = match_manager.start()
    logger.info(f"Match pool series over. WDL: {wdl}")
    # Clean up logging
    cleanup_logging(logger, handlers)

def cli_run():
    parser = setup_parser()
    args = parser.parse_args()

    if args.config:
        config = read_config(args.config)
        if config["config_type"] == "pool":
            args.pool = True
        elif "llms" in config and not args.pool:
            raise ValueError("'llms' key is specified in the config but --pool is not set. Add the --pool flag or set the config_type to 'pool' when using a pool config file.")

    if args.game is None and not args.calculate_ratings and not args.config:
        parser.print_help()
        return

    # If we are running a single game, we need to specify players
    if args.game and not args.pool and not args.calculate_ratings and args.players is None:
        raise ValueError("Must specify players when running a single game.")
    
    # Determine if we are running any games
    is_running_games = args.pool or args.game

    # If we are not running any games and calculate_elos is True, we need to only calculate ELOs without running any games from the output directory
    if not is_running_games and args.calculate_ratings and args.output_dir:
        ratings = calculate_ratings(
            logs_path=args.output_dir,
            bootstrap_rounds=args.bootstrap_rounds,
            max_player_attempts=args.max_player_attempts
        )
        print(ratings)
        return

    if args.output_dir is None:
        args.output_dir = f"zse_outputs/{args.game}"
        if args.pool:
            args.output_dir += "_pool"

    # If no config is provided, we need to create one from the arguments
    if not args.config:
        config = config_from_args(args)

    print(f"Running {args.game or config.get('game', {}).get('name', None)} with config:\n{json.dumps(config, indent=2)}")

    # Save the config to the output directory
    os.makedirs(config["manager"]["output_dir"], exist_ok=True)
    with open(os.path.join(config["manager"]["output_dir"], "pool_config.yaml"), "w") as f:
        yaml.dump(dict(config), f)

    # Run matches if pool mode is enabled
    if args.pool:
        run_pool_matches(config)

    # Calculate ELO ratings if requested
    if args.calculate_ratings:
        ratings = calculate_ratings(
            logs_path=args.output_dir,
            bootstrap_rounds=args.bootstrap_rounds,
            max_player_attempts=args.max_player_attempts
        )
        print(ratings)
    # Run single game if no other modes specified
    elif not args.pool and not args.calculate_ratings:
        run_single_game(config)
    

if __name__ == "__main__":
    cli_run()
