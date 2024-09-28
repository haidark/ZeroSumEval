import argparse
import time
import yaml
from collections import defaultdict

from zero_sum_eval.managers import GamePoolManager
from zero_sum_eval.logging_utils import setup_logging, cleanup_logging
import logging

logger = logging.getLogger(__name__)


def read_config(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return defaultdict(dict, config)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str)    
    args = parser.parse_args()

    config = read_config(args.config)

    # Set up logging with 'match_series' prefix
    handlers = setup_logging(config, 'match_series')

    try:
        while True:
            try:
                match_manager = GamePoolManager(config)
                logger.info("Starting a new match pool series!")
                wdl = match_manager.start()
                logger.info(f"Match pool series over. WDL: {wdl}")
            except Exception as e:
                print(e)
                print("Error in pool matches")
                print("Sleeping for 10 seconds then restarting")
                time.sleep(10)
                continue
            
    finally:
        # Clean up logging
        cleanup_logging(logger, handlers)


if __name__ == "__main__":
    main()