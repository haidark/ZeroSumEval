<p align="center">
  <img align="center" src="logo.png" width="380px" />
</p>
<p align="left">

ZeroSumEval is a framework for evaluating the reasoning abilities of Large Language Models (LLMs) using zero-sum multiplayer simulations. ZSEval uses [DSPy](https://github.com/stanfordnlp/dspy) for automatic prompt optimization to ensure evaluations are fair.

<!-- omit in toc -->
## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Games](#games)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Overview

ZeroSumEval aims to create a robust evaluation framework for LLMs using competitive scenarios. Instead of fixed evaluation benchmarks or model-based judging, ZSEval uses multiplayer simulations/games with clear win conditions to pit models against each other. 

The framework tests various model capabilities, including knowledge, reasoning, and planning. In addition, ZSEval uses [DSPy](https://github.com/stanfordnlp/dspy) optimization to test the self-improvement capability of models and ensure the competition between models is fair.

The eval suite consists of a growing number of simulations, including text-based challenges, board games, and Capture The Flag (CTF) competitions.

Key features:
- One-click evals on the existing suite of games
- Easily extendable abstractions for new game implementations
- Integration with DSPy for automated prompt optimization
- Comprehensive logging and analysis tools

## Project Structure

The project is organized as follows:

- `zero_sum_eval/`: Main package containing the core framework
  - `games/`: Individual game implementations
  - `managers/`: Game and match management classes
- `data/`: Game-specific data and examples
- `configs/`: Configuration files for different games and scenarios
- `run_game.py`: Script to run individual games
- `run_matches.py`: Script to run a series of matches

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/ZeroSumEval.git
   cd ZeroSumEval
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run a game:

```
python run_game.py -c configs/chess.yaml
```

To run a series of matches:
```
python run_matches.py -c configs/mathquiz.yaml
```

## Games

ZeroSumEval currently supports the following games:

1. Chess
2. Math Quiz
3. Gandalf (Password Guessing)
4. PyJail (Capture The Flag)

Each game is implemented as a separate module in the `zero_sum_eval/games/` directory.

## Configuration

Game configurations are defined in YAML files located in the `configs/` directory. These files specify:

- Logging settings
- Game parameters
- Player configurations
- LLM settings

<details>
<summary>Example Configuration (chess.yaml):</summary>

```yaml
logging:
  output_dir: ../output/chess_game
manager:
  args:
    max_rounds: 200
    win_conditions: 
      - Checkmate
    draw_conditions:
      - Stalemate
      - ThreefoldRepetition
      - FiftyMoveRule
      - InsufficientMaterial
game:
  name: chess
  players:
    - name: chess_player
      args:
        id: gpt4 white
        roles: 
          - White
        optimize: false
        dataset: chess_dataset
        dataset_args:
          filename: ./data/chess/stockfish_examples.jsonl
          role: White
        optimizer: MIPROv2
        optimizer_args:
          num_candidates: 5
          minibatch_size: 20
          minibatch_full_eval_steps: 10
        compilation_args:
          max_bootstrapped_demos: 1
          max_labeled_demos: 1
        metric: chess_move_validation_metric
        lm:
          type: AzureOpenAI
          args:
            api_base: https://allam-swn-gpt-01.openai.azure.com/
            api_version: 2023-07-01-preview
            deployment_id: gpt-4o-900ptu
            max_tokens: 800
            temperature: 0.8
            top_p: 0.95
            frequency_penalty: 0
            presence_penalty: 0
        max_tries: 5
    - name: chess_player
      args:
        id: gpt4 black
        roles: 
          - Black
        optimize: false
        dataset: chess_dataset
        dataset_args:
          filename: ./data/chess/stockfish_examples.jsonl
          role: Black
        optimizer: MIPROv2
        optimizer_args:
          num_candidates: 5
          minibatch_size: 20
          minibatch_full_eval_steps: 10
        compilation_args:
          max_bootstrapped_demos: 1
          max_labeled_demos: 1
        metric: chess_move_validation_metric
        lm:
          type: AzureOpenAI
          args:
            api_base: https://allam-swn-gpt-01.openai.azure.com/
            api_version: 2023-07-01-preview
            deployment_id: gpt-4o-900ptu
            max_tokens: 800
            temperature: 0.8
            top_p: 0.95
            frequency_penalty: 0
            presence_penalty: 0
        max_tries: 5
```

</details>


## Contributing

Contributions to ZeroSumEval are welcome! Please open a pull request

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
