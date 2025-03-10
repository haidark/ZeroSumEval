# Contributing to ZeroSumEval

Thank you for your interest in contributing to ZeroSumEval! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Adding New Games](#adding-new-games)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)


## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/ZeroSumEval.git
   cd ZeroSumEval
   ```
3. Set up the development environment:
   ```
   pip install -e .
   ```
4. Create a branch for your changes:
   ```
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. Make your changes in your feature branch
2. Add tests for your changes
3. Ensure all tests pass
4. Update documentation as needed
5. Commit your changes with clear, descriptive commit messages
6. Push your branch to your fork
7. Submit a pull request

## Pull Request Process

1. Ensure your PR includes a clear description of the changes and the purpose
2. Link any relevant issues in the PR description
3. Make sure all CI checks pass
4. Request a review from maintainers
5. Address any feedback from reviewers
6. Once approved, your PR will be merged

## Adding New Games

To add a new game to ZeroSumEval:

1. Create a new module in the `zero_sum_eval/games/` directory
2. Implement the game logic following the existing patterns
3. Create a configuration file in the `configs/` directory
4. Add tests for your game, Make sure to add a test for each of the functions extended from the GameState class. Namely:
    - `update_game`
    - `get_scores`
    - `get_next_action`
    - `is_over`
    - `player_definitions`
    - `display`
    - `export`
5. Update documentation to include your new game
6. Submit a PR with your changes

## Coding Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write clear, descriptive docstrings
- Keep functions and methods focused on a single responsibility
- Use meaningful variable and function names

## Testing

- Write unit tests for new functionality
- Ensure existing tests pass with your changes
- Run tests locally before submitting a PR:
  ```
  pytest
  ```

## Documentation

- Update documentation for any changes to the API or functionality
- Include docstrings for all public functions, classes, and methods
- Keep the README and other documentation up to date

Thank you for contributing to ZeroSumEval!
