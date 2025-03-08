import pytest
from zero_sum_eval.games.liars_dice.liars_dice_game import LiarsDiceGame
from zero_sum_eval.games.liars_dice.liars_dice_player import PLAYER_0_KEY, PLAYER_1_KEY
from zero_sum_eval.core.game_state import InvalidMoveError
from unittest.mock import MagicMock

@pytest.fixture
def liars_dice_game(base_player_config):
    """Create a game instance with fixed dice for testing"""
    # Create players config using the base_player_config fixture
    players = {
        PLAYER_0_KEY: base_player_config(
            f"mock_{PLAYER_0_KEY}", 
            "liars_dice_player",
            ["MakeBid"]
        ),
        PLAYER_1_KEY: base_player_config(
            f"mock_{PLAYER_1_KEY}", 
            "liars_dice_player",
            ["MakeBid"]
        )
    }
    
    game = LiarsDiceGame(num_dice=2, players=players)
    # Override random dice with fixed values for testing
    game.dice = {
        PLAYER_0_KEY: [1, 2],  # Player 0 has a 1 and a 2
        PLAYER_1_KEY: [2, 3]   # Player 1 has a 2 and a 3
    }
    return game

def test_initial_game_state(liars_dice_game):
    """Test the initial game state"""
    assert liars_dice_game.num_dice == 2
    assert liars_dice_game.current_bid == (0, 0)
    assert len(liars_dice_game.history) == 0
    assert liars_dice_game.scores == {PLAYER_0_KEY: 0, PLAYER_1_KEY: 0}
    assert liars_dice_game.message == f"{PLAYER_0_KEY} to bid"
    assert not liars_dice_game.is_over()

def test_valid_first_bid(liars_dice_game, mock_move):
    """Test making a valid first bid"""
    move = mock_move("[Bid] 1 2")
    liars_dice_game.update_game(move)
    assert liars_dice_game.current_bid == (1, 2)
    assert len(liars_dice_game.history) == 1
    assert liars_dice_game.history[0] == "[Bid] 1 2"
    assert not liars_dice_game.is_over()

def test_invalid_first_bid_format(liars_dice_game, mock_move):
    """Test making an invalid first bid"""
    with pytest.raises(InvalidMoveError, match="Invalid action format"):
        liars_dice_game.update_game(mock_move("Bid 1 2"))

def test_invalid_bid_values(liars_dice_game, mock_move):
    """Test bids with invalid values"""
    # Test face value too high
    with pytest.raises(InvalidMoveError, match="Face value must be between 1 and 6"):
        liars_dice_game.update_game(mock_move("[Bid] 1 7"))
    
    # Test quantity zero
    with pytest.raises(InvalidMoveError, match="Quantity must be positive"):
        liars_dice_game.update_game(mock_move("[Bid] 0 2"))

def test_bid_must_increase(liars_dice_game, mock_move):
    """Test that each bid must increase either quantity or face value"""
    liars_dice_game.update_game(mock_move("[Bid] 2 3"))
    
    # Same quantity, lower face
    with pytest.raises(InvalidMoveError, match="New bid must increase quantity or face value"):
        liars_dice_game.update_game(mock_move("[Bid] 2 2"))
    
    # Lower quantity, same face
    with pytest.raises(InvalidMoveError, match="New bid must increase quantity or face value"):
        liars_dice_game.update_game(mock_move("[Bid] 1 3"))

def test_calling_liar_correct(liars_dice_game, mock_move):
    """Test calling liar when the bid is too high"""
    # Set up a bid that's too high
    liars_dice_game.update_game(mock_move("[Bid] 3 2"))  # Bid 3 twos when there are only 2
    liars_dice_game.update_game(mock_move("[Call]"))
    
    assert liars_dice_game.is_over()
    assert liars_dice_game.scores == {PLAYER_0_KEY: 0, PLAYER_1_KEY: 1}  # Player 1 wins
    assert "Game Over" in liars_dice_game.message

def test_calling_liar_incorrect(liars_dice_game, mock_move):
    """Test calling liar when the bid is valid"""
    # Bid 2 twos when there are exactly 2
    liars_dice_game.update_game(mock_move("[Bid] 2 2"))
    liars_dice_game.update_game(mock_move("[Call]"))
    
    assert liars_dice_game.is_over()
    assert liars_dice_game.scores == {PLAYER_0_KEY: 1, PLAYER_1_KEY: 0}  # Player 0 wins
    assert "Game Over" in liars_dice_game.message

def test_player_inputs(liars_dice_game):
    """Test that player inputs are correctly formatted"""
    inputs = liars_dice_game.get_next_action().inputs
    assert 'dice_roll' in inputs
    assert 'current_bid' in inputs
    assert 'history' in inputs
    
    # Check first player sees their own dice
    assert str([1, 2]) in inputs['dice_roll']

def test_alternating_turns(liars_dice_game, mock_move):
    """Test that players alternate turns correctly"""
    assert liars_dice_game.get_next_action().player_key == PLAYER_0_KEY
    liars_dice_game.update_game(mock_move("[Bid] 1 2"))
    assert liars_dice_game.get_next_action().player_key == PLAYER_1_KEY

def test_game_display(liars_dice_game):
    """Test the game display string"""
    display = liars_dice_game.display()
    assert "Current bid: 0 0s" in display
    assert "Player 0 dice: [1, 2]" in display
    assert "Player 1 dice: [2, 3]" in display 