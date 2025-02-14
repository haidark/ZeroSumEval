import os
import logging
import pytest
from zero_sum_eval.logging_utils import setup_logging, cleanup_logging, DEFAULT_OUTPUT_DIR

@pytest.fixture
def test_output_dir():
    return './test_logs'

@pytest.fixture
def cleanup_test_logs():
    # Setup
    yield
    # Teardown
    test_dir = './test_logs/logs'
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, file))
        os.rmdir(test_dir)
        os.rmdir('./test_logs')

def test_setup_logging(test_output_dir, cleanup_test_logs):
    # Setup logging
    handlers = setup_logging(output_dir=test_output_dir, prefix='test')
    logger = logging.getLogger()
    
    # Test that all expected handlers are created
    expected_handlers = ['file_debug', 'file_info', 'file_warning', 'file_error', 'stream']
    assert all(handler in handlers for handler in expected_handlers)
    
    # Test log file creation and writing
    test_message = "Test log message"
    logger.info(test_message)
    
    # Get process ID for log file names
    pid = os.getpid()
    
    # Check if log files were created and contain the message
    log_file = os.path.join('./test_logs/logs', f'test_info_{pid}.log')
    assert os.path.exists(log_file)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert test_message in content
    
    # Cleanup
    cleanup_logging(logger, handlers)

def test_cleanup_logging(test_output_dir, cleanup_test_logs):
    # Setup logging
    handlers = setup_logging(output_dir=test_output_dir, prefix='test')
    logger = logging.getLogger()
    
    # Test cleanup
    cleanup_logging(logger, handlers)
    
    # Verify all handlers are closed and removed
    for handler in handlers.values():
        assert handler not in logger.handlers
        if hasattr(handler, '_closed'):
            assert handler._closed

def test_log_levels(test_output_dir, cleanup_test_logs):
    # Setup logging
    handlers = setup_logging(output_dir=test_output_dir, prefix='test')
    logger = logging.getLogger()
    
    # Test messages at different levels
    debug_msg = "Debug message"
    info_msg = "Info message"
    warning_msg = "Warning message"
    error_msg = "Error message"
    
    logger.debug(debug_msg)
    logger.info(info_msg)
    logger.warning(warning_msg)
    logger.error(error_msg)
    
    # Get process ID for log file names
    pid = os.getpid()
    
    # Verify debug log contains all messages
    debug_file = os.path.join('./test_logs/logs', f'test_debug_{pid}.log')
    with open(debug_file, 'r') as f:
        content = f.read()
        assert all(msg in content for msg in [debug_msg, info_msg, warning_msg, error_msg])
    
    # Verify info log doesn't contain debug messages
    info_file = os.path.join('./test_logs/logs', f'test_info_{pid}.log')
    with open(info_file, 'r') as f:
        content = f.read()
        assert debug_msg not in content
        assert all(msg in content for msg in [info_msg, warning_msg, error_msg])
    
    # Cleanup
    cleanup_logging(logger, handlers)

def test_custom_output_directory():
    # Test with no output directory specified
    handlers = setup_logging(prefix='test')
    logger = logging.getLogger()
    
    # Verify default directory is used
    assert os.path.exists(f'{DEFAULT_OUTPUT_DIR}/logs')
    
    # Cleanup
    cleanup_logging(logger, handlers)
    
    # Remove test directory
    for file in os.listdir(f'{DEFAULT_OUTPUT_DIR}/logs'):
        os.remove(os.path.join(f'{DEFAULT_OUTPUT_DIR}/logs', file))
    os.rmdir(f'{DEFAULT_OUTPUT_DIR}/logs')
