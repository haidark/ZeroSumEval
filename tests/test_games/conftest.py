import pytest
from unittest.mock import MagicMock, patch
import dspy
from dspy import Prediction

@pytest.fixture(autouse=True)
def mock_dspy():
    """Common mock setup for dspy components used across game tests."""
    # Create mock classes/types
    mock_module_type = type('Module', (), {})
    mock_parameter_type = type('Parameter', (), {})
    mock_predict_type = type('Predict', (), {})
    mock_retry_type = type('Retry', (), {})

    with patch('dspy.Module', mock_module_type), \
         patch('dspy.Module', return_value=MagicMock()), \
         patch('dspy.ChainOfThought', return_value=MagicMock()), \
         patch('dspy.Signature', return_value=MagicMock()), \
         patch('dspy.InputField', return_value=MagicMock()), \
         patch('dspy.OutputField', return_value=MagicMock()), \
         patch('dspy.LM', return_value=MagicMock()), \
         patch('dspy.predict.predict.Parameter', mock_parameter_type), \
         patch('dspy.Predict', mock_predict_type), \
         patch('dspy.retry.Retry', mock_retry_type):
        
        # Mock dspy.Module type checking
        dspy.Module = mock_module_type
        
        yield {
            'module_type': mock_module_type,
            'parameter_type': mock_parameter_type,
            'predict_type': mock_predict_type,
            'retry_type': mock_retry_type
        }

@pytest.fixture
def mock_move():
    """Common mock move with trace for testing."""
    class MockMove:
        def __init__(self, value="test value"):
            self.value = value
            self.trace = type('obj', (object,), {'toDict': lambda self: {}})()
    return MockMove

@pytest.fixture
def base_player_config():
    """Base player configuration that can be extended for specific games."""
    def make_config(player_id, player_type, actions):
        return {
            "type": player_type,
            "args": {
                "id": player_id,
                "lm": {"model": "gpt-4"},
                "actions": [{"name": action} for action in actions]
            }
        }
    return make_config 