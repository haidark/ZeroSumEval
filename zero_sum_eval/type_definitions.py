from dataclasses import dataclass
from typing import Optional
from dspy import Prediction
    
@dataclass
class ActionConfig:
    name: str
    module_path: Optional[str] = None
    optimize: Optional[bool] = False
    dataset: Optional[str] = None
    dataset_args: Optional[dict] = None
    optimizer: Optional[str] = None
    optimizer_args: Optional[dict] = None
    metric: Optional[str] = None

@dataclass
class Move:
    value: str
    trace: Optional[Prediction] = None
