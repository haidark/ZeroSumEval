from zero_sum_eval.player import Player
from zero_sum_eval.game_state import GameState
import inspect

from collections import defaultdict
from dsp.modules.lm import LM


class Registry:
    def __init__(self, registry_name: str, class_type) -> None:
        self.registry_name = registry_name
        self.class_type = class_type
        self._classes_dict = {}

    def register(self, name: str = None):
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


LM_REGISTRY = Registry("LM_REGISTRY", LM)


def populate_lm_registry():
    import dspy

    for name, module in inspect.getmembers(dspy, inspect.isclass):
        if issubclass(module, LM) and module is not LM:
            LM_REGISTRY.register(name)(module)


populate_lm_registry()

GAME_REGISTRY = Registry("GAME_REGISTRY", GameState)


class PlayerRegistry:
    def __init__(self, registry_name: str) -> None:
        self.registry_name = registry_name
        self._classes_dict = defaultdict(dict)

    def register(self, game_name: str, player_name: str = None):
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
