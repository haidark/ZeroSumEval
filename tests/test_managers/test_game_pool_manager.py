import os
import json
import pytest
from unittest.mock import MagicMock, patch

from zero_sum_eval.managers.game_pool_manager import GamePoolManager
from zero_sum_eval.core.registry import GAME_REGISTRY

class DummyPlayerDef:
    def __init__(self, player_key, optional=False):
        self.player_key = player_key
        self.optional = optional

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Fixture to provide a temporary output directory."""
    output_dir = tmp_path / "pool_output"
    output_dir.mkdir(parents=True, exist_ok=True)  # Create the directory
    return str(output_dir)

@pytest.fixture
def default_llm_configs():
    """Return a default list of LLM configurations with duplicates to test renaming."""
    return [
        {
            "name": "gpt-4o",
            "model": "openrouter/openai/chatgpt-4o-latest",
        },
        {
            "name": "claude-3-5-sonnet",
            "model": "openrouter/claude-3-5-sonnet-20240620",
        },
        {
            "name": "gpt-4o",  # duplicate name to trigger renaming logic
            "model": "openrouter/openai/chatgpt-4o-latest",
        }
    ]

@pytest.fixture
def dummy_game_registry():
    """
    Create a dummy registry entry for the game.
    This dummy object provides:
      - player_definitions(): returns a list of one dummy player definition.
      - build(): returns a dummy game object.
    """
    dummy_registry_entry = MagicMock()
    dummy_registry_entry.player_definitions.return_value = [DummyPlayerDef("player1", optional=False)]
    dummy_game = MagicMock()
    dummy_registry_entry.build.return_value = dummy_game
    return dummy_registry_entry

@pytest.fixture(autouse=True)
def patch_game_registry(dummy_game_registry):
    """
    Patch GAME_REGISTRY so that GAME_REGISTRY['chess'] returns our dummy_registry_entry.
    This ensures that _get_player_configs and _build_game can work without relying on the real registry.
    """
    with patch.object(GAME_REGISTRY, "__getitem__", return_value=dummy_game_registry):
        yield

def test_game_pool_manager_initialization(tmp_output_dir, default_llm_configs):
    """Test that the GamePoolManager correctly processes LLM configs and initializes match frequencies."""
    manager = GamePoolManager(
        max_matches=5,
        max_concurrent_matches=2,
        output_dir=tmp_output_dir,
        game="chess",
        game_args={"players": {}},
        llm_configs=default_llm_configs,
    )
    # Check that duplicate LLM names have been renamed uniquely.
    llm_names = list(manager.llm_configs.keys())
    assert "gpt-4o" in llm_names
    # One of the duplicate should have been renamed (e.g., "gpt-4o_2")
    assert any(name.startswith("gpt-4o_") for name in llm_names)
    # Ensure that match frequency dict is initialized (keys come from matcher.matches)
    assert isinstance(manager.match_freq, dict)
    assert len(manager.match_freq) > 0

def test_start(tmp_output_dir, default_llm_configs):
    """
    Test the start method by patching run_match to simulate match outcomes.
    We simulate two matches with different outcomes (a win in one match and a tie in another)
    and then check that the win/draw/loss tally is correctly updated.
    """
    # Use a configuration with three LLMs.
    manager = GamePoolManager(
        max_matches=2,
        max_concurrent_matches=1,
        max_player_attempts=5,
        output_dir=tmp_output_dir,
        game="chess",
        game_args={"players": {}},
        llm_configs=default_llm_configs,
    )
    # Reset llm_wdl to known initial state for our three models.
    manager.llm_wdl = {
        "gpt-4o": {"wins": 0, "draws": 0, "losses": 0},
        "claude-3-5-sonnet": {"wins": 0, "draws": 0, "losses": 0},
        "mistral-large": {"wins": 0, "draws": 0, "losses": 0},
    }

    # Define two simulated match results.
    # In the first match, gpt-4o wins.
    result1 = {
        "gpt-4o": {"score": 10, "role": "white", "attempts": 0},
        "claude-3-5-sonnet": {"score": 5, "role": "black", "attempts": 0},
        "mistral-large": {"score": 5, "role": "black", "attempts": 0},
    }
    # In the second match, all three tie.
    result2 = {
        "gpt-4o": {"score": 3, "role": "white", "attempts": 0},
        "claude-3-5-sonnet": {"score": 3, "role": "black", "attempts": 0},
        "mistral-large": {"score": 0, "role": "black", "attempts": 0},
    }

    # Patch run_match so that the two matches return our predetermined results.
    with patch.object(manager, "run_match", side_effect=[result1, result2]) as mock_run_match:
        final_wdl = manager.start()

    # Expected tallies:
    # From match 1: gpt-4o wins (others lose).
    # From match 2: gpt-4o, claude-3-5-sonnet draw but mistral-large loses.
    expected_wdl = {
        "gpt-4o": {"wins": 1, "draws": 1, "losses": 0},
        "claude-3-5-sonnet": {"wins": 0, "draws": 1, "losses": 1},
        "mistral-large": {"wins": 0, "draws": 0, "losses": 2},
    }
    assert final_wdl == expected_wdl

    # Check that the wdl.json file was written in the output_dir.
    wdl_path = os.path.join(tmp_output_dir, "wdl.json")
    assert os.path.exists(wdl_path)
    with open(wdl_path, "r") as f:
        file_wdl = json.load(f)
    assert file_wdl == expected_wdl

def test_start_with_max_player_attempts(tmp_output_dir, default_llm_configs):
    """
    Test the start method with max_player_attempts set to 5.
    """
    manager = GamePoolManager(
        max_matches=1,
        max_concurrent_matches=1,
        max_player_attempts=5,
        output_dir=tmp_output_dir,
        game="chess",
        game_args={"players": {}},
        llm_configs=default_llm_configs,
    )
    # Reset llm_wdl to known initial state for our three models.
    manager.llm_wdl = {
        "gpt-4o": {"wins": 0, "draws": 0, "losses": 0},
        "claude-3-5-sonnet": {"wins": 0, "draws": 0, "losses": 0},
        "mistral-large": {"wins": 0, "draws": 0, "losses": 0},
    }
    # gpt-4o scores highest, but uses all 5 attempts. Therefore, it loses.
    # claude-3-5-sonnet and mistral-large score the same, so they draw.
    result = {
        "gpt-4o": {"score": 10, "role": "white", "attempts": 5},
        "claude-3-5-sonnet": {"score": 5, "role": "black", "attempts": 0},
        "mistral-large": {"score": 5, "role": "black", "attempts": 0},
    }

    # Patch run_match so that the two matches return our predetermined results.
    with patch.object(manager, "run_match", side_effect=[result]) as mock_run_match:
        final_wdl = manager.start()

    expected_wdl = {
        "gpt-4o": {"wins": 0, "draws": 0, "losses": 1},
        "claude-3-5-sonnet": {"wins": 0, "draws": 1, "losses": 0},
        "mistral-large": {"wins": 0, "draws": 1, "losses": 0},
    }
    assert final_wdl == expected_wdl
