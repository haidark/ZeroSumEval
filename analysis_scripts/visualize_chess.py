import json
from glob import glob
import os
import argparse
from typing import Literal, Union, List, Tuple
from collections import defaultdict

import tiktoken
from transformers import AutoTokenizer
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import chess
import chess.engine


"""
Sample usage:
'''
python visualize_chess.py \
    --match_dir="path" \
    --hf_token="hf_yourtoken" \
    --stockfish_path="path" \
    --output_dir="path"
'''
"""


font = {'family' : 'serif',
        'serif':['Times'],
        'size'   : 9}

matplotlib.rc('font', **font)
plt.set_cmap('ocean')
plt.rcParams.update({'figure.autolayout': True})


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_dir", type=str, required=True, help="Directory with chess match history.")
    parser.add_argument("--hf_token", type=str, required=True, help="HuggingFace token to load tokenizers.")
    parser.add_argument("--stockfish_path", type=str, required=True, help="Path to locally installed StockFish from https://stockfishchess.org/download/")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory where visualizations will be saved.")
    return parser.parse_args()


class ChessVisualizer:
    def __init__(self, args: argparse.Namespace) -> None:

        self.match_dir = args.match_dir
        self.hf_token = args.hf_token
        self.stockfish_path = args.stockfish_path
        self.output_dir = args.output_dir
        self.cmap = plt.get_cmap('ocean')
        self.linewidth = 5.5


    def load_tokenizers(self) -> dict:
        mistral_tok = AutoTokenizer.from_pretrained('mistralai/Mistral-Large-Instruct-2407', token=self.hf_token)
        llama_tok = AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3.1-70B-Instruct', token=self.hf_token)
        gpt_tok = tiktoken.get_encoding('o200k_base')

        tokenizers = {
            'mistral-large': mistral_tok,
            'llama3.1-70b': llama_tok,
            'gpt-4o': gpt_tok,
            'claude-3-5-sonnet': gpt_tok, #Claude tokenizer is not public.
        }

        return tokenizers


    def read_matches(self):

        matches = []
        for match_log_path in glob(f'{self.match_dir}/matches/*/turns.jsonl'):

            match_log_path = os.path.normpath(match_log_path)
            candidates = match_log_path.split(os.sep)[-2]
            white, _, black, _ = candidates.split('_')

            with open(match_log_path) as f:
                turns = [json.loads(turn) for turn in f]

            def split_model_opt(model: str) -> Tuple[str, str]:
                """splits model+optimizer name to (model, optimizer)."""

                if model.endswith('-default'):
                    return model.replace('-default', ''), 'Default'
                elif model.endswith('-optimized'):
                    return model.replace('-optimized', ''), 'Optimized BSFS'
                elif model.endswith('-optimized-bsfs'):
                    return model.replace('-optimized-bsfs', ''), 'Optimized BSFS'
                elif model.endswith('-optimized-mipro'):
                    return model.replace('-optimized-mipro', ''), 'Optimized MIPRO'
                else:
                    raise ValueError(f'Unexpected model name {model}.')
                
            white_model, white_opt = split_model_opt(white)
            black_model, black_opt = split_model_opt(black)

            try:
                matches.append({
                    'white_model': white_model,
                    'white_opt': white_opt,
                    'black_model': black_model,
                    'black_opt': black_opt,
                    'board_states': [turn['environment']['fen'] for turn in turns],
                    'model_reasoning': [turn['context']['last_trace']['rationale'] for turn in turns],
                })
            except KeyError as e:
                print(f'Encountered {e} KeyError in {match_log_path}.')

        return matches


    def visualize(self):
        self.matches = self.read_matches()
        self.visualize_reasoning_dist(metric='words')
        self.visualize_evaluation_trend(depth=10)
        # self.visualize_correct_planning_steps(depth=10)


    def visualize_reasoning_dist(self, metric: Union[Literal['tokens'], Literal['words']]) -> None:
        """Plot a histogram of CoT tokens/words used per move for each model."""

        if metric == 'tokens':
            tokenizers = self.load_tokenizers()
            metric_func = lambda model, reasoning: len(tokenizers[model].encode(reasoning))

        elif metric == 'words':
            metric_func = lambda model, reasoning: len(reasoning.split())

        else:
            raise ValueError("`metric` should either be 'tokens' or 'words'")

        reasoning_lengths = defaultdict(lambda: defaultdict(list))
        for match in self.matches:
            for i, reasoning in enumerate(match['model_reasoning']):
                model = [match['white_model'], match['black_model']][i%2]
                opt = [match['white_opt'], match['black_opt']][i%2]
                reasoning_lengths[model][opt].append(metric_func(model, reasoning))

        # Currently hard-coded for four models in 2x2 grid
        figsize = (self.linewidth, self.linewidth *.6)
        fig, axs = plt.subplots(2, 2, sharex=True, sharey=True, layout='constrained', figsize=figsize)
        max_len = max(max(v) for v in reasoning_lengths.values())
        for i, (model, opt_lengths) in enumerate(sorted(reasoning_lengths.items())):
            plt.sca(axs[i//2][i%2])
            for j, (opt, lengths) in enumerate(sorted(opt_lengths.items())):
                plt.hist(
                    lengths,
                    bins=25,
                    range=(0, 400),
                    zorder=3,
                    alpha=0.6,
                    color=self.cmap(0.3*j),
                    edgecolor='black',
                    label=opt,
                )
            plt.title(model)
            plt.grid()
            if i == 3:
                plt.legend()

        # Remove ticks from inner subplots
        for i in range(2):
            for j in range(2):
                if i < 1:  # Remove x-ticks for the first row
                    axs[i, j].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
                if j > 0:  # Remove y-ticks for the second column
                    axs[i, j].tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

        fig.suptitle(f'Chess Reasoning {metric.title()} Distribution')
        fig.text(0.5, -0.01, metric.title(), ha='center', va='center', fontsize=10)
        fig.text(-0.01, 0.5, 'Frequency', ha='center', va='center', rotation='vertical', fontsize=10)

        for file_type in ['png', 'pdf']:
            plt.savefig(
                os.path.join(self.output_dir, f'chess_reasoning_{metric}_dist.{file_type}'),
                dpi=300, 
                bbox_inches='tight',
            )

        plt.close(fig)


    def visualize_evaluation_trend(self, depth: int=15, mate_score: int=2_000) -> None:

        # Plot eval trends
        model_match_scores = defaultdict(lambda: defaultdict(list))
        model_match_scores2 = defaultdict(list)
        model_set = set()
        engine = chess.engine.SimpleEngine.popen_uci(args.stockfish_path)

        initial_baord_state = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        for match in tqdm(self.matches, desc='Generating stockfish evals'):
            scores = []
            for state in [initial_baord_state] + match['board_states']:
                board = chess.Board(state)
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                score = info['score'].white().score(mate_score=mate_score)
                score /= 100 # Convert centi-pawns advantage evaluation to pawns
                scores.append(score)
            model_match_scores[match['white_model']][match['black_model']].append(scores)
            model_match_scores2[(
                match['white_model'],
                match['white_opt'],
                match['black_model'],
                match['black_opt'],
            )].append(scores)
            model_set.add(match['white_model'])
            model_set.add(match['black_model'])

        models = list(sorted(model_set))

        # Hard-coded for four models
        fig, axs = plt.subplots(4, 4, figsize=(12, 12), sharex=True, sharey=True)

        for i, white_model in enumerate(models):
            for j, black_model in enumerate(models):
                ax = axs[j, i]
                matches = model_match_scores[white_model][black_model]
                
                if matches:
                    for match in matches:
                        ax.plot(match, alpha=0.6)
                
                ax.set_title(f"{white_model} vs {black_model}", fontsize=10)
                ax.grid(True)

                # Show tick labels only for leftmost column and bottom row
                if i == 0:
                    ax.tick_params(axis='y', which='both', labelleft=True)
                else:
                    ax.tick_params(axis='y', which='both', labelleft=False)
                
                if j == 3:
                    ax.tick_params(axis='x', which='both', labelbottom=True)
                else:
                    ax.tick_params(axis='x', which='both', labelbottom=False)

        # Set common labels for all subplots
        for ax in axs.flat:
            ax.set(xlabel='', ylabel='')

        # Add row labels (Black models)
        for j, black_model in enumerate(models):
            axs[j, 0].set_ylabel(f"{black_model} (Black)", rotation=90, labelpad=20, fontsize=12, va='center')

        # Add column labels (White models)
        for i, white_model in enumerate(models):
            axs[-1, i].set_xlabel(f"{white_model} (White)", fontsize=12, labelpad=10)

        fig.suptitle('Chess Position Evaluation Trends', fontsize=16, y=0.98)

        # Adjust layout to prevent overlapping
        plt.tight_layout(rect=[0.03, 0.03, 0.97, 0.97])

        # Add global x and y axis labels
        fig.text(0.5, 0.01, 'Turn', ha='center', va='center', fontsize=14)
        fig.text(0.01, 0.5, 'Position evaluation (pawns)', ha='center', va='center', rotation='vertical', fontsize=14)

        for file_type in ['png', 'pdf']:
            plt.savefig(
                os.path.join(self.output_dir, f'chess_position_eval_trend.{file_type}'),
                dpi=300, 
                bbox_inches='tight',
            )

        plt.close(fig)

        # Plot eval deltas
        eval_deltas = defaultdict(lambda: defaultdict(list))
        for (white_model, white_opt, black_model, black_opt), matches in model_match_scores2.items():
            for match_scores in matches:
                for i in range(1, len(match_scores)):
                    # Flipped order as state 0 is the initial board state before any move.
                    model, opt, sign = [
                        (black_model, black_opt, -1),
                        (white_model, white_opt, +1)
                    ][i%2]
                    eval_deltas[model][opt].append(sign * (match_scores[i] - match_scores[i-1]))

        # Currently hard-coded for four models in 2x2 grid
        figsize = (self.linewidth, self.linewidth *.6)
        fig, axs = plt.subplots(2, 2, sharex=True, sharey=True, figsize=figsize)
        for i, (model, opt_deltas) in enumerate(eval_deltas.items()):
            plt.sca(axs[i//2][i%2])
            plt.title(model)
            plt.grid()
            for j, (opt, deltas) in enumerate(opt_deltas.items()):
                plt.hist(
                    deltas,
                    bins=40,
                    range=(-10, +2),
                    zorder=3,
                    alpha=0.6,
                    edgecolor='black',
                    label=opt,
                    color=self.cmap(0.3*j),
                )
            if i == 3:
                plt.legend()
            
        fig.text(0.5, -0.01, 'Move evaluation change (pawn)', ha='center', va='center', fontsize=10)
        fig.text(-0.01, 0.5, 'Frequency', ha='center', va='center', rotation='vertical', fontsize=10)
        fig.suptitle(f'Chess Evaluation Change Distribution')

        for i in range(2):
            for j in range(2):
                if i < 1:  # Remove x-ticks for the first row
                    axs[i, j].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
                if j > 0:  # Remove y-ticks for the second column
                    axs[i, j].tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

        for file_type in ['png', 'pdf']:
            plt.savefig(
                os.path.join(self.output_dir, f'chess_eval_delta_dist.{file_type}'),
                dpi=300, 
                bbox_inches='tight',
            )

        plt.close(fig)
        engine.quit()


    def visualize_correct_planning_steps(
        self,
        depth: int=20,
        mate_score: int=2_000,
        correct_threshold: float=-0.3,
    ) -> None:
        """
        Plots the proportion of model moves that result in an evaluation difference
        that do not exceed the `correct_threshold` for a given stockfish depth.
        """

        model_opt_correct_tally = defaultdict(lambda: defaultdict(list))
        engine = chess.engine.SimpleEngine.popen_uci(args.stockfish_path)

        initial_baord_state = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        models = set()
        for match in tqdm(self.matches, desc='Calculating stockfish evals'):
            scores = []
            for state in [initial_baord_state] + match['board_states']:
                board = chess.Board(state)
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                score = info['score'].white().score(mate_score=mate_score)
                score /= 100 # Convert centi-pawns advantage evaluation to pawns
                scores.append(score)
            
            for i in range(11, len(scores)):
                # Flipped order as state 0 is the initial board state before any move.
                model, opt, sign = [
                    (match['black_model'], match['black_opt'], -1),
                    (match['white_model'], match['white_opt'], +1),
                ][i%2]
                models.add(model)
                eval_delta = sign * (scores[i] - scores[i-1])
                model_opt_correct_tally[opt][model].append(eval_delta >= correct_threshold)

        models = sorted(list(models))
        x = np.arange(len(models))  # the label locations
        width = 0.25  # the width of the bars
        multiplier = 0

        figsize = (self.linewidth * 0.6, self.linewidth * 0.5)
        fig, ax = plt.subplots(layout='constrained', figsize=figsize)

        for i, (opt, model_accs) in enumerate(sorted(model_opt_correct_tally.items())):
            y = np.array([
                100 * sum(model_accs[m])/len(model_accs[m]) if model_accs[m] else 0
                for m in models
            ])
            offset = width * multiplier
            ax.bar(x + offset, y, width, label=opt, color=self.cmap(0.3*i), zorder=3, alpha=0.6, edgecolor='black')
            multiplier += 1

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_xticks(x + width, models)
       
        plt.grid()
        plt.xlabel('Model')
        plt.ylabel('Correct percentage')
        plt.title('Chess Planning Ability')
        plt.legend()

        for file_type in ['png', 'pdf']:
            plt.savefig(
                os.path.join(self.output_dir, f'correct_plans.{file_type}'),
                dpi=300, 
                bbox_inches='tight',
            )

        plt.close()
        engine.quit()
                

if __name__=='__main__':
    args = get_args()
    CV = ChessVisualizer(args)
    CV.visualize()