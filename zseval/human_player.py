#file human_player.py
class Player:
    def __init__(self, args):
        self.role = args.get('role')
        self.max_tries = args.get('max_tries', 3)
        self.id = args.get('id', 'human')

    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")

        return move.strip()

