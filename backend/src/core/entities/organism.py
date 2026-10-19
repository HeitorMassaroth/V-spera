"""Entidade Organismo, representando um indivíduo autônomo no ecossistema."""

from __future__ import annotations
import math
from typing import Dict, Any, Optional
from .traits import OrganismTraits


class Organism:
    """Organismo autônomo com cinemática, balanço de energia e percepção."""

    def __init__(
        self,
        id: int,
        x: float,
        y: float,
        vx: float = 0.0,
        vy: float = 0.0,
        energy: float = 100.0,
        age: int = 0,
        traits: Optional[OrganismTraits] = None,
        wander_angle: float = 0.0,
        generation: int = 0,
        parent_id: Optional[int] = None,
    ) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.energy = energy
        self.age = age
        self.traits = traits if traits is not None else OrganismTraits()
        self.wander_angle = wander_angle
        self.generation = generation
        self.parent_id = parent_id
        self.alive = True
        self.food_eaten = 0

    @property
    def speed(self) -> float:
        """Módulo da velocidade escalar atual."""
        return math.hypot(self.vx, self.vy)

    @property
    def heading(self) -> float:
        """Ângulo direcional do vetor velocidade em radianos."""
        return math.atan2(self.vy, self.vx)

    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa para snapshot."""
        return {
            "id": self.id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "vx": round(self.vx, 3),
            "vy": round(self.vy, 3),
            "energy": round(self.energy, 2),
            "age": self.age,
            "traits": self.traits.to_dict(),
            "wander_angle": round(self.wander_angle, 4),
            "generation": self.generation,
            "parent_id": self.parent_id,
            "alive": self.alive,
            "food_eaten": self.food_eaten,
        }

    def to_compact_dict(self) -> Dict[str, Any]:
        """Serialização compacta para transmissão via WebSocket em tempo real."""
        return {
            "id": self.id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "e": round(self.energy, 1),
            "sz": self.traits.size,
            "h": self.traits.color_hue,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Organism:
        traits = OrganismTraits.from_dict(data["traits"])
        org = cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            vx=data.get("vx", 0.0),
            vy=data.get("vy", 0.0),
            energy=data.get("energy", 100.0),
            age=data.get("age", 0),
            traits=traits,
            wander_angle=data.get("wander_angle", 0.0),
            generation=data.get("generation", 0),
            parent_id=data.get("parent_id"),
        )
        org.alive = data.get("alive", True)
        org.food_eaten = data.get("food_eaten", 0)
        return org
