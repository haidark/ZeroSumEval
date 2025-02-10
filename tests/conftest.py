import pytest
import os
import tempfile
import logging

@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_module():
    class DummyModule:
        def save(self, path):
            pass
        def load(self, path):
            pass
    return DummyModule()

@pytest.fixture
def cleanup_logging():
    """Fixture to save and restore logging state around tests."""
    # Save original logging state
    original_handlers = logging.getLogger().handlers.copy()
    original_level = logging.getLogger().level
    
    yield
    
    # Restore original logging state
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    for handler in original_handlers:
        logger.addHandler(handler)
    logger.setLevel(original_level) 