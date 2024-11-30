from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel
    
@dataclass
class Role:
    name: str
    module_path: Optional[str] = None
    optimize: Optional[bool] = False
    dataset: Optional[str] = None
    dataset_args: Optional[dict] = None
    optimizer: Optional[str] = None
    optimizer_args: Optional[dict] = None
    metric: Optional[str] = None
