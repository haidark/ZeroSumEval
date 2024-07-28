import argparse
import yaml
from collections import defaultdict

from zero_sum_eval.managers import MatchManager
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
    #TODO: add optional match series history datafile
    
    args = parser.parse_args()

    config = read_config(args.config)

    match_manager = MatchManager(config)

    logger.info("Starting a new match series!")

    final_elos = match_manager.start()


    logger.info(
        f"\Match series over. Final elos: {final_elos}"
    )


if __name__ == "__main__":
    main()
