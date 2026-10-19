"""Sistema dinâmico de Ciclos Ambientais, Estações do Ano e Equilíbrio Ecológico."""

from __future__ import annotations
import math
from typing import List, Dict, Optional, Any
from ..entities.environment import SeasonType, SEASON_ORDER, SEASON_METADATA, EnvironmentalState
from ..entities.organism import Organism
from ..entities.food import Food


class EnvironmentSystem:
    """Controla o relógio sazonal do ecossistema, transições climáticas suaves e parâmetros de sobrevivência."""

    def __init__(self, season_duration_ticks: int = 250) -> None:
        self.season_duration = max(50, int(season_duration_ticks))
        self.cycle_length = self.season_duration * len(SEASON_ORDER)
        self.state = EnvironmentalState(
            tick=0,
            year=1,
            season=SeasonType.SPRING,
            season_tick=0,
            season_duration=self.season_duration,
            season_progress=0.0,
            temperature=SEASON_METADATA[SeasonType.SPRING]["base_temp"],
            food_spawn_multiplier=SEASON_METADATA[SeasonType.SPRING]["food_spawn_mult"],
            metabolic_cost_multiplier=SEASON_METADATA[SeasonType.SPRING]["metabolic_cost_mult"],
            reproduction_cost_multiplier=SEASON_METADATA[SeasonType.SPRING]["reproduction_cost_mult"],
            movement_cost_multiplier=SEASON_METADATA[SeasonType.SPRING]["movement_cost_mult"],
            environmental_stress=SEASON_METADATA[SeasonType.SPRING]["stress_level"],
        )
        self._sliding_consumed: List[float] = []
        self._sliding_spawned: List[float] = []

    def update(
        self,
        tick: int,
        organisms: Dict[int, Organism],
        foods: Dict[int, Food],
        events: List[Dict[str, Any]],
    ) -> None:
        """Avança o relógio sazonal e calcula a transição contínua dos parâmetros climáticos."""
        self.state.tick = tick
        self.state.year = (tick // self.cycle_length) + 1

        cycle_tick = tick % self.cycle_length
        season_index = cycle_tick // self.season_duration
        season_tick = cycle_tick % self.season_duration
        new_season = SEASON_ORDER[season_index]

        # Transição e virada de estação
        if new_season != self.state.season:
            old_meta = SEASON_METADATA[self.state.season]
            new_meta = SEASON_METADATA[new_season]

            # Arquiva dados da estação que se encerrou
            summary = {
                "year": self.state.year,
                "season": self.state.season.value,
                "season_name": old_meta["name"],
                "births": self.state.births_this_season,
                "deaths": self.state.deaths_this_season,
                "vrancos_births": self.state.vrancos_births_season,
                "vrancos_deaths": self.state.vrancos_deaths_season,
                "predators_births": self.state.predators_births_season,
                "predators_deaths": self.state.predators_deaths_season,
                "food_consumed": round(self.state.food_consumed_season, 1),
                "food_spawned": round(self.state.food_spawned_season, 1),
            }
            self.state.season_history.append(summary)
            if len(self.state.season_history) > 12:
                self.state.season_history.pop(0)

            # Reseta contadores sazonais
            self.state.season = new_season
            self.state.births_this_season = 0
            self.state.deaths_this_season = 0
            self.state.vrancos_births_season = 0
            self.state.vrancos_deaths_season = 0
            self.state.predators_births_season = 0
            self.state.predators_deaths_season = 0
            self.state.food_consumed_season = 0.0
            self.state.food_spawned_season = 0.0

            # Dispara evento ambiental no ecossistema
            events.append({
                "type": "season_changed",
                "season": new_season.value,
                "season_name": new_meta["name"],
                "icon": new_meta["icon"],
                "year": self.state.year,
                "message": f"Início de {new_meta['name']} (Ano {self.state.year}) - {new_meta['description']}",
                "tick": tick,
            })

        self.state.season_tick = season_tick
        progress = season_tick / float(self.season_duration)
        self.state.season_progress = progress

        # Interpolação suave e contínua (smoothstep senoidal) entre a estação atual e a próxima
        next_season_index = (season_index + 1) % len(SEASON_ORDER)
        next_season = SEASON_ORDER[next_season_index]

        curr_meta = SEASON_METADATA[self.state.season]
        next_meta = SEASON_METADATA[next_season]

        w = 0.5 * (1.0 - math.cos(math.pi * progress))

        self.state.temperature = (1.0 - w) * curr_meta["base_temp"] + w * next_meta["base_temp"]
        self.state.food_spawn_multiplier = (1.0 - w) * curr_meta["food_spawn_mult"] + w * next_meta["food_spawn_mult"]
        self.state.metabolic_cost_multiplier = (1.0 - w) * curr_meta["metabolic_cost_mult"] + w * next_meta["metabolic_cost_mult"]
        self.state.reproduction_cost_multiplier = (1.0 - w) * curr_meta["reproduction_cost_mult"] + w * next_meta["reproduction_cost_mult"]
        self.state.movement_cost_multiplier = (1.0 - w) * curr_meta["movement_cost_mult"] + w * next_meta["movement_cost_mult"]
        self.state.environmental_stress = (1.0 - w) * curr_meta["stress_level"] + w * next_meta["stress_level"]

    def record_birth(self, organism: Organism) -> None:
        """Registra novo nascimento na contagem sazonal da espécie."""
        self.state.births_this_season += 1
        if getattr(organism, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO:
            self.state.vrancos_births_season += 1
        else:
            self.state.predators_births_season += 1

    def record_death(self, organism: Organism, cause: str) -> None:
        """Registra óbito na contagem sazonal da espécie."""
        self.state.deaths_this_season += 1
        if getattr(organism, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO:
            self.state.vrancos_deaths_season += 1
        else:
            self.state.predators_deaths_season += 1

    def record_food_consumed(self, energy_value: float) -> None:
        """Registra biomassa assimilada para balanço ecológico."""
        self.state.food_consumed_season += energy_value
        self._sliding_consumed.append(energy_value)
        if len(self._sliding_consumed) > 100:
            self._sliding_consumed.pop(0)

    def record_food_spawned(self, energy_value: float) -> None:
        """Registra biomassa gerada para balanço ecológico."""
        self.state.food_spawned_season += energy_value
        self._sliding_spawned.append(energy_value)
        if len(self._sliding_spawned) > 100:
            self._sliding_spawned.pop(0)

    def get_ecology_metrics(
        self,
        organisms: Dict[int, Organism],
        foods: Dict[int, Food],
        territories: Optional[Dict[int, Any]] = None,
    ) -> Dict[str, Any]:
        """Calcula métricas agregadas de equilíbrio ecológico, capacidade de carga e estresse ambiental."""
        pop_count = len(organisms)
        vrancos = [o for o in organisms.values() if getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO]
        predators = [o for o in organisms.values() if getattr(o, "species", Organism.SPECIES_PREDATOR) != Organism.SPECIES_VRANCO]

        food_biomass = sum(getattr(f, "energy_value", 25.0) for f in foods.values())
        animal_biomass = sum(o.energy + o.traits.size * 5.0 for o in organisms.values())
        total_biomass = round(food_biomass + animal_biomass, 1)

        # Capacidade de suporte total estimada do mundo
        total_carrying_capacity = 160
        if territories:
            total_carrying_capacity = sum(getattr(z, "carrying_capacity", 20) for z in territories.values())

        carrying_capacity_ratio = round(pop_count / max(1.0, float(total_carrying_capacity)), 2)

        # Taxas médias móveis de consumo e regeneração por tick
        consumption_rate = round(sum(self._sliding_consumed) / max(1, len(self._sliding_consumed)), 1)
        regeneration_rate = round(sum(self._sliding_spawned) / max(1, len(self._sliding_spawned)), 1)

        critical_regions_count = 0
        if territories:
            critical_regions_count = sum(1 for z in territories.values() if getattr(z, "status", "") in ("DEGRADED", "CONTESTED"))

        predator_prey_ratio = round(len(vrancos) / max(1, len(predators)), 2)
        growth_rate = round((self.state.births_this_season - self.state.deaths_this_season) / max(1, pop_count), 2)

        return {
            "total_biomass": total_biomass,
            "food_biomass": round(food_biomass, 1),
            "animal_biomass": round(animal_biomass, 1),
            "carrying_capacity": total_carrying_capacity,
            "carrying_capacity_ratio": carrying_capacity_ratio,
            "is_overpopulated": carrying_capacity_ratio > 1.25,
            "consumption_rate": consumption_rate,
            "regeneration_rate": regeneration_rate,
            "biomass_balance": round(regeneration_rate - consumption_rate, 1),
            "critical_regions_count": critical_regions_count,
            "predator_prey_ratio": predator_prey_ratio,
            "seasonal_growth_rate": growth_rate,
            "vrancos_count": len(vrancos),
            "predators_count": len(predators),
        }
