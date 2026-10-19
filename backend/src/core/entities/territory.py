"""Entidades e estruturas de dados para Territórios, Qualidade Regional e Dinâmica de Ocupação."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any


@dataclass
class TerritoryZone:
    """Representa uma região geográfica delimitada no ecossistema com indicadores dinâmicos de qualidade."""

    id: int
    name: str
    x: float
    y: float
    radius: float = 95.0
    is_peripheral: bool = False

    # Recursos e biomassa finita
    food_count: int = 0
    biomass: float = 0.0
    base_fertility: float = 1.0          # Fertilidade natural do solo
    current_fertility: float = 1.0       # Fertilidade efetiva dinâmica (degrada com superexploração)
    depletion_ticks: int = 0             # Ciclos consecutivos com recursos esgotados
    recovery_ticks: int = 0              # Ciclos de descanso/pousio ecológico

    # Densidade biológica presente
    predator_count: int = 0
    vranco_count: int = 0
    shelter_count: int = 0               # Ninhos ou refúgios ativos na região
    carrying_capacity: int = 20          # Capacidade de suporte recomendada da região
    occupant_ids: Set[int] = field(default_factory=set)

    # Indicadores quantitativos de qualidade
    food_availability_score: float = 0.5 # [0.0, 1.0]
    safety_score: float = 1.0            # [0.0, 1.0]
    population_density: float = 0.0      # Razão ocupantes / capacidade
    competition_pressure: float = 0.0     # [0.0, 1.0]
    quality_score: float = 50.0          # [0.0, 100.0]

    # Controle e Situação Política
    controller_type: str = "NONE"        # "NONE", "FAMILY", "CLAN"
    controlling_clan_id: Optional[int] = None
    controlling_family_id: Optional[int] = None
    status: str = "UNCLAIMED"            # "UNCLAIMED", "SETTLED", "CONTESTED", "DEGRADED", "ABANDONED"
    dispute_ticks: int = 0
    abandoned_cooldown: int = 0          # Cooldown após abandono para permitir repouso
    abandoned_tick: Optional[int] = None

    # Histórico de eventos territoriais
    history_log: List[Dict[str, Any]] = field(default_factory=list)

    def log_event(self, event_type: str, description: str, tick: int) -> None:
        """Registra acontecimentos marcantes da região."""
        entry = {
            "type": event_type,
            "description": description,
            "tick": tick,
        }
        self.history_log.append(entry)
        if len(self.history_log) > 25:
            self.history_log.pop(0)

    def calculate_quality(self, recent_combat_in_zone: int = 0, recent_combat: Optional[bool] = None) -> float:
        """
        Calcula a qualidade territorial dinâmica composta [0.0 - 100.0] considerando:
        1. Alimento disponível real e biomassa efetiva.
        2. Segurança (presença de predadores, agressões e combates recentes).
        3. Abrigos disponíveis (ninhos familiares funcionais).
        4. Pressão de competição e saturação populacional.
        """
        if recent_combat is not None:
            recent_combat_in_zone = 2 if recent_combat else 0
        # 1. Disponibilidade de alimento relativa à capacidade
        target_biomass = float(self.carrying_capacity * 12.0)
        self.food_availability_score = min(1.0, max(0.0, self.biomass / max(1.0, target_biomass)))

        # 2. Densidade e Competição
        total_occupants = len(self.occupant_ids)
        self.population_density = total_occupants / float(max(1, self.carrying_capacity))

        # Competição por recursos eleva-se quando há muitos ocupantes para pouca comida
        if self.food_count > 0:
            forager_ratio = float(total_occupants) / float(self.food_count)
            self.competition_pressure = min(1.0, max(0.0, forager_ratio / 3.0))
        else:
            self.competition_pressure = 1.0 if total_occupants > 0 else 0.0

        # 3. Segurança: Presença de predadores gera risco, combates recentes reduzem segurança
        predator_threat = min(1.0, self.predator_count * 0.22)
        combat_penalty = min(0.40, recent_combat_in_zone * 0.10)
        self.safety_score = max(0.0, min(1.0, 1.0 - predator_threat - combat_penalty))

        # 4. Abrigo disponível (bônus por ninho estruturado)
        shelter_bonus = min(1.0, self.shelter_count * 0.50)

        # 5. Composição ponderada da qualidade
        # Alimento (40%) + Segurança (30%) + Abrigo (15%) + Fertilidade (15%) - Competição (20%)
        raw_score = (
            0.38 * self.food_availability_score
            + 0.30 * self.safety_score
            + 0.14 * shelter_bonus
            + 0.18 * self.current_fertility
            - 0.20 * self.competition_pressure
        )

        self.quality_score = round(max(0.0, min(100.0, raw_score * 100.0)), 1)

        # Atualiza status baseado na qualidade e histórico
        if self.quality_score < 22.0 or (self.food_count == 0 and total_occupants >= 4):
            self.status = "DEGRADED"
        elif self.status == "DEGRADED" and self.quality_score >= 38.0:
            self.status = "SETTLED" if (self.controlling_clan_id or self.controlling_family_id) else "UNCLAIMED"

        return self.quality_score

    def update_resource_ecology(self, tick: int) -> None:
        """
        Garante finitude dos recursos: regiões superexploradas sofrem degradação de fertilidade,
        enquanto regiões em repouso recuperam gradualmente a produtividade natural do solo.
        """
        total_occupants = len(self.occupant_ids)

        if self.abandoned_cooldown > 0:
            self.abandoned_cooldown -= 1

        # Superpopulação / superexploração continuada: o solo se esgota
        if total_occupants > int(self.carrying_capacity * 1.25) or (self.food_count == 0 and total_occupants > 0):
            self.depletion_ticks += 1
            self.recovery_ticks = 0
            if self.depletion_ticks % 25 == 0:
                self.current_fertility = max(0.20, round(self.current_fertility - 0.10, 2))
                self.log_event("resource_depleted", f"{self.name}: Solo degradado por sobreuso (Fertilidade {self.current_fertility:.2f})", tick)
        else:
            # População moderada ou vazia: regeneração ecológica natural
            self.recovery_ticks += 1
            if self.depletion_ticks > 0:
                self.depletion_ticks = max(0, self.depletion_ticks - 1)
            if self.recovery_ticks % 30 == 0 and self.current_fertility < self.base_fertility:
                self.current_fertility = min(self.base_fertility, round(self.current_fertility + 0.08, 2))
                self.log_event("resource_recovered", f"{self.name}: Regeneração da biomassa e solo (Fertilidade {self.current_fertility:.2f})", tick)

    def contains_point(self, x: float, y: float) -> bool:
        """Verifica se as coordenadas estão dentro do raio de influência do território."""
        dx = x - self.x
        dy = y - self.y
        return (dx * dx + dy * dy) <= (self.radius * self.radius)

    def distance_to_point(self, x: float, y: float) -> float:
        """Calcula a distância euclidiana do centro do território a um ponto."""
        return math.hypot(x - self.x, y - self.y)

    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa para snapshot e streaming do ecossistema."""
        return {
            "id": self.id,
            "name": self.name,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "radius": round(self.radius, 1),
            "is_peripheral": self.is_peripheral,
            "food_count": self.food_count,
            "biomass": round(self.biomass, 1),
            "current_fertility": round(self.current_fertility, 2),
            "predator_count": self.predator_count,
            "vranco_count": self.vranco_count,
            "shelter_count": self.shelter_count,
            "carrying_capacity": self.carrying_capacity,
            "occupants_count": len(self.occupant_ids),
            "food_availability_score": round(self.food_availability_score, 2),
            "safety_score": round(self.safety_score, 2),
            "population_density": round(self.population_density, 2),
            "competition_pressure": round(self.competition_pressure, 2),
            "quality_score": self.quality_score,
            "controller_type": self.controller_type,
            "controlling_clan_id": self.controlling_clan_id,
            "controlling_family_id": self.controlling_family_id,
            "status": self.status,
            "dispute_ticks": self.dispute_ticks,
            "abandoned_cooldown": self.abandoned_cooldown,
            "history_log": self.history_log[-5:],
        }
