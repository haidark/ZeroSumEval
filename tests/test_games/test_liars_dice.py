import pytest
from zero_sum_eval.games.liars_dice.liars_dice_game import LiarsDiceGame
from zero_sum_eval.games.liars_dice.liars_dice_player import LiarsDicePlayer, PLAYER_0_KEY, PLAYER_1_KEY
from zero_sum_eval.player import Move
from zero_sum_eval.game_state import InvalidMoveError

class MockTrace:
    def toDict(self):
        return {}

class MockMove:
    def __init__(self, value):
        self.value = value
        self.trace = MockTrace()

class MockPlayer:
    def __init__(self, player_key):
        self.player_key = player_key
        self.id = f"mock_{player_key}"

@pytest.fixture
def game():
    """Create a game instance with fixed dice for testing"""
    # Create players config dictionary in the expected format
    players = {
        PLAYER_0_KEY: {
            "class": "liars_dice_player",
            "args": {
                "id": f"mock_{PLAYER_0_KEY}",
                "actions": [{"name": "MakeBid"}],
                "lm": {"model": "mock"},  # Add mock LM config
                "max_tries": 1
            }
        },
        PLAYER_1_KEY: {
            "class": "liars_dice_player",
            "args": {
                "id": f"mock_{PLAYER_1_KEY}",
                "actions": [{"name": "MakeBid"}],
                "lm": {"model": "mock"},  # Add mock LM config
                "max_tries": 1
            }
        }
    }
    
    game = LiarsDiceGame(num_dice=2, players=players)
    # Override random dice with fixed values for testing
    game.dice = {
        PLAYER_0_KEY: [1, 2],  # Player 0 has a 1 and a 2
        PLAYER_1_KEY: [2, 3]   # Player 1 has a 2 and a 3
    }
    return game

def test_initial_game_state(game):
    """Test the initial game state"""
    assert game.num_dice == 2
    assert game.current_bid == (0, 0)
    assert len(game.history) == 0
    assert game.scores == {PLAYER_0_KEY: 0, PLAYER_1_KEY: 0}
    assert game.message == f"{PLAYER_0_KEY} to bid"
    assert not game.is_over()

def test_valid_first_bid(game):
    """Test making a valid first bid"""
    move = MockMove("[Bid] 1 2")
    game.update_game(move)
    assert game.current_bid == (1, 2)
    assert len(game.history) == 1
    assert game.history[0] == "[Bid] 1 2"
    assert not game.is_over()

def test_invalid_first_bid_format(game):
    """Test making an invalid first bid"""
    with pytest.raises(InvalidMoveError, match="Invalid action format"):
        game.update_game(MockMove("Bid 1 2"))

def test_invalid_bid_values(game):
    """Test bids with invalid values"""
    # Test face value too high
    with pytest.raises(InvalidMoveError, match="Face value must be between 1 and 6"):
        game.update_game(MockMove("[Bid] 1 7"))
    
    # Test quantity zero
    with pytest.raises(InvalidMoveError, match="Quantity must be positive"):
        game.update_game(MockMove("[Bid] 0 2"))

def test_bid_must_increase(game):
    """Test that each bid must increase either quantity or face value"""
    game.update_game(MockMove("[Bid] 2 3"))
    
    # Same quantity, lower face
    with pytest.raises(InvalidMoveError, match="New bid must increase quantity or face value"):
        game.update_game(MockMove("[Bid] 2 2"))
    
    # Lower quantity, same face
    with pytest.raises(InvalidMoveError, match="New bid must increase quantity or face value"):
        game.update_game(MockMove("[Bid] 1 3"))

def test_calling_liar_correct(game):
    """Test calling liar when the bid is too high"""
    # Set up a bid that's too high
    game.update_game(MockMove("[Bid] 3 2"))  # Bid 3 twos when there are only 2
    game.update_game(MockMove("[Call]"))
    
    assert game.is_over()
    assert game.scores == {PLAYER_0_KEY: 0, PLAYER_1_KEY: 1}  # Player 1 wins
    assert "Game Over" in game.message

def test_calling_liar_incorrect(game):
    """Test calling liar when the bid is valid"""
    # Bid 2 twos when there are exactly 2
    game.update_game(MockMove("[Bid] 2 2"))
    game.update_game(MockMove("[Call]"))
    
    assert game.is_over()
    assert game.scores == {PLAYER_0_KEY: 1, PLAYER_1_KEY: 0}  # Player 0 wins
    assert "Game Over" in game.message

def test_player_inputs(game):
    """Test that player inputs are correctly formatted"""
    inputs = game.player_inputs()
    assert 'dice_roll' in inputs
    assert 'current_bid' in inputs
    assert 'history' in inputs
    
    # Check first player sees their own dice
    assert str([1, 2]) in inputs['dice_roll']

def test_alternating_turns(game):
    """Test that players alternate turns correctly"""
    assert game.get_next_action().player.player_key == PLAYER_0_KEY
    game.update_game(MockMove("[Bid] 1 2"))
    assert game.get_next_action().player.player_key == PLAYER_1_KEY

def test_game_display(game):
    """Test the game display string"""
    display = game.display()
    assert "Current bid: 0 0s" in display
    assert "Player 0 dice: [1, 2]" in display
    assert "Player 1 dice: [2, 3]" in display 