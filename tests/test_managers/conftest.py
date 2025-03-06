import pytest
from unittest.mock import MagicMock, patch
import dspy
import os
from pathlib import Path
from zero_sum_eval.games.debate.debate_player import FOR_KEY, AGAINST_KEY

@pytest.fixture(autouse=True)
def setup_logs_dir():
    """Create logs directory before tests and clean up after"""
    log_dir = Path("/tmp/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Optional: Clean up after tests
    # import shutil
    # shutil.rmtree(log_dir, ignore_errors=True)

@pytest.fixture
def mock_config():
    """Creates a mock configuration for managers."""
    return {
        "manager": {
            "args": {
                "max_rounds": 10,
                "max_games": 5,
                "max_matches": 3,
                "max_player_attempts": 3
            },
            "game_pool_manager_args": {
                "max_pool_size": 100,
                "cleanup_interval": 3600,
                "max_matches": 5
            },
            "match_manager_args": {
                "match_timeout": 3600,
                "match_cleanup_interval": 3600,
                "max_matches": 3,
                "starting_elo": 1200,
                "matching": "round_robin"
            },
            "game_manager_args": {
                "turn_timeout": 300,
                "turn_cleanup_interval": 3600,
                "max_matches": 2
            }
        },
        "logging": {
            "output_dir": "/tmp/logs"
        },
        "llms": [
            {
                "name": "gpt-4",
                "model": "gpt-4",
                "provider": "openai"
            },
            {
                "name": "mock_model",
                "model": "mock",
                "provider": "mock"
            }
        ],
        "game": {
            "type": "debate",
            "args": {
                "topic": "Test topic",
                "rebuttal_rounds": 1,
                "judges": [{"name": "mock_judge", "model": "mock_model"}],
                "players": [
                    {
                        "args": {
                            "roles": [{"name": "for"}],
                            "lm": {"model": "gpt-4"}
                        }
                    },
                    {
                        "args": {
                            "roles": [{"name": "against"}],
                            "lm": {"model": "mock_model"}
                        }
                    }
                ]
            }
        }
    }

@pytest.fixture
def mock_game():
    """Creates a mock game instance for testing."""
    game = MagicMock()
    game.is_over.return_value = False
    game.get_next_action.return_value = MagicMock(
        name="OpeningStatement",
        player=MagicMock(player_key="for")
    )
    return game

@pytest.fixture
def mock_move():
    """Common mock move with trace for testing."""
    class MockMove:
        def __init__(self, value="test value"):
            self.value = value
            self.trace = type('obj', (object,), {'toDict': lambda self: {}})()
            self.time = 0.1
    return MockMove 