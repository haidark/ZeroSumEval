import pytest
import textwrap
from zero_sum_eval.games.pyjail import PyJailGame
from zero_sum_eval.game_state import InvalidMoveError

@pytest.fixture
def pyjail_game(base_player_config):
    players_config = {
        "defender": base_player_config("defender", "pyjail_player", ["GeneratePyJail", "SolvePyJail"]),
        "attacker": base_player_config("attacker", "pyjail_player", ["SolvePyJail"])
    }
    # Disable permission prompt and show source code in tests.
    return PyJailGame(players=players_config, ask_permission=False, show_source_code=True, max_attacks=5)

@pytest.fixture
def valid_pyjail_code():
    code = """
def jail(user_input):
    import os
    # Return the secret flag from the environment.
    return os.environ.get("FLAG")
"""
    return textwrap.dedent(code)

@pytest.fixture
def invalid_pyjail_code():
    code = """
def not_jail(user_input):
    return "no flag here"
"""
    return textwrap.dedent(code)

@pytest.fixture
def non_flag_pyjail_code():
    code = """
def jail(user_input):
    return "no flag"
"""
    return textwrap.dedent(code)

def test_pyjail_game_initialization(pyjail_game):
    # Before any moves, no code is set and history is empty.
    assert pyjail_game.pyjail_code is None
    assert pyjail_game.history == []
    assert "defender" in pyjail_game.players
    assert "attacker" in pyjail_game.players
    assert pyjail_game.flag is not None

def test_generate_valid_code(pyjail_game, valid_pyjail_code, mock_move):
    # The first move should be to generate the PyJail code.
    move = mock_move(valid_pyjail_code)
    pyjail_game.update_game(move)
    # The valid code contains a jail function, so it should be accepted.
    assert pyjail_game.pyjail_code is not None
    assert "def jail" in pyjail_game.pyjail_code

def test_generate_invalid_code(pyjail_game, invalid_pyjail_code, mock_move):
    # Using a code snippet without a 'jail' function should raise an error.
    move = mock_move(invalid_pyjail_code)
    with pytest.raises(InvalidMoveError):
        pyjail_game.update_game(move)

def test_defender_solution(pyjail_game, valid_pyjail_code, mock_move):
    # First, generate the valid PyJail code.
    gen_move = mock_move(valid_pyjail_code)
    pyjail_game.update_game(gen_move)
    # Next, simulate the defender's solution move.
    # The provided jail function returns the flag, so the output will contain it.
    solve_input = "defender attempt"
    solve_move = mock_move(solve_input)
    pyjail_game.update_game(solve_move)
    # The first valid solution should be recorded as the defender's.
    assert pyjail_game.defender_solution == solve_input
    # Note that upon a valid defender solution, the history is reset and then one entry is added.
    assert len(pyjail_game.history) == 1
    # With only the defender's solution, scores indicate a defender win.
    scores = pyjail_game.get_scores()
    assert scores == {"defender": 1, "attacker": 0}

def test_attacker_solution(pyjail_game, valid_pyjail_code, mock_move):
    # Generate the code and simulate a valid defender solution.
    gen_move = mock_move(valid_pyjail_code)
    pyjail_game.update_game(gen_move)
    defender_move = mock_move("defender input")
    pyjail_game.update_game(defender_move)
    # Now, simulate an attacker solution move.
    attacker_move = mock_move("attacker input")
    pyjail_game.update_game(attacker_move)
    # The attacker solution should now be recorded.
    assert pyjail_game.attacker_solution == "attacker input"
    # Since both solutions produced output that included the flag, the attacker wins.
    scores = pyjail_game.get_scores()
    assert scores == {"defender": 0, "attacker": 1}
    assert pyjail_game.is_over()

def test_game_over_conditions_max_attacks(pyjail_game, non_flag_pyjail_code, mock_move):
    # Generate PyJail code that defines jail but never returns the flag.
    gen_move = mock_move(non_flag_pyjail_code)
    pyjail_game.update_game(gen_move)
    # Now, simulate max_attacks attempts with solutions that do not yield the flag.
    for _ in range(pyjail_game.max_attacks):
        solve_move = mock_move("attempt")
        pyjail_game.update_game(solve_move)
    # The game should be over once the number of attacks reaches max_attacks.
    assert pyjail_game.is_over()

def test_display_and_export(pyjail_game, valid_pyjail_code, mock_move):
    # Generate code and simulate a defender solution move.
    gen_move = mock_move(valid_pyjail_code)
    pyjail_game.update_game(gen_move)
    solve_move = mock_move("solution")
    pyjail_game.update_game(solve_move)
    display_str = pyjail_game.display()
    assert "Defender Code:" in display_str
    assert "Defender Solution:" in display_str
    # Check that export returns the expected keys.
    export_data = pyjail_game.export()
    for key in ["pyjail_code", "defender_solution", "attacker_solution", "history", "flag"]:
        assert key in export_data

def test_pyjail_game_display(pyjail_game):
    display_str = pyjail_game.display()
    assert "Defender Code: Not set" in display_str

def test_pyjail_game_export(pyjail_game):
    export_dict = pyjail_game.export()
    assert "GeneratePyJail" in export_dict["next_action"]
    assert "flag" in export_dict
    assert "history" in export_dict
    assert "pyjail_code" in export_dict
    assert "defender_solution" in export_dict
    assert "attacker_solution" in export_dict
