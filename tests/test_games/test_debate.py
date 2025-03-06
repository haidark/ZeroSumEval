import pytest
from unittest.mock import MagicMock
from zero_sum_eval.games.debate.debate_game import DebateGame
from zero_sum_eval.games.debate.debate_player import FOR_KEY, AGAINST_KEY


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

@pytest.fixture
def debate_game(base_player_config):
    players_config = {
        FOR_KEY: base_player_config(
            "for_player", 
            "debate_player",
            ["OpeningStatement", "Rebuttal", "ClosingStatement"]
        ),
        AGAINST_KEY: base_player_config(
            "against_player", 
            "debate_player",
            ["OpeningStatement", "Rebuttal", "ClosingStatement"]
        )
    }
    
    game = DebateGame(
        players=players_config,
        topic="AI Safety is important",
        rebuttal_rounds=2,
        judges=[{"name": "mock_judge", "model": "mock_model"}]
    )
    
    # Replace judge module with mock
    game.judge_module = MagicMock()
    game.judge_module.return_value = type('obj', (object,), {
        'weighted_score': 1.0,
        'toDict': lambda self: {}
    })()
    
    return game

def test_debate_game_initialization(debate_game):
    assert FOR_KEY in debate_game.players
    assert AGAINST_KEY in debate_game.players
    assert debate_game.topic == "AI Safety is important"
    assert debate_game.rebuttal_rounds == 2

def test_debate_game_flow(debate_game):
    # Test initial state
    assert not debate_game.is_over()
    assert debate_game.get_scores() == {FOR_KEY: 0, AGAINST_KEY: 0}
    
    # Test that first action is OpeningStatement by FOR player
    action = debate_game.get_next_action()
    assert action.name == "OpeningStatement"
    assert action.player_key == FOR_KEY

def test_debate_game_over(debate_game, mock_move):
    # Calculate total moves needed:
    # 2 opening statements + (2 * rebuttal_rounds) rebuttals + 2 closing statements
    total_moves = 2 + (2 * debate_game.rebuttal_rounds) + 2
    
    # Add moves until we reach the end
    for _ in range(total_moves):
        debate_game.update_game(mock_move("test argument"))
    
    # Test game over state
    assert debate_game.is_over()
    scores = debate_game.get_scores()
    assert scores[FOR_KEY] in [0, 1]
    assert scores[AGAINST_KEY] in [0, 1] 