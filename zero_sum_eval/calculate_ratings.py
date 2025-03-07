import math
import json
import argparse
from glob import glob
from typing import List

import numpy as np
import pandas as pd

from tqdm import tqdm
from sklearn.linear_model import LogisticRegression

# Function from https://lmsys.org/blog/2023-12-07-leaderboard/
def compute_mle_elo(
    df, SCALE=400, BASE=10, INIT_RATING=1000, sample_weight=None
):
    ptbl_a_win = pd.pivot_table(
        df[df["winner"] == "model_a"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
    )

    # TODO: patch to fix sets with ties when not all models have ties
    # but currently not optimal due to the iterrows().
    ptbl_tie = pd.DataFrame(0, index=ptbl_a_win.index, columns=ptbl_a_win.columns)
    for _, row in df[df["winner"].isin(["tie", "tie (bothbad)"])].iterrows():
        ptbl_tie.loc[row['model_a'],row['model_b']] += 1
        ptbl_tie.loc[row['model_b'],row['model_a']] += 1

    ptbl_b_win = pd.pivot_table(
        df[df["winner"] == "model_b"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
    )
    ptbl_win = ptbl_a_win * 2 + ptbl_b_win.T * 2 + ptbl_tie

    models = pd.Series(np.arange(len(ptbl_win.index)), index=ptbl_win.index)

    p = len(models)
    X = np.zeros([p * (p - 1) * 2, p])
    Y = np.zeros(p * (p - 1) * 2)

    cur_row = 0
    sample_weights = []
    for m_a in ptbl_win.index:
        for m_b in ptbl_win.columns:
            if m_a == m_b:
                continue
            # if nan skip
            if math.isnan(ptbl_win.loc[m_a, m_b]) or math.isnan(ptbl_win.loc[m_b, m_a]):
                continue
            X[cur_row, models[m_a]] = +math.log(BASE)
            X[cur_row, models[m_b]] = -math.log(BASE)
            Y[cur_row] = 1.0
            sample_weights.append(ptbl_win.loc[m_a, m_b])

            X[cur_row + 1, models[m_a]] = math.log(BASE)
            X[cur_row + 1, models[m_b]] = -math.log(BASE)
            Y[cur_row + 1] = 0.0
            sample_weights.append(ptbl_win.loc[m_b, m_a])
            cur_row += 2
    X = X[:cur_row]
    Y = Y[:cur_row]

    lr = LogisticRegression(fit_intercept=False, penalty=None, tol=1e-6)
    lr.fit(X, Y, sample_weight=sample_weights)
    elo_scores = SCALE * lr.coef_[0] + INIT_RATING

    return pd.Series(elo_scores, index=models.index).sort_values(ascending=False)


# Function from https://lmsys.org/blog/2023-12-07-leaderboard/
def get_bootstrap_result(battles, func_compute_elo, num_round):
    rows = []
    for _ in tqdm(range(num_round), desc="bootstrap"):
        try:
            rows.append(func_compute_elo(battles.sample(frac=1.0, replace=True)))
        except KeyError:
            pass
    
    if len(rows) != num_round:
        print(f"Only used {len(rows)}/{num_round} bootstrap rounds due to samples that have zero matches for some models")

    df = pd.DataFrame(rows)
    return df[df.median().sort_values(ascending=False).index]


def convert_matches_to_df(logs_path: str, max_player_attempts: int) -> pd.DataFrame:
    matches = []
    for match_results_path in glob(f'{logs_path}/**/matches/*/scores.json', recursive=True):
        with open(match_results_path) as f:
            scores = json.load(f)
        
        # TODO: just uses first two models of each matchup for now, probably not the correct/best way to do this for multi-player games
        models = list(scores.keys())[:2]

        for model in models:
            if scores[model]['attempts'] >= max_player_attempts:
                scores[model]['score'] = -math.inf

        def winner(scores: dict, models: List[str]) -> str:
            advantage_a = scores[models[0]]['score'] - scores[models[1]]['score']
            if advantage_a > 0:
                return 'model_a'
            elif advantage_a < 0:
                return 'model_b'
            return 'tie'
        
        matches.append([
            models[0],
            models[1],
            winner(scores, models),
        ])

    matches_df = pd.DataFrame(matches, columns=['model_a', 'model_b', 'winner'])
    return matches_df


def calculate_ratings(logs_path: str, bootstrap_rounds: int, max_player_attempts: int) -> pd.DataFrame:
    match_df = convert_matches_to_df(logs_path, max_player_attempts)
    np.random.seed(1)
    bootstrap_elo_lu = get_bootstrap_result(match_df, compute_mle_elo, bootstrap_rounds)

    bars = pd.DataFrame(dict(
        lower = bootstrap_elo_lu.quantile(.025),
        rating = bootstrap_elo_lu.quantile(.5),
        upper = bootstrap_elo_lu.quantile(.975),
    )).reset_index(names="model").sort_values("rating", ascending=False).round(decimals=2)
    
    return bars

    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-path", "-p", help="Path to the match logs file")
    parser.add_argument("--bootstrap-rounds", "-b", help="Number of rounds to bootstrap for confidence intervals.", type=int, default=100)
    parser.add_argument("--max-player-attempts", "-m", help="Maximum number of player attempts.", type=int, default=5)
    args = parser.parse_args()

    ratings = calculate_ratings(logs_path=args.logs_path, bootstrap_rounds=args.bootstrap_rounds, max_player_attempts=args.max_player_attempts)
    print(ratings)
