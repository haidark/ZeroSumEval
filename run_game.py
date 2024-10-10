import argparse
from collections import defaultdict
from zero_sum_eval.config_utils import load_yaml_with_env_vars
from zero_sum_eval.managers.game_manager import GameManager
from zero_sum_eval.logging_utils import setup_logging, cleanup_logging
import logging

logger = logging.getLogger(__name__)


def read_config(path):
    config = load_yaml_with_env_vars(path)
    return defaultdict(dict, config)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str)

    args = parser.parse_args()

    config = read_config(args.config)

    # Set up logging with 'game' prefix
    handlers = setup_logging(config, 'game')

    try:
        game_manager = GameManager(config)
        logger.info("Starting a new game")
        final_state = game_manager.start()
        logger.info(
            f"\nGame over. Final state: {final_state.validate_game()}\n{final_state.display()}"
        )
    finally:
        # Clean up logging
        cleanup_logging(logger, handlers)


if __name__ == "__main__":
    main()