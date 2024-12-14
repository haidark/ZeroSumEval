from typing import Optional
from pathlib import Path

import os
import dspy

_DEFAULT_CACHE_DIR = os.path.join(Path().home(), ".zse_cache")

def save_module(module: dspy.Module, model: str, role: str, optimizer: str, dataset: str, module_path: Optional[str] = None) -> None:
    if module_path is None:
        module_path = _DEFAULT_CACHE_DIR
    module_path = os.path.join(module_path, model, role, optimizer, dataset)
    os.makedirs(module_path, exist_ok=True)
    module.save(os.path.join(module_path, "module.json"))

def load_module(module: dspy.Module, model: str, role: str, optimizer: str, dataset: str, module_path: Optional[str] = None) -> Optional[dspy.Module]:
    if module_path is None:
        module_path = _DEFAULT_CACHE_DIR
    module_path = os.path.join(module_path, model, role, optimizer, dataset, "module.json")
    
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module not found at {module_path}")
    
    return module.load(module_path)
