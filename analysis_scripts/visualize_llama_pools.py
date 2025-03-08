from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

from zero_sum_eval.calculate_ratings import calculate_ratings


matplotlib.rc('font', family='serif', serif=['Times'], size=9)
plt.rcParams.update({'figure.autolayout': True})


CHESS_POOL_PATH = "../llama_chess_pool"
DEBATE_POOL_PATH = "../debate_llama_pool"
BOOTSTRAP_ITERS = 10_000

# RGB colors from ZSE logo
COLORS = [
    (41/255, 44/255, 147/255),  # Debate
    (14/255, 140/255, 247/255),  # Chess
]

# ACL template widths in inches
TEXT_WIDTH = 3.03
LINE_WIDTH = 6.30


def preprocess_ratings(ratings: pd.DataFrame) -> pd.DataFrame:
    """Cleans and sorts the model ratings DataFrame."""

    ratings['model'] = ratings['model'].str.replace('llama-', '').str.replace('llama', '')
    ratings['parameters'] = ratings['model'].apply(lambda x: int(x.split('-')[-1][:-1]))

    return ratings.sort_values(by='parameters')


def compute_error_bars(ratings: pd.DataFrame) -> List[float]:

    return [
        ratings["rating"] - ratings["lower"],
        ratings["upper"] - ratings["rating"]
    ]

def visualize_ratings(chess_ratings: pd.DataFrame, debate_ratings: pd.DataFrame) -> None:
    """Generates a bar chart comparing chess and debate ratings."""

    chess_ratings = preprocess_ratings(chess_ratings)
    debate_ratings = preprocess_ratings(debate_ratings)
    
    models = chess_ratings['model']
    x = np.arange(len(models))
    width = 0.35 
    y_start = -500
    
    chess_errors = compute_error_bars(chess_ratings)
    debate_errors = compute_error_bars(debate_ratings)
    
    plt.figure(figsize=(TEXT_WIDTH, 2.5))
    plt.bar(
        x, debate_ratings["rating"] - y_start, width,
        bottom=y_start, yerr=debate_errors, capsize=2,
        color=COLORS[0], alpha=0.8, edgecolor='black',
        label='Debate', zorder=3
    )
    plt.bar(
        x + width, chess_ratings["rating"] - y_start, width,
        bottom=y_start, yerr=chess_errors, capsize=2,
        color=COLORS[1], alpha=0.8, edgecolor='black',
        label='Chess', zorder=3
    )
    
    plt.xticks(x + width/2, models)
    plt.title("Ratings across various Llama 3 sizes")
    plt.ylabel("Rating")
    plt.xlabel("Llama model")
    plt.legend()
    plt.grid(ls='--', zorder=0)

    plt.savefig('llama_chess_debate_results.pdf', bbox_inches='tight')

def main():
    chess_ratings = calculate_ratings(CHESS_POOL_PATH, BOOTSTRAP_ITERS, 1)
    debate_ratings = calculate_ratings(DEBATE_POOL_PATH, BOOTSTRAP_ITERS, 1)
    visualize_ratings(chess_ratings, debate_ratings)

if __name__ == "__main__":
    main()
