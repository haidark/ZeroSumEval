import chess
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY


@GAME_REGISTRY.register("chess")
class ChessGame(GameState):

    def instantiate(self, environment: dict, context: dict, roles: list[str], board: chess.Board) -> None:
        self.environment = environment if environment else {"fen": chess.Board().fen()}
        self.context = context if context else {"message": "", "history": []}
        self.roles = roles if roles else self.get_next_roles()
        self.board = board if board else chess.Board(self.environment["fen"])

    def update_game(self, move: str) -> GameState:
        new_game = ChessGame().instantiate(
            self.environment.copy(), 
            self.context.copy(), 
            self.roles.copy(), 
            self.board.copy()
        )

        try:
            chess_move = new_game.board.parse_san(move)
            if new_game.board.is_legal(chess_move):
                new_game.board.push(chess_move)
                new_game.context['history'].append(move)
                new_game.context['message'] = ""
                new_game.environment["fen"] = new_game.board.fen()
                new_game.roles = new_game.get_next_roles()
            else:
                new_game.context['message'] = f"Your move {move} is an illegal move"
        except ValueError as e:
            new_game.context['message'] = f"Your move {move} caused an error: {str(e)}"

        return new_game

    def query_game(self) -> GameState:
        new_game = ChessGame().instantiate(
            self.environment.copy(), 
            self.context.copy(), 
            self.roles.copy(), 
            self.board.copy()
        )
        
        msg = new_game.validate_game()
        new_game.context['message'] = msg if msg else f"You will move as {new_game.roles[0]}"

        return new_game

    def validate_game(self) -> str | None:
        if self.board.is_checkmate():
            return "Checkmate"
        elif self.board.is_stalemate():
            return "Stalemate"
        elif self.board.is_insufficient_material():
            return "Insufficient material"
        elif self.board.is_seventyfive_moves():
            return "75-move rule"
        elif self.board.is_fivefold_repetition():
            return "Fivefold repetition"
        elif not self.board.is_valid():
            return "Invalid"
        return None

    def get_next_roles(self) -> list[str]:
        turn = self.board.turn
        return ['White', 'Black'] if turn else ['Black', 'White']

    def formatted_move_history(self) -> str:
        history = self.context['history']
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

    def export(self):
        return {
            'roles': self.roles,
            'environment': self.environment,
            'context': self.context
        }
    
    def display(self):
        display_str = f"Role to Act: {self.roles[0]}\nMessage: {self.context['message']}\n"
        display_str += f"{self.formatted_move_history()}\n"
        display_str += f"{self.board}\n"
        return display_str


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
