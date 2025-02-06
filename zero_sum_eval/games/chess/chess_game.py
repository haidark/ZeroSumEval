import chess

from zero_sum_eval.games.chess.chess_player import ChessPlayer
from zero_sum_eval.player import Move
from zero_sum_eval.game_state import Action, GameState, InvalidMoveError, PlayerDescription
from zero_sum_eval.registry import GAME_REGISTRY
from typing import Dict

@GAME_REGISTRY.register("chess")
class ChessGame(GameState):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = chess.Board()
        self.history = []
        self.scores = {"white": 0, "black": 0}
        self.message = "White to move."

    def update_game(self, move: Move):
        try:
            chess_move = self.board.parse_san(move.value)
            san = self.board.san(chess_move)
            self.board.push(chess_move)
            self.history.append(san)
            self.message = "White to move." if self.board.turn else "Black to move."

            if self.board.is_checkmate():
                self.message = f"Checkmate"
                winner = "white" if self.board.turn else "black"
                loser = "black" if self.board.turn else "white"
                self.scores = {winner: 1, loser: 0}
            elif not self.board.is_valid():
                self.message = f"Invalid move"
                winner = "black" if self.board.turn else "white"
                loser = "white" if self.board.turn else "black"
                self.scores = {winner: 1, loser: 0}
            elif self.board.is_stalemate():
                self.message = f"Stalemate"
                self.scores = {"white": 0.5, "black": 0.5}
            elif self.board.is_insufficient_material():
                self.message = f"Insufficient material"
                self.scores = {"white": 0.5, "black": 0.5}
            elif self.board.is_seventyfive_moves():
                self.message = f"Seventy-five moves"
                self.scores = {"white": 0.5, "black": 0.5}
            elif self.board.is_fivefold_repetition():
                self.message = f"Fivefold repetition"
                self.scores = {"white": 0.5, "black": 0.5}

        except chess.IllegalMoveError as e:
            raise InvalidMoveError(f"Move {move} is Illegal: {e}")
        except chess.InvalidMoveError as e:
            raise InvalidMoveError(f"Move {move} is Invalid: {e}")
        except chess.AmbiguousMoveError as e:
            raise InvalidMoveError(f"Move {move} is Ambiguous: {e}")
    
    def get_scores(self):
        return self.scores
    
    def is_over(self):
        return self.board.is_game_over() or not self.board.is_valid()

    def get_next_action(self) -> Action:
        return Action("MakeMove", self.players["white"]) if self.board.turn else Action("MakeMove", self.players["black"])

    def formatted_move_history(self) -> str:
        history = self.history
        formatted_history = ""
        moves = len(history)//2+1
        for i in range(1, moves+1):
            j = (i-1)*2
            formatted_history += f"{i}."
            if j < len(history):
                formatted_history += f"{history[j]} "
            if j+1 < len(history):
                formatted_history += f"{history[j+1]} "
        return formatted_history.strip()

    def player_descriptions(self):
        return [
            PlayerDescription(name="white", actions=["MakeMove"], default_player_class=ChessPlayer),
            PlayerDescription(name="black", actions=["MakeMove"], default_player_class=ChessPlayer)
        ]

    def player_inputs(self) -> Dict[str, str]:
        return {
            'board_state': self.board.fen(),
            'role': self.message,
            'history': self.formatted_move_history()
        }
    
    def display(self) -> None:
        display_str = f"{self.message}\n"
        display_str += f"{self.formatted_move_history()}\n"
        display_str += f"{self.board}\n"
        return display_str
    
    def export(self):
        return {
            'message': self.message,
            'board_state': self.board.fen(),
            'next_action': self.get_next_action().name,
            'history': self.history,
            'scores': self.get_scores()
        }

if __name__ == "__main__":
    chess_game = ChessGame()
    chess_game.instantiate({"fen": chess.Board().fen()}, None, None)
    print(chess_game.export())

    # 1. e4 e5
    chess_game = chess_game.update_game("e4")
    print(chess_game.export())

    print(chess_game.query_game().export())
    chess_game = chess_game.update_game("e5")
    print(chess_game.export())

    # 2. Nf3 Nc6
    chess_game = chess_game.update_game("Nf3")
    print(chess_game.query_game().export())
    chess_game = chess_game.update_game("Nc6")
    print(chess_game.export())

    # 3. Nxe5
    chess_game = chess_game.update_game("Nxe5")
    print(chess_game.export())

    validation_result = chess_game.validate_game()
    if validation_result:
        print(f"Game validation result: {validation_result}")
    else:
        print("Game is valid.")
