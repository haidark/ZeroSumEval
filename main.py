import argparse
import yaml
from collections import defaultdict

from zero_sum_eval.game_manager import GameManager

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO) 


def read_config(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return defaultdict(dict, config)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str)

    args = parser.parse_args()

    config = read_config(args.config)

    game_manager = GameManager(config)

    logger.info("Starting a new game of chess.")

    final_state = game_manager.start()

    logger.info(
        f"\nGame over. Final state: {final_state.validate_game()}\n{final_state.display()}"
    )


if __name__ == "__main__":
    main()
