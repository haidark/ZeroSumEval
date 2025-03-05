import pytest
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
        pass
    
    def is_over(self):
        return False
    
    def get_next_action(self):
        return Action("test_action", self.players["player1"])
    
    def player_inputs(self):
        return {}
    
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
        trace = type('obj', (object,), {'toDict': lambda self: {}})()
    
    game.update_game(TestMove())
    exported = game.export()
    assert "last_move" in exported
    assert exported["last_move"] == "test_move" 