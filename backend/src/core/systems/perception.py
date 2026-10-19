"""Sistema de percepção de organismos no ambiente."""

from __future__ import annotations
from typing import Tuple, Optional
from ..entities.organism import Organism
from ..entities.food import Food
from ..spatial.spatial_grid import SpatialHashGrid


class PerceptionSystem:
    """Responsável por permitir que os organismos detectem alvos e recursos no seu campo visual."""

    @staticmethod
    def find_nearest_food(
        organism: Organism,
        food_grid: SpatialHashGrid[Food],
    ) -> Tuple[Optional[Food], float]:
        """Localiza o recurso alimentar mais próximo dentro do raio de visão do organismo."""
        return food_grid.query_nearest(
            organism.x,
            organism.y,
            organism.traits.vision_radius,
        )
