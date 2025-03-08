import pytest
from unittest.mock import MagicMock
from dspy import Prediction
from zero_sum_eval.utils.types import ActionConfig, Move

@pytest.fixture
def mock_prediction():
    """Mock dspy.Prediction for testing"""
    return Prediction({"output": "test"})

def test_action_config_basic():
    """Test basic ActionConfig creation and defaults"""
    config = ActionConfig(name="test_action")
    assert config.name == "test_action"
    assert all(getattr(config, field) is None for field in [
        "module_path", "dataset", "dataset_args", 
        "optimizer", "optimizer_args", "metric"
    ])
    assert config.optimize is False

def test_action_config_full():
    """Test ActionConfig with all fields specified"""
    test_config = {
        "name": "test_action",
        "module_path": "path/to/module",
        "optimize": True,
        "dataset": "test_dataset",
        "dataset_args": {"key": "value"},
        "optimizer": "test_optimizer",
        "optimizer_args": {"learning_rate": 0.01},
        "metric": "accuracy"
    }
    
    config = ActionConfig(**test_config)
    assert all(getattr(config, key) == value for key, value in test_config.items())

def test_move_basic():
    """Test basic Move creation"""
    move = Move(value="test_move", time=0.5)
    assert move.value == "test_move"
    assert move.time == 0.5
    assert move.trace is None

def test_move_with_trace(mock_prediction):
    """Test Move with trace"""
    move = Move(value="test_move", trace=mock_prediction, time=0.5)
    assert move.value == "test_move"
    assert move.trace == mock_prediction
    assert move.time == 0.5

def test_action_config_from_dict():
    """Test creating ActionConfig from dictionary"""
    config_dict = {
        "name": "test_action",
        "module_path": "path/to/module",
        "optimize": True,
        "dataset": "test_dataset",
        "dataset_args": {"key": "value"},
        "optimizer": "test_optimizer",
        "optimizer_args": {"learning_rate": 0.01},
        "metric": "accuracy"
    }
    
    config = ActionConfig(**config_dict)
    
    assert config.name == config_dict["name"]
    assert config.module_path == config_dict["module_path"]
    assert config.optimize == config_dict["optimize"]
    assert config.dataset == config_dict["dataset"]
    assert config.dataset_args == config_dict["dataset_args"]
    assert config.optimizer == config_dict["optimizer"]
    assert config.optimizer_args == config_dict["optimizer_args"]
    assert config.metric == config_dict["metric"]

def test_action_config_partial_dict():
    """Test creating ActionConfig from partial dictionary"""
    config_dict = {
        "name": "test_action",
        "optimize": True,
        "dataset": "test_dataset"
    }
    
    config = ActionConfig(**config_dict)
    
    assert config.name == config_dict["name"]
    assert config.optimize == config_dict["optimize"]
    assert config.dataset == config_dict["dataset"]
    assert config.module_path is None
    assert config.dataset_args is None
    assert config.optimizer is None
    assert config.optimizer_args is None
    assert config.metric is None

def test_action_config_equality():
    """Test ActionConfig equality comparison"""
    config1 = ActionConfig(name="test", optimize=True)
    config2 = ActionConfig(name="test", optimize=True)
    config3 = ActionConfig(name="different", optimize=True)
    
    assert config1 == config2
    assert config1 != config3

def test_move_equality():
    """Test Move equality comparison"""
    move1 = Move(value="test", time=0.5)
    move2 = Move(value="test", time=0.5)
    move3 = Move(value="different", time=0.5)
    
    assert move1 == move2
    assert move1 != move3
    assert move2 != move3 