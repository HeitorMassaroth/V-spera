"""Definição de traços hereditários e físicos dos organismos."""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class OrganismTraits:
    """Conjunto de características fenotípicas e genotípicas de um organismo."""

    size: float = 6.0                  # Raio físico em pixels
    max_speed: float = 2.8             # Velocidade máxima (unidades/tick)
    vision_radius: float = 75.0        # Alcance do sensor de percepção (pixels)
    max_force: float = 0.25            # Capacidade máxima de manobra/steering force
    color_hue: float = 160.0           # Matiz de cor visual (0 - 360 em HSL)
    max_age: int = 2500                # Ciclos máximos de vida (senescência)
    metabolic_efficiency: float = 1.0  # Fator multiplicador de eficiência metabólica

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OrganismTraits:
        return cls(**data)
