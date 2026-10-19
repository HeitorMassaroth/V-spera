"""Entidade Ninho Familiar, representando o abrigo, repositório de recursos e berço dos filhotes."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Nest:
    """Ninho familiar onde casais estabelecem seu território, protegem filhotes e acumulam recursos."""

    id: int
    family_id: int
    x: float
    y: float
    materials: float = 25.0       # Nível de materiais estruturais [0.0 - 100.0]
    food_storage: float = 0.0     # Biomassa alimentar estocada para amamentar/nutrir filhotes
    level: int = 1                # 1: Ninho Simples, 2: Refúgio Fortificado, 3: Santuário Familiar
    created_tick: int = 0
    is_active: bool = True

    def add_food(self, amount: float) -> None:
        """Adiciona biomassa ao estoque alimentar do ninho."""
        self.food_storage = min(180.0, self.food_storage + max(0.0, amount))

    def consume_food(self, amount: float) -> float:
        """Consome biomassa estocada para alimentar os habitantes do ninho."""
        consumed = min(self.food_storage, max(0.0, amount))
        self.food_storage -= consumed
        return consumed

    def add_materials(self, amount: float) -> bool:
        """Adiciona materiais de construção e verifica se o ninho pode ser aprimorado."""
        self.materials = min(100.0, self.materials + max(0.0, amount))
        return self.check_upgrade()

    def check_upgrade(self) -> bool:
        """Evolui o nível do ninho caso atinja os limiares de materiais."""
        if self.level == 1 and self.materials >= 50.0:
            self.level = 2
            return True
        elif self.level == 2 and self.materials >= 90.0:
            self.level = 3
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa para snapshot e API."""
        return {
            "id": self.id,
            "family_id": self.family_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "materials": round(self.materials, 1),
            "food_storage": round(self.food_storage, 1),
            "level": self.level,
            "created_tick": self.created_tick,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Nest:
        return cls(
            id=data["id"],
            family_id=data["family_id"],
            x=float(data["x"]),
            y=float(data["y"]),
            materials=float(data.get("materials", 25.0)),
            food_storage=float(data.get("food_storage", 0.0)),
            level=int(data.get("level", 1)),
            created_tick=int(data.get("created_tick", 0)),
            is_active=bool(data.get("is_active", True)),
        )
