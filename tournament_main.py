import argparse
import yaml
from collections import defaultdict

from zero_sum_eval.managers import TournamentManager
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

    tournament_manager = TournamentManager(config)

    logger.info("Starting a new tournament.")

    final_elos = tournament_manager.start()


    logger.info(
        f"\Tournament over. Final elos: {final_elos}"
    )


if __name__ == "__main__":
    main()
