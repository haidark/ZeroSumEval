# Zero Sum Eval (ZSEval)

The goal of this work is to understand how two player games/problems/challenges can be used the evaluate/improve the reasoning ability of LLMs

# High level Plan

## Current Plan

1. Define the framework for two player games: including the components, interactions, and overall flow
    1. Abstractions that captures the players in the games, win conditions, and interactions between players
        1. Player: captures the essential parts of a player in the game, including the LLM driving the player and abstract methods which prepare the player to play its role in the game
        2. GameEnvironment: captures the setup of the game, controls information provided to each player, the progress of each player in the game, tracks tries/retries, win/loss conditions, ends the game
        
        ### UML DIagram
        
        ```html
        +-------------------+          +--------------------+
        |   GameManager     |          |       Player       |
        +-------------------+          +--------------------+
        | - players         |1        n| - id               |
        | - game_state      |<-------->| - llm_model        |
        | - max_turns       |          | - name             |
        | - current_turn    |          +--------------------+
        | - win_conditions  |          | + initlaize()      |
        +-------------------+          | + make_move()      |
        | + initialize()    |          +--------------------+
        | + update_state()  |       
        | + check_win()     |       
        | + run_game()      |
        +-------------------+
        ```
        
2. Implement DSPy for prompt optimization (Haidar)
3. Implement simple CTF game FuzzMe (Colton)
4. Implement text based two player game
    1. mathquiz
    2. codequiz 
5. Implement chess and other board games
6. First round of eval on 3-5 current models on the implemented games
7. Analyze results (end of July)
8. Implement tool usage
9. Implement complex CTF games
10. Iterate on the games, design of framework.
11. Harden framework and generalize it
12. Second round of evals on 5-7 current models.
13. Analyze results
14. Write plan to open source
15. Write paper

### Initial plan (outdated)

1. Develop an understanding of Capture the Flag
    1. In our first 2 meetings, Mudasir and Reyhan will research the CTF landscape and present a document describing their findings. Some aspects of interest to this project:
        1. The CTF format
        2. How do humans compete in CTF
        3. Sample CTF problems and solutions
        4. Software required for CTF problems/competitions
        5. CTF problem/competition repositories that can be mined for data
        6. a taxonomy of CTF problems/competitions
2. Survey the published work around LLMs applied to CTF
    1. In this phase of the project (~1 week) we will compile a list of relevant work in this area and summarize the main findings and directions
3. Create a LLM evaluation benchmark based on CTF
    1. Our first publishable milestone
    2. Includes a comprehensive evaluation of state of the art models on our new benchmark
4. Create training data for LLMs based on CTF

# Two Player LLM Evaluation

Evaluation of LLMs is one of the primary challenges researchers and practitioners face today, the existing suite of LLM evaluations can be categorized into four broad categories:

1. Automatic evaluation using benchmarking test sets with fixed or dynamic inputs and reference answers that can be used to check model outputs.
2. Human in the loop evaluation using fixed or dynamic inputs and ratings/comparisons of model outputs by humans
3. Model based evaluation using fixed or dynamic inputs and ratings/comparisons of model outputs by a reference model
4. Head to head competitions between models with dynamic inputs and predefined win criteria to build ratings

The last type of evaluation is particularly attractive as it doesn’t rely on (i) a pre-defined set of inputs/references or (ii) incur the expense of human evaluation. One can determine ELO ratings based on wins and losses.

Let’s focus on this type of evaluation in the context of CTF

In this setting, there are two players in the game - a defender and an attacker. The defender creates a CTF challenge and proves the challenge is solvable. The attacker examines the CTF challenge and must retrieve the hidden flag. The defender and attacker are limited in the number of attempts to generate a valid challenge and solve the challenge respectively.

## A proof of concept: pyjail defense & attack

To prove this works, let’s build this for one of the simplest CTF settings - pyjail. Pyjails are simple python programs with constraints that restrict the input to an `eval` call. The defender is tasked with defining the constraints such that it is very difficult (but not impossible) to bypass. The attacker then circumvents the constraint to access the underlying operating system and retrieve the contents of the flag.

The following components are required:

- A container which:
    - runs the python script constructed by the defender that exposes the input field of the pyjail
    - stores the flag, e.g. in `flag.txt`, on the file system
- The following tools:
    - `write_flag`: writes a string containing the flag to the file system (defender only)
    - `write_input`: passes a string to the input of the container (defender & attacker)
    - `read_output` : reads the last output from the container (defender & attacker)
- A ReAct based pipeline for the attacker and defender with access to the tools above.

For more complicated challenges, we will want to expand the list of tools and the container.

## Defender

Here is an outline of the Defender pipeline.

- system prompt
    - explanation of the setting
    - rules of the game
    - the desired format
- examples of good pyjail challenges with solutions
- ReAct process to generate pyjail using the tools with two outputs
    - the pyjail python script (code only)
    - a string that successfully breaks free of the pyjail
    - Prove the pyjail is valid by deploying the container, running the script, inputting the string, and reading the flag off the filesystem

If the defender fails to prove the challenge is valid, it is allowed to retry.

## Attacker

Here is an outline of the Attacker pipeline

- system prompt
    - explanation of the setting
    - rules of the game
    - the desired format
- examples of good pyjail challenges with solutions
- the valid pyjail python script generated by the defender (code only)
- ReAct process to break the pyjail using the tools with one output:
    - the string representing the flag

If the attacker fails to retrieve the flag, it is allowed to retry.

## The container and setup

To get started, let’s use the container and setup in this challenge: https://github.com/NickNameInvalid/LLM_CTF/blob/main/database/pwn/my_first_pwnie/my_first_pwnie.py

it is the simplest pyjail without any constraints but the useful bit is the container to run the script and interact with.
