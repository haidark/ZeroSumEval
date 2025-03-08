import pytest
from zero_sum_eval.games.gandalf import GandalfGame
from zero_sum_eval.games.gandalf.gandalf_player import SENTINEL_KEY, INFILTRATOR_KEY
from zero_sum_eval.core.game_state import InvalidMoveError

@pytest.fixture
def gandalf_game(base_player_config):
    players_config = {
        SENTINEL_KEY: base_player_config(
            "test_sentinel",
            "gandalf_sentinel",
            ["sentinel"]
        ),
        INFILTRATOR_KEY: base_player_config(
            "test_infiltrator",
            "gandalf_infiltrator",
            ["infiltrator"]
        )
    }
    
    return GandalfGame(
        players=players_config,
        secret_password="test_password",
        max_turns=20
    )

def test_gandalf_game_initialization(gandalf_game):
    assert gandalf_game.secret_password == "test_password"
    assert gandalf_game.max_turns == 20
    assert len(gandalf_game.players) == 2
    assert SENTINEL_KEY in gandalf_game.players
    assert INFILTRATOR_KEY in gandalf_game.players

def test_gandalf_game_flow(gandalf_game):
    assert not gandalf_game.is_over()

def test_gandalf_scoring(gandalf_game):
    scores = gandalf_game.get_scores()
    assert SENTINEL_KEY in scores
    assert INFILTRATOR_KEY in scores

def test_gandalf_game_over(gandalf_game):
    gandalf_game.max_turns = 2
    assert not gandalf_game.is_over()  # Initially not over
    # Simulate 2 turns
    gandalf_game.conversation.extend([
        {"name": INFILTRATOR_KEY, "message": "test message"},
        {"name": SENTINEL_KEY, "message": "test response"}
    ])
    assert gandalf_game.is_over()

def test_gandalf_invalid_moves(gandalf_game, mock_move):
    with pytest.raises(InvalidMoveError):
        gandalf_game.update_game(mock_move("\n invalid move with newline"))