from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Type, Union
import logging
import functools
from dataclasses import dataclass
import dspy
import time
from dspy.primitives import assert_transform_module, backtrack_handler
from zero_sum_eval.utils.checkpointing import save_checkpoint, load_checkpoint, get_cached_module_path
from zero_sum_eval.utils.types import Action, ActionConfig, Move

# Disable debugging logs of litellm
import litellm
litellm._logging._disable_debugging()
logger = logging.getLogger()


# Abstract class for players
class Player(ABC):
    def __init__(
        self,
        id: str,
        actions: Union[List[ActionConfig], List[str]],
        lm: dict,
        player_key: str,
        optimizer: str = "MIPROv2",
        optimizer_args: dict = {},
        compilation_args: dict = {},
        metric: str = "exact_match",
        max_tries: int = 10,
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
    ):
        from zero_sum_eval.core.registry import LM_REGISTRY, DATASET_REGISTRY, METRIC_REGISTRY, OPTIMIZER_REGISTRY

        self.player_key = player_key

        self.id = id
        lm_args = lm["args"] if "args" in lm else {}
        if "type" not in lm:
            self.llm_model = dspy.LM(model=lm["model"], **lm_args)
        else:
            self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
        self.max_tries = max_tries

        # initialize the actions
        self.actions: List[ActionConfig] = []
        for action in actions:
            if isinstance(action, str):
                self.actions.append(ActionConfig(name=action))
            elif isinstance(action, dict):
                self.actions.append(ActionConfig(**action))
            else:
                self.actions.append(action)
        
        self.action_names: List[str] = [action if isinstance(action, str) else action.name for action in self.actions]
        self.action_fn_dict = self.init_actions()

        # Add backtracking to all modules
        for action in self.action_fn_dict:
            if isinstance(self.action_fn_dict[action], dspy.Module):
                self.action_fn_dict[action] = assert_transform_module(self.action_fn_dict[action], functools.partial(backtrack_handler, max_backtracks=max_tries))
        
        # Prioritize the optimizer set in the llm config over the one set in the player config
        if "optimizer" in lm:
            optimizer = lm["optimizer"]
            optimizer_args = lm.get("optimizer_args", {})
            compilation_args = lm.get("compilation_args", {})
        
        # TODO: add support for different optimizers for different actions, right now it's just one optimizer for all actions   
        if optimizer == "MIPROv2":
            optimizer_args.update(prompt_model=self.llm_model, task_model=self.llm_model)

        for action in self.actions:
            # Option to either only list the action names in the config or provide the full action object with optimization details
            if action.name not in self.action_fn_dict:
                raise ValueError(f"Action {action.name} not found in module_dict")
            
            # Load the module from checkpoint if provided for the action (does not preclude further optimization)
            if action.name in lm.get("module_paths", {}) and isinstance(self.action_fn_dict[action.name], dspy.Module):
                path = lm["module_paths"][action.name]
                self.action_fn_dict[action.name] = load_checkpoint(
                    module=self.action_fn_dict[action.name],
                    module_path=path
                )
                logger.info(f"Loaded module from {path}")

            # prioritize the optimize flag in the lm config over the one in the action config
            if lm.get("optimize", action.optimize) and isinstance(self.action_fn_dict[action.name], dspy.Module):
                if not action.dataset:
                    raise ValueError("A dataset must be passed for players with 'optimize = True'")
                
                if use_cache:
                    cached_module_path = get_cached_module_path(
                        model=lm["model"],
                        action=action.name, 
                        optimizer=optimizer, 
                        dataset=action.dataset, 
                        cache_dir=cache_dir,
                        optimizer_args=optimizer_args,
                        compilation_args=compilation_args
                    )

                    try:
                        cached_module = load_checkpoint(
                            module=self.action_fn_dict[action.name],
                            module_path=cached_module_path
                        )
                        self.action_fn_dict[action.name] = cached_module
                        logger.info(f"Loaded cached module for Action: {action.name}")
                        continue
                    except FileNotFoundError:
                        logger.info(f"No cached module found for Action: {action.name}")
                
                # Load the dataset and metric of this particular action
                dataset = DATASET_REGISTRY.build(action.dataset, **action.dataset_args)
                metric = METRIC_REGISTRY.build(action.metric, output_key=dataset.output_key)

                # Compile the module
                opt = OPTIMIZER_REGISTRY.build(optimizer, metric=metric, **optimizer_args)
                dspy.configure(trace=[])
                logger.info(f"Optimizing Player: {self.id} for Action: {action.name} with Optimzer: {opt}...")
                with dspy.context(lm=self.llm_model):
                    self.action_fn_dict[action.name] = opt.compile(self.action_fn_dict[action.name], trainset=dataset.get_dataset(), **compilation_args)

                if use_cache:
                    save_checkpoint(
                        module=self.action_fn_dict[action.name],
                        module_path=cached_module_path
                    )
                    logger.info(f"Cached compiled module for Action: {action.name}")

    
    def act(self, action: Action) -> Move:
        if isinstance(self.action_fn_dict[action.name], dspy.Module):
            start_time = time.time()
            with dspy.context(lm=self.llm_model):
                trace = self.action_fn_dict[action.name](**action.inputs)
            output = trace.items()[-1][1]
            return Move(value=output, time=time.time() - start_time, trace=trace)
        else:
            start_time = time.time()
            output = self.action_fn_dict[action.name](**action.inputs)
            return Move(value=output, time=time.time() - start_time, trace=None)

    @abstractmethod
    def init_actions(self) -> Dict[str, Callable]:
        """
        Abstract method for getting the action-function dictionary for the Player
        
        Parameters:
        None
        
        Returns:
        dict: The action-function dictionary
        """
        raise NotImplementedError


@dataclass
class PlayerDefinition:
    player_key: str
    actions: List[str]
    default_player_class: Type[Player]
    optional: bool = False

