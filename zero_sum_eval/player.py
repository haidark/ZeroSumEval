from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import logging
import functools
import os

from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import dspy

logger = logging.getLogger('ZeroSumEval')

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
        datasets: Optional[List]= None,
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
        self.module = self._build_module(roles, **module_args)
        if "module_path" in lm:
            path = lm["module_path"]
            self.module.load(path)
            logger.info(f"Loaded module from {path}")

        self.module = assert_transform_module(self.module, functools.partial(backtrack_handler, max_backtracks=max_tries))
        if optimize:
            if not datasets:
                raise ValueError("A list of datasets must be passed for players with 'optimize = True'")
            for d_conf in datasets:
                dataset = DATASET_REGISTRY.build(d_conf['dataset'], **d_conf['dataset_args'])
                metric = METRIC_REGISTRY.build(d_conf.get('metric', metric), output_key=dataset.output_key)
                optimizer = d_conf.get('optimizer', optimizer)
                optimizer_args = d_conf.get('optimizer_args', optimizer_args)
                if optimizer == "MIPROv2":
                    optimizer_args.update(prompt_model=self.llm_model, task_model=self.llm_model)
                optimizer = OPTIMIZER_REGISTRY.build(optimizer, metric=metric, **optimizer_args)
                # Optimize
                compilation_args = d_conf.get('compilation_args', compilation_args)
                dspy.configure(trace=[])
                logger.info(f"Optimizing Player:{self.id} for Role:{dataset.role} with Optimzer:TBD ...")
                with dspy.context(lm=self.llm_model):
                    self.module.module_dict[dataset.role] = optimizer.compile(self.module.module_dict[dataset.role],
                                                                            trainset=dataset.get_dataset(), 
                                                                            **compilation_args)
            os.makedirs(os.path.join(output_dir, "compiled_modules"), exist_ok=True)
            self.module.save(os.path.join(output_dir, "compiled_modules", f"{self.id}_prompts.json"))

    @abstractmethod
    def _build_module(self, roles, **module_args):
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
        dspy.Prediction: DSPy trace of the move
        """
        raise NotImplementedError

    def make_move(self, game_state):
        with dspy.context(lm=self.llm_model):
            return self._make_move(**game_state.player_inputs())

class HumanPlayer(Player):
    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")
        return move.strip()
