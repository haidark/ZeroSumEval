import pytest
from zero_sum_eval.games.chess import ChessGame
from zero_sum_eval.game_state import InvalidMoveError

@pytest.fixture
def chess_game(base_player_config):
    players_config = {
        "white": base_player_config(
            "white",
            "chess_player",
            ["MakeMove"]
        ),
        "black": base_player_config(
            "black",
            "chess_player",
            ["MakeMove"]
        )
    }
    return ChessGame(players=players_config)

def test_chess_game_initialization(chess_game):
    assert chess_game.board is not None
    assert len(chess_game.history) == 0
    assert chess_game.scores == {"white": 0, "black": 0}
    assert "white" in chess_game.players
    assert "black" in chess_game.players

def test_chess_valid_moves(chess_game, mock_move):
    # Test a valid opening move for white
    chess_game.update_game(mock_move("e4"))
    assert "e4" in [str(m) for m in chess_game.history]
    assert not chess_game.board.turn  # False means black's turn

def test_chess_invalid_moves(chess_game, mock_move):
    # Test an invalid move
    with pytest.raises(InvalidMoveError):
        chess_game.update_game(mock_move("e9"))

def test_chess_game_over_conditions(chess_game, mock_move):
    # Fool's mate sequence
    moves = ["f3", "e5", "g4", "Qd8h4"]
    for move in moves:
        chess_game.update_game(mock_move(move))
    
    assert chess_game.is_over()
    scores = chess_game.get_scores()
    assert scores["black"] > scores["white"] 

def test_chess_game_display(chess_game):
    display_str = chess_game.display()
    assert "white to move" in display_str

def test_chess_game_export(chess_game):
    export_dict = chess_game.export()
    assert "MakeMove" in export_dict["next_action"]
