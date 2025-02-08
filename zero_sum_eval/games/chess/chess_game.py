import chess

from zero_sum_eval.games.chess.chess_player import ChessPlayer, WHITE_KEY, BLACK_KEY
from zero_sum_eval.player import Move
from zero_sum_eval.game_state import Action, GameState, InvalidMoveError, PlayerDefinition
from zero_sum_eval.registry import GAME_REGISTRY
from typing import Dict, List

@GAME_REGISTRY.register("chess")
class ChessGame(GameState):
    """
    This is a two-player game where the players take turns to make moves in a chess game.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = chess.Board()
        self.history = []
        self.scores = {WHITE_KEY: 0, BLACK_KEY: 0}
        self.message = f"{WHITE_KEY} to move."

    def update_game(self, move: Move):
        try:
            chess_move = self.board.parse_san(move.value)
            san = self.board.san(chess_move)
            self.board.push(chess_move)
            self.history.append(san)
            self.message = f"{WHITE_KEY} to move." if self.board.turn else f"{BLACK_KEY} to move."

            if self.board.is_checkmate():
                self.message = f"Checkmate"
                winner = WHITE_KEY if self.board.turn else BLACK_KEY
                loser = BLACK_KEY if self.board.turn else WHITE_KEY
                self.scores = {winner: 1, loser: 0}
            elif not self.board.is_valid():
                self.message = f"Invalid move"
                winner = BLACK_KEY if self.board.turn else WHITE_KEY
                loser = WHITE_KEY if self.board.turn else BLACK_KEY
                self.scores = {winner: 1, loser: 0}
            elif self.board.is_stalemate():
                self.message = f"Stalemate"
                self.scores = {WHITE_KEY: 0.5, BLACK_KEY: 0.5}
            elif self.board.is_insufficient_material():
                self.message = f"Insufficient material"
                self.scores = {WHITE_KEY: 0.5, BLACK_KEY: 0.5}
            elif self.board.is_seventyfive_moves():
                self.message = f"Seventy-five moves"
                self.scores = {WHITE_KEY: 0.5, BLACK_KEY: 0.5}
            elif self.board.is_fivefold_repetition():
                self.message = f"Fivefold repetition"
                self.scores = {WHITE_KEY: 0.5, BLACK_KEY: 0.5}

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
        return Action("MakeMove", self.players[WHITE_KEY]) if self.board.turn else Action("MakeMove", self.players[BLACK_KEY])

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

    def player_definitions(self) -> List[PlayerDefinition]:
        return [
            PlayerDefinition(player_key=WHITE_KEY, actions=["MakeMove"], default_player_class=ChessPlayer),
            PlayerDefinition(player_key=BLACK_KEY, actions=["MakeMove"], default_player_class=ChessPlayer)
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

