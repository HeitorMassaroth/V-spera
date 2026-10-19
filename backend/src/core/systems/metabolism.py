"""Sistema de balanço metabólico, consumo de alimento e vitalidade."""

from __future__ import annotations
import math
from typing import List, Tuple
from ..entities.organism import Organism
from ..entities.food import Food
from ..spatial.spatial_grid import SpatialHashGrid


class MetabolismSystem:
    """Calcula gastos energéticos termodinâmicos, assimilação de biomassa e mortalidade."""

    def __init__(
        self,
        k_basal: float = 0.05,
        k_mov: float = 0.025,
        k_vis: float = 0.0008,
    ) -> None:
        self.k_basal = float(k_basal)
        self.k_mov = float(k_mov)
        self.k_vis = float(k_vis)

    def calculate_cost(self, organism: Organism, dt: float = 1.0) -> float:
        """Calcula o débito energético total no ciclo: basal + cinético + sensorial."""
        size_factor = organism.traits.size / 5.0

        # Custo basal de sustentação celular
        cost_basal = self.k_basal * (size_factor ** 2)

        # Custo cinético por atrito e aceleração
        cost_mov = self.k_mov * size_factor * (organism.speed ** 2)

        # Custo de manutenção do aparelho sensorial (visão)
        cost_vis = self.k_vis * organism.traits.vision_radius

        # Total modulado pela eficiência metabólica do genótipo
        total = (cost_basal + cost_mov + cost_vis) * organism.traits.metabolic_efficiency * dt
        return max(0.001, total)

    def apply_metabolism(self, organism: Organism, dt: float = 1.0) -> float:
        """Deduz a energia metabólica calculada do organismo."""
        cost = self.calculate_cost(organism, dt)
        organism.energy -= cost
        return cost

    def process_feeding(
        self,
        organism: Organism,
        food_grid: SpatialHashGrid[Food],
    ) -> List[Food]:
        """Verifica se o organismo alcançou algum alimento e realiza o consumo."""
        consumed: List[Food] = []
        eat_radius = organism.traits.size + 4.0  # raio de alcance físico da boca

        nearby_foods = food_grid.query_radius(organism.x, organism.y, eat_radius)
        for food, dist in nearby_foods:
            if dist <= organism.traits.size + food.radius:
                organism.energy += food.energy_value
                organism.food_eaten += 1
                consumed.append(food)

        return consumed

    def check_survival(self, organism: Organism) -> bool:
        """Atualiza a idade e verifica condições de inanição ou senescência."""
        organism.age += 1

        # Morte por inanição
        if organism.energy <= 0.0:
            organism.alive = False
            organism.energy = 0.0
            return False

        # Morte por senescência (idade avançada)
        if organism.age >= organism.traits.max_age:
            organism.alive = False
            return False

        return True
