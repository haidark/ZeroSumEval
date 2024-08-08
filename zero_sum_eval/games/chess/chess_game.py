import chess
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY


@GAME_REGISTRY.register("chess")
class ChessGame(GameState):

    def instantiate(self, environment: dict, context: dict, roles: list[str], board: chess.Board = None) -> None:
        self.board = board if board else chess.Board()
        self.environment = environment if environment else {"fen": self.board.fen()}
        self.context = context if context else {"message": "", "history": []}
        self.roles = roles if roles else self.get_next_roles()

    def update_game(self, move: str) -> GameState:
        new_state = ChessGame()
        new_state.instantiate(
            self.environment.copy(), 
            self.context.copy(), 
            self.roles.copy(), 
            self.board.copy()
        )

        chess_move = new_state.board.parse_san(move)
        san = new_state.board.san(chess_move)
        new_state.board.push(chess_move)
        new_state.context['history'].append(san)
        new_state.context['message'] = ""
        new_state.environment["fen"] = new_state.board.fen()
        new_state.roles = new_state.get_next_roles()
        return new_state

    def query_game(self) -> GameState:
        new_state = ChessGame()
        new_state.instantiate(
            environment=self.environment.copy(), 
            context=self.context.copy(), 
            roles=self.roles.copy(), 
            board=self.board.copy()
        )
        
        msg = new_state.validate_game()
        new_state.context['message'] = msg if msg else f"You will move as {new_state.roles[0]}"

        return new_state

    def validate_game(self) -> str | None:
        message = None
        if self.board.is_checkmate():
            message = "Checkmate"
        elif self.board.is_stalemate():
            message = "Stalemate"
        elif self.board.is_insufficient_material():
            message = "Insufficient material"
        elif self.board.is_seventyfive_moves():
            message = "75-move rule"
        elif self.board.is_fivefold_repetition():
            message = "Fivefold repetition"
        elif not self.board.is_valid():
            message = "Invalid"
        if message:
            self.context['message'] = message
        return message

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
            'environment': self.environment['fen'],
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
