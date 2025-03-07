import pytest
from unittest.mock import MagicMock, patch
from zero_sum_eval.managers.game_manager import GameManager

@pytest.fixture
def mock_game():
    """Create a mock game for testing"""
    game = MagicMock()
    game.is_over.side_effect = [False, True]  # Game ends after first move
    
    # Create a proper mock action
    mock_action = MagicMock()
    mock_action.name = "test_action"  # Set name as attribute, not as mock
    mock_action.player = MagicMock(
        id="player1",
        llm_model="mock_model",
        module_dict={
            "test_action": MagicMock(  # Match the action name
                return_value=MagicMock(
                    items=lambda: [("output", "test")]
                )
            )
        }
    )
    
    game.get_next_action.return_value = mock_action
    game.player_inputs.return_value = {}
    game.display.return_value = "game state"
    game.export.return_value = {"state": "test"}
    return game

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    return {
        "max_rounds": 10,
        "max_player_attempts": 3,
        "output_dir": "/tmp/logs",
        "max_time_per_player": 10.0
    }

def test_game_manager_initialization(mock_config):
    """Test GameManager initialization"""
    manager = GameManager(**mock_config)
    assert manager.max_rounds == mock_config["max_rounds"]
    assert manager.max_player_attempts == mock_config["max_player_attempts"]
    assert manager.turns_log_file == "/tmp/logs/turns.jsonl"

@patch('dspy.context')
@patch('jsonlines.Writer')
def test_game_manager_start(mock_writer, mock_context, mock_config, mock_game):
    """Test game manager start functionality"""
    # Create a mock Move with time attribute
    mock_move = MagicMock()
    mock_move.time = 0.5
    mock_move.value = "test move"
    
    # Set up player to return our mock move
    mock_player = MagicMock()
    mock_player.id = "player1"
    mock_player.act.return_value = mock_move
    
    # Set up game state to return our player
    mock_action = MagicMock()
    mock_action.player_key = "player1"
    mock_game.get_next_action.return_value = mock_action
    mock_game.players = {"player1": mock_player}
    
    manager = GameManager(**mock_config)
    manager.game = mock_game
    
    result = manager.start(mock_game)
    
    # Verify game was played correctly
    assert result["game_state"] == mock_game
    assert mock_game.update_game.called
    assert mock_game.get_next_action.called
    assert mock_game.export.called

@patch('dspy.context')
@patch('jsonlines.Writer')
def test_game_manager_turn_handling(mock_writer, mock_context, mock_config, mock_game):
    """Test game manager turn handling"""
    # Create a mock Move with time attribute
    mock_move = MagicMock()
    mock_move.time = 0.5
    mock_move.value = "test move"
    
    # Set up player to return our mock move
    mock_player = MagicMock()
    mock_player.id = "player1"
    mock_player.act.return_value = mock_move
    
    manager = GameManager(**mock_config)
    manager.game = mock_game
    
    # Setup mock action
    mock_action = MagicMock()
    mock_action.name = "test_action"  # Set as attribute
    mock_action.player_key = "test_player"
    mock_game.get_next_action.return_value = mock_action
    mock_game.players = {"test_player": mock_player}
    
    # Test turn execution
    result = manager.start(mock_game)
    
    # Verify turn was handled correctly
    assert mock_player.act.called
    assert mock_game.update_game.called

@patch('dspy.context')
@patch('jsonlines.Writer')
def test_game_manager_logging(mock_writer, mock_context, mock_config, mock_game):
    """Test game manager logging functionality"""
    # Create a mock Move with time attribute
    mock_move = MagicMock()
    mock_move.time = 0.5
    mock_move.value = "test move"
    
    # Set up player to return our mock move
    mock_player = MagicMock()
    mock_player.id = "player1"
    mock_player.act.return_value = mock_move
    
    # Set up game state to return our player
    mock_action = MagicMock()
    mock_action.player_key = "player1"
    mock_game.get_next_action.return_value = mock_action
    mock_game.players = {"player1": mock_player}
    
    manager = GameManager(**mock_config)
    manager.game = mock_game
    
    manager.start(mock_game)
    
    # Verify logging occurred
    assert mock_game.export.called
    assert mock_game.display.called

@patch('dspy.context')
@patch('jsonlines.Writer')
def test_game_manager_error_handling(mock_writer, mock_context, mock_config, mock_game):
    """Test game manager error handling"""
    manager = GameManager(**mock_config)
    manager.game = mock_game
    
    # Setup error condition
    mock_game.update_game.side_effect = Exception("Test error")
    
    # Test error handling
    with pytest.raises(Exception):
        manager.start(mock_game) 