import pytest
import os
import tempfile

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