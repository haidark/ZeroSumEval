from abc import ABC, abstractmethod
from typing import Optional
import logging
import functools

from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import dspy

logger = logging.getLogger()

# Abstract class for players
class Player(ABC):
    def __init__(
        self,
        id: str,
        role: str,
        lm: dict,
        module_args: dict = {},
        optimize: bool = False,
        optimizer: str = "MIPROv2",
        optimizer_args: dict = {},
        compilation_args: dict = {},
        metric: str = "exact_match",
        dataset: Optional[str]= None,
        dataset_args: dict = {},
        max_tries: int = 10,
    ):
        from zero_sum_eval.registry import LM_REGISTRY, DATASET_REGISTRY, METRIC_REGISTRY, OPTIMIZER_REGISTRY

        self.id = id
        self.role = role
        self.optimize = optimize
        lm_args = lm["args"] if "args" in lm else {}
        self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
        self.max_tries = max_tries
        self.module = self._build_module(**module_args)
        self.module = assert_transform_module(self.module, functools.partial(backtrack_handler, max_backtracks=max_tries))
        if optimize:
            if not dataset:
                raise ValueError("A dataset must be passed for players with 'optimize = True'")
            
            self.dataset = DATASET_REGISTRY.build(dataset, **dataset_args)
            self.metric = METRIC_REGISTRY.build(metric, output_key=self.dataset.output_key)
            self.optimizer = OPTIMIZER_REGISTRY.build(optimizer, metric=self.metric, prompt_model=self.llm_model, task_model=self.llm_model, **optimizer_args)
            # Optimize
            dspy.configure(trace=[])
            with dspy.context(lm=self.llm_model):
                self.module = self.optimizer.compile(self.module, trainset=self.dataset.get_dataset(), **compilation_args)

    @abstractmethod
    def _build_module(self, **module_args):
        """
        Abstract method for building the main dspy module for the player
        
        Parameters:
        None
        
        Returns:
        dspy.Module: The module
        """
        raise NotImplementedError

    @abstractmethod
    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        raise NotImplementedError

class HumanPlayer(Player):
    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")
        return move.strip()
