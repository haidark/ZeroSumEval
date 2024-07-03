import json
import chess
import chess.pgn
import io
from random import randint

def format_move_history(history):
    formatted_history = ""
    moves = len(history)//2+1
    for i in range(1, moves+1):
        j = (i-1)*2
        formatted_history+=f"{i}."
        if j < len(history):
            formatted_history+=f"{history[j]} "
        if j+1 < len(history):
            formatted_history+=f"{history[j+1]} "
    return formatted_history.strip()

if __name__ == "__main__":
    of = open('stockfish_examples.jsonl', 'w')
    with open('stockfish_games.jsonl', 'r') as f:
        for line in f:
            game_obj = json.loads(line)
            transcript = game_obj['transcript']
            game = chess.pgn.read_game(io.StringIO(transcript))
            moves = [str(move) for move in game.mainline_moves()]
            for i in range(0, len(moves)-1):
                board = game.board()
                for move in moves[:i]:
                    board.push_san(move)
                example = dict(board_state=board.fen(), 
                               history=format_move_history(moves[:i]), 
                               move=moves[i],
                               turn=board.turn)
                of.write(json.dumps(example))
                of.write('\n')
    of.close()