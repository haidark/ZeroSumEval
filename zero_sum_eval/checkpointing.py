from typing import Optional
from pathlib import Path

import os
import dspy

_DEFAULT_CACHE_DIR = os.path.join(Path().home(), ".zse_cache")

def get_cached_module_path(model: str, role: str, optimizer: str, dataset: str, optimizer_args: dict = {}, compilation_args: dict = {}, cache_dir: Optional[str] = None) -> str:
    if cache_dir is None:
        cache_dir = _DEFAULT_CACHE_DIR
        
    # Name filename over content of optimizer_args and compilation_args
    filename = f"optimizer_args["
    for k, v in optimizer_args.items():
        if isinstance(v, dspy.LM):
            v = v.model.replace("/", "_")
        filename += f"{k}={v},"

    # Remove trailing comma
    if optimizer_args:
        filename = filename[:-1]
        
    filename += "]_compilation_args["
    for k, v in compilation_args.items():
        filename += f"{k}={v},"

    # Remove trailing comma
    if compilation_args:
        filename = filename[:-1]

    filename += "].json"

    return os.path.join(cache_dir, model, role, optimizer, dataset, filename)

def save_checkpoint(module: dspy.Module, module_path:str) -> None:
    os.makedirs(os.path.dirname(module_path), exist_ok=True)
    module.save(module_path)

def load_checkpoint(module: dspy.Module, module_path:str) -> dspy.Module:
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module not found at {module_path}")
    module.load(module_path)
    return module