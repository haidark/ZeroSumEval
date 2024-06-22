import chess
import yaml
from game_manager import GameManager
from game_state import GameState

class ChessGame(GameState):
    def __init__(self, roles=None, environment=None, context=None):
        super().__init__()
        self.environment = environment if environment is not None else chess.Board().fen()
        self.roles = self.get_next_roles(self.environment) if roles is None else roles
        self.context = context if context is not None else {"history": [], "message": None}
        self.board = chess.Board(self.environment)  # Cache the board state

    def initialize(self, environment, context=None ,roles=None):
        return ChessGame(
            roles=roles,
            environment=environment,
            context=context if context is not None else {"history": [], "message": None}

        )

    def update_game(self, move):
        new_context = self.context.copy()

        try:
            chess_move = self.board.parse_san(move)
            if self.board.is_legal(chess_move):
                self.board.push(chess_move)
                new_context['history'].append(f"{self.roles[0]} -> {move}")
                new_context['message'] = None 
                #maybe fix message here
            else:
                new_context['message'] = f"Your move {move} is an illegal move"
        except ValueError as e:
            new_context['message'] = f"Your move {move} caused an error: {str(e)} "

        new_environment = self.board.fen()
        return self.initialize(
            environment=new_environment,
            context=new_context
        )

    def query_game(self):
        
        new_context = self.context.copy()
        new_roles = [self.roles[0]]
        msg = self.validate_game() 
        new_context['message'] = msg if msg is not None else f"You will move as {self.get_next_roles(self.environment)[0]}" 

        return self.initialize(
            environment=self.environment,
            context=new_context,
            roles=new_roles
        )

    def validate_game(self):
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
        else:
            return self.context['message'] 

    def get_next_roles(self, fen):
        turn = fen.split()[1]  # 'w' or 'b'
        return ['White', 'Black'] if turn == 'w' else ['Black', 'White']

    def export(self):
        return yaml.dump({
            'roles': self.roles,
            'environment': self.environment,
            'context': self.context
        })

if __name__ == "__main__":
    chess_game = ChessGame().initialize(chess.Board().fen())
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

