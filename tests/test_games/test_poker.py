import pytest
from zero_sum_eval.games.poker import PokerGame
from zero_sum_eval.core.game_state import InvalidMoveError

@pytest.fixture
def poker_game(base_player_config):
    # For simplicity, we create a 2-player game.
    # In a 2-player setting, player_0 is the big blind and player_1 posts the small blind.
    players_config = {
        "player_0": base_player_config("player_0", "poker_player", ["MakeMove"]),
        "player_1": base_player_config("player_1", "poker_player", ["MakeMove"]),
    }
    # Use 1 round to more easily test finalization.
    return PokerGame(players=players_config, rounds=1, starting_chips=1000, small_blind=10)

def test_poker_game_initialization(poker_game):
    scores = poker_game.get_scores()
    # In a 2-player game:
    # Dealer is player_0 by default, so:
    #   small blind is posted by player_1 (10 chips)
    #   big blind is posted by player_0 (20 chips)
    assert scores["player_0"] == 1000 - poker_game.big_blind  # 980
    assert scores["player_1"] == 1000 - poker_game.small_blind  # 990
    # The pot should be the sum of the blinds.
    assert poker_game.pot == poker_game.small_blind + poker_game.big_blind  # 30
    # The game should start at the "preflop" stage with an empty history.
    assert poker_game.stage == "preflop"
    assert len(poker_game.history) == 0

def test_valid_call_move(poker_game, mock_move):
    # At initialization in a 2-player game:
    #   player_0 (big blind) and player_1 (small blind) have posted their blinds.
    # The current player is determined as (bb_pos + 1) mod num_players.
    # With dealer at player_0, bb is player_0 and current_player becomes player_1.
    # Player_1's bet is 10, so a "Call" should require posting an extra 10 to match the current bet of 20.
    poker_game.update_game(mock_move("Call"))
    
    scores = poker_game.get_scores()
    # Player_1 should have lost 10 more chips.
    assert scores["player_1"] == 990 - 10  # becomes 980
    # The pot increases by 10 (from 30 to 40).
    assert poker_game.pot == 30 + 10
    # Check that the move was recorded in history.
    assert any("player_1: Call 10" in entry for entry in poker_game.history)

def test_valid_raise_move(poker_game, mock_move):
    # When player_1 (the first to act) chooses to raise, the raise amount must be at least the big blind (20).
    # Their call amount is current_bet (20) minus their small blind (10) = 10, so a raise of 20 means
    # they must post an additional 10 (to call) + 20 (raise) = 30 chips.
    poker_game.update_game(mock_move("Raise 20"))
    
    scores = poker_game.get_scores()
    # Player_1's chips: 990 - 30 = 960.
    assert scores["player_1"] == 960
    # The current bet should now update to player_1's total bet (10 + 30 = 40).
    assert poker_game.current_bet == 40
    # History should record the raise.
    assert any("player_1: Raise 20" in entry for entry in poker_game.history)

def test_invalid_move(poker_game, mock_move):
    # Test that an unrecognized move results in an InvalidMoveError.
    with pytest.raises(InvalidMoveError):
        poker_game.update_game(mock_move("InvalidAction"))

def test_hand_finalization_fold(poker_game, mock_move):
    # In a 2-player hand, if one player folds then the hand is finalized and the remaining player wins the pot.
    # Current order: player_1 acts first.
    # Let player_1 "Call" to complete the bet, then player_0 "Fold".
    poker_game.update_game(mock_move("Call"))
    poker_game.update_game(mock_move("Fold"))
    
    # Finalization should award the pot to player_1 (the only active player).
    # Check that the message indicates a win by default.
    assert "player_1 wins the pot" in poker_game.message
    # Since we set rounds=1, the hand should be the final hand and the game is over.
    assert poker_game.is_over()

def test_game_over_conditions(poker_game, mock_move):
    # Test that the game recognizes a game-over state if only one player has chips.
    # For testing purposes, manually reduce one player's chips.
    poker_game.chips["player_0"] = 0
    assert poker_game.is_over()