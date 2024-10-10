import os
import logging

def setup_logging(config, log_prefix):
    logger = logging.getLogger('ZeroSumEval')
    logger.setLevel(logging.DEBUG)  # Set to lowest level to capture all logs
    logging.getLogger('LiteLLM').setLevel(logging.ERROR)
    logging.getLogger('httpcore').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('openai').setLevel(logging.ERROR)
    output_dir = os.path.join(config['logging'].get('output_dir', './'), "logs")
    os.makedirs(output_dir, exist_ok=True)
    
    log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }

    handlers = {}
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    for level_name, level in log_levels.items():
        # File handler
        log_file = os.path.join(output_dir, f'{log_prefix}_{level_name}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        handlers[f'file_{level_name}'] = file_handler

        # Stream handler for info, warning, and error levels
        if level_name in ['info', 'warning', 'error']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            handlers[f'stream_{level_name}'] = stream_handler

    return handlers

def cleanup_logging(logger, handlers):
    for handler in handlers.values():
        logger.removeHandler(handler)
        handler.close()