from typing import Optional
from pathlib import Path

import os
import dspy

_DEFAULT_CACHE_DIR = os.path.join(Path().home(), ".zse_cache")

def get_cached_module_path(model: str, role: str, optimizer: str, dataset: str, cache_dir: Optional[str] = None) -> str:
    if cache_dir is None:
        cache_dir = _DEFAULT_CACHE_DIR
    return os.path.join(cache_dir, model, role, optimizer, dataset, "module.json")


def save_checkpoint(module: dspy.Module, module_path:str) -> None:
    module.save(module_path)

def load_checkpoint(module: dspy.Module, module_path:str) -> dspy.Module:
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module not found at {module_path}")
    return module.load(module_path)
