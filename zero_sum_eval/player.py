from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import logging
import functools
import os

from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import dspy

logger = logging.getLogger()

# Abstract class for players
class Player(ABC):
    def __init__(
        self,
        id: str,
        roles: List[str],
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
        output_dir: str = "",
    ):
        from zero_sum_eval.registry import LM_REGISTRY, DATASET_REGISTRY, METRIC_REGISTRY, OPTIMIZER_REGISTRY

        self.id = id
        self.roles = roles
        self.optimize = optimize
        lm_args = lm["args"] if "args" in lm else {}
        self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
        self.max_tries = max_tries
        self.module = self._build_module(**module_args)
        if "module_paths" in lm:
            for role, path in lm["module_paths"].items():
                if role in self.roles:
                    self.module.load(path)
                    logger.info(f"Loaded module for role {role} from {path}")

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
                print(output_dir)
                os.makedirs(os.path.join(output_dir, "compiled_modules"), exist_ok=True)
                self.module.save(os.path.join(output_dir, "compiled_modules", f"{self.id}_prompts.json"))

    @abstractmethod
    def _build_module(self, **module_args):
        """
        Abstract method for building the main dspy module for the Player
        
        Parameters:
        None
        
        Returns:
        dspy.Module: The module
        """
        raise NotImplementedError

    @abstractmethod
    def _make_move(self, game_state) -> Tuple[str, dspy.Prediction]:
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (dict): The current state of the game
        
        Returns:
        dict: The move made by the player
        """
        raise NotImplementedError

    def make_move(self, game_state):
        with dspy.context(lm=self.llm_model):
            return self._make_move(**game_state.player_inputs())

class HumanPlayer(Player):
    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")
        return move.strip()
