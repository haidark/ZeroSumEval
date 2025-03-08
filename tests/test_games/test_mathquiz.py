import pytest
from zero_sum_eval.games.mathquiz import MathQuizGame
from zero_sum_eval.core.game_state import InvalidMoveError
from copy import deepcopy

@pytest.fixture
def mathquiz_game(base_player_config):
    players_config = {
        "teacher": base_player_config(
            "teacher",
            "mathquiz_teacher",
            []
        ),
        "student": base_player_config(
            "student",
            "mathquiz_student",
            []
        )
    }
    game = MathQuizGame(players=players_config)
    game.target = str(10)
    return game

def test_mathquiz_game_initialization(mathquiz_game):
    assert len(mathquiz_game.players) == 2
    assert "teacher" in mathquiz_game.players
    assert "student" in mathquiz_game.players
    assert mathquiz_game.scores == {"teacher": 0, "student": 0}
    assert mathquiz_game.question is None
    assert mathquiz_game.target == "10"

def test_mathquiz_game_flow(mathquiz_game, mock_move):
    # Teacher generates question
    mathquiz_game.update_game(mock_move("What is 5 + 5?"))
    assert mathquiz_game.question == "What is 5 + 5?"
    
    # Teacher validates with answer
    mathquiz_game.update_game(mock_move("10"))
    assert mathquiz_game.teacher_answer == "10"
    
    # Student answers correctly
    mathquiz_game.update_game(mock_move("10"))
    assert mathquiz_game.student_answer == "10"
    
    scores = mathquiz_game.get_scores()
    assert scores["student"] == 1
    assert scores["teacher"] == 0

def test_mathquiz_invalid_answers(mathquiz_game, mock_move):
    # Teacher generates question
    test_mathquiz_game = deepcopy(mathquiz_game)
    test_mathquiz_game.update_game(mock_move("What is 5 + 5?"))
    
    # Teacher validates with wrong answer
    with pytest.raises(InvalidMoveError, match="TeacherIncorrect"):
        test_mathquiz_game.update_game(mock_move("11"))

    # Reset game state and try student wrong answer
    test_mathquiz_game = deepcopy(mathquiz_game)
    test_mathquiz_game.update_game(mock_move("What is 5 + 5?"))
    test_mathquiz_game.update_game(mock_move("10"))
    
    with pytest.raises(InvalidMoveError, match="StudentIncorrect"):
        test_mathquiz_game.update_game(mock_move("11"))