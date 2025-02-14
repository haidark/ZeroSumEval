import os
import logging
import tempfile
from pathlib import Path

def setup_logging(output_dir, prefix):
    """Set up logging with the given configuration."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Get output directory, default to temp dir if not specified
    if not output_dir:
        output_dir = "zse_outputs"
    
    # Create logs directory
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Add process ID to log filenames for uniqueness
    pid = os.getpid()
    handlers = {}
    
    # File handlers for different log levels
    handler_configs = {
        'file_debug': (logging.DEBUG, f'{prefix}_debug_{pid}.log'),
        'file_info': (logging.INFO, f'{prefix}_info_{pid}.log'),
        'file_warning': (logging.WARNING, f'{prefix}_warning_{pid}.log'),
        'file_error': (logging.ERROR, f'{prefix}_error_{pid}.log')
    }
    
    for name, (level, filename) in handler_configs.items():
        handler = logging.FileHandler(os.path.join(logs_dir, filename))
        handler.setLevel(level)
        handler.name = name
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        handlers[name] = handler
    
    # Stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.name = 'stream'
    stream_formatter = logging.Formatter('%(levelname)s     %(name)s:%(filename)s:%(lineno)d %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)
    handlers['stream'] = stream_handler
    
    return handlers

def cleanup_logging(logger, handlers):
    """Clean up logging handlers."""
    for handler in handlers.values():
        handler.close()
        if handler in logger.handlers:
            logger.removeHandler(handler)