import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Any
from dataclasses import dataclass

from zero_sum_eval.core.registry import (
    Registry, GAME_REGISTRY, PLAYER_REGISTRY, 
    DATASET_REGISTRY, METRIC_REGISTRY
)
from zero_sum_eval.core.game_state import GameState
from zero_sum_eval.utils.types import Dataset
from zero_sum_eval.core.player import Player

# Test fixtures and base classes
@pytest.fixture
def mock_base_class():
    """Create a base class for testing registries"""
    return type('MockBase', (), {'__module__': 'test'})

@dataclass
class MockPlayerDef:
    """Mock player definition for testing"""
    player_key: str
    actions: List[str]
    default_player_class: type

# Base test classes with minimal implementations
class TestGameState(GameState):
    """Minimal GameState implementation for testing"""
    def __init__(self):
        self._is_over = False
        self._scores = {"player1": 0, "player2": 0}
    
    def get_valid_moves(self) -> List[str]: return []
    def get_next_action(self) -> str: return "test_action"
    def get_scores(self) -> Dict[str, float]: return self._scores
    def is_over(self) -> bool: return self._is_over
    def player_definitions(self) -> List[MockPlayerDef]:
        return [
            MockPlayerDef(player_key="player1", actions=[], default_player_class=Player),
            MockPlayerDef(player_key="player2", actions=[], default_player_class=Player)
        ]
    def player_inputs(self) -> Dict[str, Any]: return {}

class TestDataset(Dataset):
    """Minimal Dataset implementation for testing"""
    def __init__(self):
        super().__init__(output_key="output")
    def get_dataset(self): return []

def test_basic_registry(mock_base_class):
    """Test basic Registry functionality"""
    registry = Registry("test_registry", mock_base_class)
    
    @registry.register("test_item")
    class TestClass(mock_base_class):
        pass
    
    # Test registration and lookup
    assert "test_item" in registry
    assert "TestClass" in registry
    
    # Test case insensitivity
    assert "TEST_ITEM" in registry
    
    # Test building
    instance = registry.build("test_item")
    assert isinstance(instance, mock_base_class)
    
    # Test error cases
    with pytest.raises(ValueError):
        registry.build("nonexistent_item")
    
    with pytest.raises(AssertionError):
        @registry.register()
        class InvalidClass:
            pass

def test_metric_registry():
    """Test MetricRegistry functionality"""
    @METRIC_REGISTRY.register("test_metric")
    def test_metric(pred, gt): return pred == gt
    
    # Test registration and building
    assert "test_metric" in METRIC_REGISTRY
    metric = METRIC_REGISTRY.build("test_metric", output_key="output")
    assert callable(metric)
    
    # Test error on non-callable
    with pytest.raises(AssertionError):
        METRIC_REGISTRY.register("invalid")(None)

def test_dataset_registry():
    """Test Dataset registry functionality"""
    @DATASET_REGISTRY.register("test_dataset")
    class TestDatasetImpl(TestDataset):
        pass
    
    # Test registration and building
    assert "test_dataset" in DATASET_REGISTRY
    dataset = DATASET_REGISTRY.build("test_dataset")
    assert isinstance(dataset, Dataset)
    
    # Test error on unregistered dataset
    with pytest.raises(ValueError):
        DATASET_REGISTRY.build("nonexistent_dataset")

def test_player_registry():
    """Test PlayerRegistry functionality"""
    # Register test game and player
    @GAME_REGISTRY.register("test_game")
    class TestGame(TestGameState):
        pass
    
    @PLAYER_REGISTRY.register("test_game", "test_player")
    class TestGamePlayer(Player):
        def init_actions(self): return {}
    
    # Test registration
    assert "test_game" in PLAYER_REGISTRY
    
    # Test building player
    player = PLAYER_REGISTRY.build(
        "test_game",
        "test_player",
        id="test",
        actions=[],
        lm={"model": "test"},
        player_key="test"
    )
    assert isinstance(player, Player)
    
    # Test error cases
    with pytest.raises(AssertionError):
        PLAYER_REGISTRY.build("nonexistent_game", "test_player")
    with pytest.raises(AssertionError):
        PLAYER_REGISTRY.build("test_game", "nonexistent_player")

def test_registry_case_insensitivity(mock_base_class):
    """Test registry case insensitivity"""
    registry = Registry("test_registry", mock_base_class)
    
    @registry.register("Test_Item")
    class TestClass(mock_base_class):
        pass
    
    variants = ["test_item", "TEST_ITEM", "Test_Item"]
    assert all(variant in registry for variant in variants)
    assert all(isinstance(registry.build(variant), mock_base_class) 
              for variant in variants)

def test_registry_duplicate_registration(mock_base_class):
    """Test handling of duplicate registrations"""
    registry = Registry("test_registry", mock_base_class)
    
    @registry.register("test_item")
    class TestClass1(mock_base_class):
        pass
    
    @registry.register("test_item")
    class TestClass2(mock_base_class):
        pass
    
    instance = registry.build("test_item")
    assert isinstance(instance, TestClass2) 