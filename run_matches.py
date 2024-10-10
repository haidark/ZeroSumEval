import argparse
from collections import defaultdict
from zero_sum_eval.config_utils import load_yaml_with_env_vars
from zero_sum_eval.managers import MatchManager
from zero_sum_eval.logging_utils import setup_logging, cleanup_logging
import logging

logger = logging.getLogger('ZeroSumEval')


def read_config(path):
    config = load_yaml_with_env_vars(path)
    return defaultdict(dict, config)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str)    
    args = parser.parse_args()

    config = read_config(args.config)

    # Set up logging with 'match_series' prefix
    handlers = setup_logging(config, 'match_series')

    try:
        match_manager = MatchManager(config)
        logger.info("Starting a new match series!")
        final_elos = match_manager.start()
        logger.info(f"Match series over. Final elos: {final_elos}")
    finally:
        # Clean up logging
        cleanup_logging(logger, handlers)


if __name__ == "__main__":
    main()