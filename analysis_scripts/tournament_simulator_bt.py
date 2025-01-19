import math
import json
import argparse
from glob import glob

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm


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
    # if no tie, create a zero matrix
    if sum(df["winner"].isin(["tie", "tie (bothbad)"])) == 0:
        ptbl_tie = pd.DataFrame(0, index=ptbl_a_win.index, columns=ptbl_a_win.columns)
    else:
        ptbl_tie = pd.pivot_table(
            df[df["winner"].isin(["tie", "tie (bothbad)"])],
            index="model_a",
            columns="model_b",
            aggfunc="size",
            fill_value=0,
        )
        ptbl_tie = ptbl_tie + ptbl_tie.T

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
        except ValueError:
            pass
    print(f"Only used {len(rows)}/{num_round} bootstrap rounds due to samples that have zero matches for some models")
    df = pd.DataFrame(rows)
    return df[df.median().sort_values(ascending=False).index]


def convert_matches_to_df(args: argparse.Namespace) -> pd.DataFrame:

    score_to_result = {
        0.0: 'model_b',
        0.5: 'tie',
        1.0: 'model_a',
    }

    def standardize_model_names(model: str) -> str:
        for opt in ['default', 'bsfs', 'bsfsrs', 'mipro']:
            model = model.replace(f'optimized-{opt}', opt)
            
        return model
    
    matches = []
    for match_results_path in glob(f'{args.logs_path}/**/matches/*/results.json', recursive=True):
        with open(match_results_path) as f:
            result = json.load(f)
        models = list(result.keys())
        assert len(models) == 2
        matches.append([
            standardize_model_names(models[0]),
            standardize_model_names(models[1]),
            score_to_result[round(result[models[0]]['result'], 1)],
        ])

    matches_df = pd.DataFrame(matches, columns=['model_a', 'model_b', 'winner'])
    return matches_df


def main(args: argparse.Namespace) -> None:
    match_df = convert_matches_to_df(args)
    print(compute_mle_elo(match_df))

    np.random.seed(1)
    bootstrap_elo_lu = get_bootstrap_result(match_df, compute_mle_elo, args.bootstrap_rounds)

    bars = pd.DataFrame(dict(
        lower = bootstrap_elo_lu.quantile(.025),
        rating = bootstrap_elo_lu.quantile(.5),
        upper = bootstrap_elo_lu.quantile(.975),
    )).reset_index(names="model").sort_values("rating", ascending=False)
    
    print(bars)

    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-path", "-p", help="Path to the match logs file")
    parser.add_argument("--bootstrap-rounds", "-b", help="Number of rounds to bootstrap for confidence intervals.", type=int, default=100)
    args = parser.parse_args()

    main(args)
