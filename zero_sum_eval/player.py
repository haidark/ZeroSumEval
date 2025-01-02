from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import logging
import functools
import os
import dspy

from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from zero_sum_eval.checkpointing import save_checkpoint, load_checkpoint, get_cached_module_path
from zero_sum_eval.types import Role

# Disable debugging logs of litellm
import litellm
litellm._logging._disable_debugging()

logger = logging.getLogger()

# Abstract class for players
class Player(ABC):
    def __init__(
        self,
        id: str,
        roles: Union[List[Role], List[str]],
        lm: dict,
        optimizer: str = "MIPROv2",
        optimizer_args: dict = {},
        compilation_args: dict = {},
        metric: str = "exact_match",
        max_tries: int = 10,
        output_dir: str = "",
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
    ):
        from zero_sum_eval.registry import LM_REGISTRY, DATASET_REGISTRY, METRIC_REGISTRY, OPTIMIZER_REGISTRY

        self.id = id
        lm_args = lm["args"] if "args" in lm else {}
        if "type" not in lm:
            self.llm_model = dspy.LM(model=lm["model"], **lm_args)
        else:
            self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
        self.max_tries = max_tries

        self.roles: List[str] = [role if isinstance(role, str) else role["name"] for role in roles]
        self.module_dict = self.init_role_module_dict()

        # Add backtracking to all modules
        for role in self.module_dict:
            self.module_dict[role] = assert_transform_module(self.module_dict[role], functools.partial(backtrack_handler, max_backtracks=max_tries))
        
        # Prioritize the optimizer set in the llm config over the one set in the player config
        if "optimizer" in lm:
            optimizer = lm["optimizer"]
            optimizer_args = lm.get("optimizer_args", {})
            compilation_args = lm.get("compilation_args", {})
        
        # TODO: add support for different optimizers for different roles, right now it's just one optimizer for all roles   
        if optimizer == "MIPROv2":
            optimizer_args.update(prompt_model=self.llm_model, task_model=self.llm_model)

        for role in roles:
            # Option to either only list the role names in the config or provide the full role object with optimization details
            if isinstance(role, str):
                role = Role(name=role)
            else:
                role = Role(**role)
            if role.name not in self.module_dict:
                raise ValueError(f"Role {role.name} not found in module_dict")
            
            # Load the module from checkpoint if provided for the role (does not preclude further optimization)
            if role.name in lm.get("module_paths", {}):
                path = lm["module_paths"][role.name]
                self.module_dict[role.name] = load_checkpoint(
                    module=self.module_dict[role.name],
                    module_path=path
                )
                logger.info(f"Loaded module from {path}")

            # prioritize the optimize flag in the lm config over the one in the role config
            if lm.get("optimize", role.optimize):
                if not role.dataset:
                    raise ValueError("A dataset must be passed for players with 'optimize = True'")
                
                if use_cache:
                    cached_module_path = get_cached_module_path(
                        model=lm["model"],
                        role=role.name, 
                        optimizer=optimizer, 
                        dataset=role.dataset, 
                        cache_dir=cache_dir,
                        optimizer_args=optimizer_args,
                        compilation_args=compilation_args
                    )

                    try:
                        cached_module = load_checkpoint(
                            module=self.module_dict[role.name],
                            module_path=cached_module_path
                        )
                        self.module_dict[role.name] = cached_module
                        logger.info(f"Loaded cached module for Role: {role.name}")
                        continue
                    except FileNotFoundError:
                        logger.info(f"No cached module found for Role: {role.name}")
                
                # Load the dataset and metric of this particular role
                dataset = DATASET_REGISTRY.build(role.dataset, **role.dataset_args)
                metric = METRIC_REGISTRY.build(role.metric, output_key=dataset.output_key)

                # Compile the module
                opt = OPTIMIZER_REGISTRY.build(optimizer, metric=metric, **optimizer_args)
                dspy.configure(trace=[])
                logger.info(f"Optimizing Player: {self.id} for Role: {role.name} with Optimzer: {opt}...")
                with dspy.context(lm=self.llm_model):
                    self.module_dict[role.name] = opt.compile(self.module_dict[role.name], trainset=dataset.get_dataset(), **compilation_args)

                if use_cache:
                    save_checkpoint(
                        module=self.module_dict[role.name],
                        module_path=cached_module_path
                    )
                    logger.info(f"Cached compiled module for Role: {role.name}")


    def make_move(self, game_state):
        """
        Make a move based on the game state.
        
        Parameters:
        game_state (GameState): The current game state

        Returns:
        output: The move to make
        trace: The trace of the move
        """
        inputs = game_state.player_inputs()
        role = inputs.get("role", None)
        if role not in self.roles:
            raise ValueError(f"Role {role} of game state not found in player roles {self.roles}")
    
        with dspy.context(lm=self.llm_model):
            trace = self.module_dict[role](**inputs)

        # the final value in the prediction is assumed to be the output of the module
        output = trace.items()[-1][1]

        return output, trace

    
    @abstractmethod
    def init_role_module_dict(self) -> Dict[str, dspy.Module]:
        """
        Abstract method for getting the role-module dictionary for the Player
        
        Parameters:
        None
        
        Returns:
        dict: The role-module dictionary
        """
        raise NotImplementedError

class HumanPlayer(Player):
    def make_move(self, game_state):
        move = input(f"{game_state} enter your move: ")
        return move.strip()
