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
        """Calcula o débito energético total no ciclo com compensações biológicas: basal + cinético + sensorial."""
        size_factor = organism.traits.size / 5.0
        pheno = getattr(organism, "phenotype", None)

        # Custo basal de sustentação celular - maior massa muscular exige mais energia basal
        muscle_factor = (0.75 + 0.50 * (pheno.forca_muscular / 50.0)) if pheno else 1.0
        cost_basal = self.k_basal * (size_factor ** 2) * muscle_factor

        # Custo cinético por atrito e aceleração - maior propensão a velocidade consome mais por deslocamento
        speed_factor = (0.80 + 0.40 * (pheno.velocidade / 50.0)) if pheno else 1.0
        cost_mov = self.k_mov * size_factor * (organism.speed ** 2) * speed_factor

        # Custo de manutenção do aparelho sensorial (visão e detecção de ameaças)
        vis_factor = (0.80 + 0.40 * (pheno.deteccao_ameacas / 50.0)) if pheno else 1.0
        cost_vis = self.k_vis * organism.traits.vision_radius * vis_factor

        # Total modulado pela eficiência metabólica do genótipo/fenótipo
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
        # Recém-nascidos e filhotes em desenvolvimento não coletam alimento selvagem independentemente
        if getattr(organism, "life_stage", None) in [Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING]:
            return []

        consumed: List[Food] = []
        eat_radius = organism.traits.size + 4.0  # raio de alcance físico da boca
        pheno = getattr(organism, "phenotype", None)

        nearby_foods = food_grid.query_radius(organism.x, organism.y, eat_radius)
        for food, dist in nearby_foods:
            if dist <= organism.traits.size + food.radius:
                # Modula energia absorvida pela eficiência de coleta expressa
                eff = pheno.eficiencia_coleta if pheno else (getattr(organism.personality, "eficiencia_coleta", 1.0) if hasattr(organism, "personality") else 1.0)
                gained_energy = food.energy_value * eff
                organism.energy = min(120.0, organism.energy + gained_energy)

                # Alimentação regenera gradualmente a saúde física
                max_hp = pheno.max_saude if pheno else (organism.genome.max_saude if hasattr(organism, "genome") else 100.0)
                organism.saude = min(max_hp, organism.saude + gained_energy * 0.20)
                organism.food_eaten += 1
                consumed.append(food)

                # Registra fonte de alimento na memória episódica
                if getattr(organism, "memory", None):
                    organism.memory.add_food_source(food.x, food.y, getattr(organism, "age", 0))

        return consumed

    def check_survival(self, organism: Organism) -> bool:
        """Atualiza a idade e verifica condições de inanição, dano fatal ou senescência."""
        organism.age += 1

        # Morte por inanição energética
        if organism.energy <= 0.0:
            organism.alive = False
            organism.energy = 0.0
            if not getattr(organism, "cause_of_death", None):
                organism.cause_of_death = "Inanição"
            return False

        # Morte por dano físico de combate ou predação
        if hasattr(organism, "saude") and organism.saude <= 0.0:
            organism.alive = False
            organism.saude = 0.0
            if not getattr(organism, "cause_of_death", None):
                organism.cause_of_death = "Combate Fatal"
            return False

        # Morte por senescência (idade avançada)
        if organism.age >= organism.traits.max_age:
            organism.alive = False
            if not getattr(organism, "cause_of_death", None):
                organism.cause_of_death = "Senescência"
            return False

        return True
