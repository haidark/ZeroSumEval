from typing import Optional

from zero_sum_eval.player import Player
from zero_sum_eval.game_state import GameState
from zero_sum_eval.dataset import Dataset
import inspect

from collections import defaultdict
from dsp.modules.lm import LM
from dspy import Module
from dspy.teleprompt import Teleprompter


class Registry:
    def __init__(self, registry_name: str, class_type) -> None:
        self.registry_name = registry_name
        self.class_type = class_type
        self._classes_dict = {}

    def register(self, name: Optional[str] = None):
        def _register(cls):
            assert issubclass(
                cls, self.class_type
            ), f'Cannot register class "{cls.__name__}" in "{self.registry_name}". Registered classes in this registry must extend "{self.class_type}"'
            if name is not None:
                key = name
            else:
                key = cls.__name__
            key = key.lower()
            self._classes_dict[key] = cls
            return cls

        return _register

    def build(self, name, *args, **kwargs):
        key = name.lower()
        if key not in self._classes_dict.keys():
            raise ValueError(
                f"Type '{name}' is not registered in '{self.registry_name}'."
            )
        cls = self._classes_dict[key]
        return cls(*args, **kwargs)

    def __contains__(self, key: str):
        if key is None:
            return False
        return key.lower() in self._classes_dict

    def __getitem__(self, key: str):
        return self._classes_dict[key]


##### Game Registry ####
GAME_REGISTRY = Registry("GAME_REGISTRY", GameState)

##### Dataset Registry ####
DATASET_REGISTRY = Registry("DATASET_REGISTRY", Dataset)

######### Player Registry ########
class PlayerRegistry:
    def __init__(self, registry_name: str) -> None:
        self.registry_name = registry_name
        self._classes_dict = defaultdict(dict)

    def register(self, game_name: str, player_name: Optional[str] = None):
        def _register(cls):
            nonlocal player_name
            assert issubclass(
                cls, Player
            ), f'Cannot register class "{cls.__name__}" in "{self.registry_name}". Registered classes in this registry must extend "Player"'
            if player_name is None:
                player_name = cls.__name__
            player_name = player_name.lower()
            self._classes_dict[game_name][player_name] = cls
            return cls

        return _register

    def build(self, game_name, player_name, *args, **kwargs):
        game_name = game_name.lower()
        player_name = player_name.lower()

        assert (
            game_name in GAME_REGISTRY
        ), f'No registered game with the name "{game_name}"'
        assert (
            game_name in self._classes_dict
        ), f'No players registered for the game "{game_name}"'
        assert (
            player_name in self._classes_dict[game_name]
        ), f'Player "{player_name}" is not registered for game "{game_name}"'

        cls = self._classes_dict[game_name][player_name]
        return cls(*args, **kwargs)

    def __contains__(self, key: str):
        if key is None:
            return False
        return key.lower() in self._classes_dict

    def __getitem__(self, key: str):
        return self._classes_dict[key]


PLAYER_REGISTRY = PlayerRegistry("PLAYER_REGISTRY")

##### LM Registry ####
LM_REGISTRY = Registry("LM_REGISTRY", LM)

def populate_lm_registry():
    import dspy

    for name, module in inspect.getmembers(dspy, inspect.isclass):
        if issubclass(module, LM) and module is not LM:
            LM_REGISTRY.register(name)(module)

populate_lm_registry()


##### Optimizer Registry ####
OPTIMIZER_REGISTRY = Registry("OPTIMIZER_REGISTRY", Teleprompter)

def populate_optimizer_registry():
    import dspy.teleprompt as tp

    for name, module in inspect.getmembers(tp, inspect.isclass):
        if issubclass(module, Teleprompter) and module is not Teleprompter:
            OPTIMIZER_REGISTRY.register(name)(module)

populate_optimizer_registry()

####### Metric Registry #######
class MetricRegistry:
    def __init__(self, registry_name: str) -> None:
        self.registry_name = registry_name
        self._metrics_dict = {}

    def register(self, name: Optional[str] = None):
        def _register(func):
            assert callable(
                func
            ), f'The registered metric should be a callable object.'
            if name is not None:
                key = name
            else:
                key = func.__name__
            key = key.lower()
            self._metrics_dict[key] = func
            return func

        return _register

    def build(self, name, output_key, *args, **kwargs):
        key = name.lower()
        if key not in self._metrics_dict.keys():
            raise ValueError(
                f"Metric '{name}' is not registered in '{self.registry_name}'."
            )

        metric = self._metrics_dict[key]
        return metric
        # # TODO fix this wrapper or remove it if it isnt needed.
        # return self._metric_wrapper(*args, func=metric, output_key=output_key, **kwargs)

    # def _metric_wrapper(self, func, output_key):
    #     """
    #     This function wraps a function that takes strings as input to one that takes dspy.Example objects as input.
    #     This allows for the user to write functions that compare strings without needing to worry about what the output key is for the dataset.
    #     """
    #     def new_func(pred, gt, trace=None):
    #         return func(getattr(pred, output_key), getattr(gt, output_key))
    #     return new_func

    def __contains__(self, key: str):
        if key is None:
            return False
        return key.lower() in self._metrics_dict

    def __getitem__(self, key: str):
        return self._metrics_dict[key]
    
METRIC_REGISTRY = MetricRegistry("METRIC_REGISTRY")
