from typing import Optional
from pathlib import Path

import os
import dspy

_DEFAULT_CACHE_DIR = os.path.join(Path().home(), ".zse_cache")

def cache_module(module: dspy.Module, model: str, role: str, optimizer: str, dataset: str, cache_dir: Optional[str] = None) -> None:
    if cache_dir is None:
        cache_dir = _DEFAULT_CACHE_DIR
    cache_dir = os.path.join(cache_dir, model, role, optimizer, dataset)
    os.makedirs(cache_dir, exist_ok=True)

    module.save(os.path.join(cache_dir, "module.json"))

def load_cached_module(module: dspy.Module, model: str, role: str, optimizer: str, dataset: str, cache_dir: Optional[str] = None) -> Optional[dspy.Module]:
    if cache_dir is None:
        cache_dir = _DEFAULT_CACHE_DIR
    cache_dir = os.path.join(cache_dir, model, role, optimizer, dataset, "module.json")
    
    if not os.path.exists(cache_dir):
        return None
    
    module.load(cache_dir)

    return module