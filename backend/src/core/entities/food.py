"""Entidade de recurso alimentar no ambiente."""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Food:
    """Ponto de biomassa/alimento estático no ambiente."""

    id: int
    x: float
    y: float
    energy_value: float = 45.0
    radius: float = 3.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Food:
        return cls(**data)
