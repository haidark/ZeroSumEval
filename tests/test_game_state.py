import pytest
import time
from unittest.mock import MagicMock
from zero_sum_eval.game_state import GameState, Action, PlayerDefinition
from zero_sum_eval.player import Player
from zero_sum_eval.registry import GAME_REGISTRY, PLAYER_REGISTRY

# Mock the entire Player class
@pytest.fixture
def mock_player():
    # Create a mock player class that doesn't need LM initialization
    class MockPlayer(Player):
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', 'test_id')
            self.player_key = kwargs.get('player_key', 'player1')
            # Initialize module_dict from init_action_module_dict
            self.action_fn_dict = self.init_actions()
            # Set other required attributes
            self.actions = kwargs.get('actions', [])
            self.llm_model = MagicMock()
            
        def init_actions(self):
            return {"test_action": MagicMock()}

    # Register the mock player
    PLAYER_REGISTRY.register("testgamestate", "mockplayer")(MockPlayer)
    return MockPlayer

class TestGameState(GameState):
    def get_scores(self):
        return {"player1": 0, "player2": 0}
    
    def update_game(self, move):
        # simulate an update taking time to test time logging
        time.sleep(0.001)
        pass
    
    def is_over(self):
        return False
    
    def get_next_action(self):
        return Action(name="test_action", player_key="player1", inputs={})
    
    def player_definitions(self):
        return [
            PlayerDefinition("player1", ["test_action"], self.mock_player_class),
            PlayerDefinition("player2", ["test_action"], self.mock_player_class)
        ]
    
    def __init__(self, players, mock_player_class=None, **kwargs):
        self.mock_player_class = mock_player_class
        super().__init__(players=players, **kwargs)

# Register the test game
GAME_REGISTRY.register("testgamestate")(TestGameState)

def test_game_state_initialization(mock_player):
    players_config = {
        "player1": {"args": {}},
        "player2": {"args": {}}
    }
    game = TestGameState(players=players_config, mock_player_class=mock_player)
    
    assert "player1" in game.players
    assert "player2" in game.players
    assert isinstance(game.players["player1"], mock_player)
    assert isinstance(game.players["player2"], mock_player)

def test_game_state_logging(mock_player):
    players_config = {
        "player1": {"args": {}},
        "player2": {"args": {}}
    }
    game = TestGameState(players=players_config, mock_player_class=mock_player, log_moves=True)
    
    # Test that moves are logged
    class TestMove:
        value = "test_move"
        time = 0.1
        class MockTrace:
            def toDict(self):
                return {}
        trace = MockTrace()
    
    game.update_game(TestMove())
    exported = game.export()
    assert "last_move" in exported
    assert "last_trace" in exported
    assert "next_action" in exported
    assert "player_key" in exported
    assert "time" in exported
    assert exported["last_move"] == "test_move"
    assert exported["last_trace"] == {}
    assert exported["next_action"] == "test_action"
    assert exported["player_key"] == "player1"
    assert isinstance(exported["time"], float)
    assert exported["time"] > 0

def test_game_state_version_logging(mock_player):
    players_config = {
        "player1": {"args": {}},
        "player2": {"args": {}}
    }
    game = TestGameState(players=players_config, mock_player_class=mock_player, log_moves=True)
    
    # Test that version is logged
    class TestMove:
        value = "test_move"
        time = 0.1
        class MockTrace:
            def toDict(self):
                return {}
        trace = MockTrace()
    
    game.update_game(TestMove())
    exported = game.export()
    
    # Check that version is included in the export
    assert "zseval_version" in exported
    # Version should be a string
    assert isinstance(exported["zseval_version"], str)
    # Version should either be a valid version string or "unknown"
    import re
    version_pattern = r"^\d+\.\d+\.\d+$"  # Simple version pattern like "0.1.0"
    assert re.match(version_pattern, exported["zseval_version"]) or exported["zseval_version"] == "unknown"