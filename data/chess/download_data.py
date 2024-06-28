import pandas as pd

# TODO replace this dataset with one where Black also wins

dataset = pd.read_csv('~/Downloads/stockfish_dataset.csv')
trunc_dataset = dataset[:1000]
trunc_dataset.to_json('stockfish_games.jsonl', orient='records', lines=True)