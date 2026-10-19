"""Entidades e modelos para Ciclos Ambientais, Estações do Ano e Equilíbrio Ecológico."""

from __future__ import annotations
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class SeasonType(str, Enum):
    SPRING = "SPRING"    # Primavera: Abundância, brotamento acelerado, facilidade reprodutiva
    SUMMER = "SUMMER"    # Verão: Calor, alta biomassa, gasto cinético moderado, visibilidade plena
    AUTUMN = "AUTUMN"    # Outono: Esfriamento, desaceleração vegetal, acúmulo de reservas
    WINTER = "WINTER"    # Inverno: Escassez, frio severo, desaceleração do brotamento, termorregulação


SEASON_ORDER = [
    SeasonType.SPRING,
    SeasonType.SUMMER,
    SeasonType.AUTUMN,
    SeasonType.WINTER,
]


SEASON_METADATA = {
    SeasonType.SPRING: {
        "name": "Primavera",
        "icon": "🌸",
        "description": "Período de regeneração da flora, clima ameno e condições ideais para reprodução e expansão.",
        "base_temp": 20.0,
        "food_spawn_mult": 1.35,
        "metabolic_cost_mult": 0.95,
        "reproduction_cost_mult": 0.85,
        "movement_cost_mult": 0.95,
        "stress_level": 0.15,
        "color_theme": "#34D399",
    },
    SeasonType.SUMMER: {
        "name": "Verão",
        "icon": "☀️",
        "description": "Período de calor intenso e máxima atividade metabólica. Alta biomassa porém maior exaustão cinética.",
        "base_temp": 29.0,
        "food_spawn_mult": 1.15,
        "metabolic_cost_mult": 1.05,
        "reproduction_cost_mult": 1.00,
        "movement_cost_mult": 1.00,
        "stress_level": 0.35,
        "color_theme": "#F59E0B",
    },
    SeasonType.AUTUMN: {
        "name": "Outono",
        "icon": "🍂",
        "description": "Transição para o frio. Regeneração vegetal desacelera; grupos sociais estocam biomassa e preparam abrigos.",
        "base_temp": 15.0,
        "food_spawn_mult": 0.80,
        "metabolic_cost_mult": 1.02,
        "reproduction_cost_mult": 1.10,
        "movement_cost_mult": 1.02,
        "stress_level": 0.45,
        "color_theme": "#FB923C",
    },
    SeasonType.WINTER: {
        "name": "Inverno",
        "icon": "❄️",
        "description": "Escassez severa e temperaturas baixas. Custo metabólico de termorregulação elevado e reprodução dificultada.",
        "base_temp": 6.0,
        "food_spawn_mult": 0.40,
        "metabolic_cost_mult": 1.25,
        "reproduction_cost_mult": 1.35,
        "movement_cost_mult": 1.15,
        "stress_level": 0.80,
        "color_theme": "#38BDF8",
    },
}


@dataclass
class EnvironmentalState:
    """Estado instantâneo do clima, sazonalidade e equilíbrio ecológico."""

    tick: int = 0
    year: int = 1
    season: SeasonType = SeasonType.SPRING
    season_tick: int = 0
    season_duration: int = 250
    season_progress: float = 0.0          # [0.0 - 1.0]

    # Parâmetros físicos contínuos (interpolados suavemente)
    temperature: float = 20.0             # Em °C
    food_spawn_multiplier: float = 1.35
    metabolic_cost_multiplier: float = 0.95
    reproduction_cost_multiplier: float = 0.85
    movement_cost_multiplier: float = 0.95
    environmental_stress: float = 0.15

    # Métricas sazonais de equilíbrio
    births_this_season: int = 0
    deaths_this_season: int = 0
    vrancos_births_season: int = 0
    vrancos_deaths_season: int = 0
    predators_births_season: int = 0
    predators_deaths_season: int = 0
    food_consumed_season: float = 0.0
    food_spawned_season: float = 0.0

    # Histórico de transições sazonais
    season_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        meta = SEASON_METADATA.get(self.season, SEASON_METADATA[SeasonType.SPRING])
        return {
            "tick": self.tick,
            "year": self.year,
            "season": self.season.value,
            "season_name": meta["name"],
            "season_icon": meta["icon"],
            "season_description": meta["description"],
            "season_color": meta["color_theme"],
            "season_tick": self.season_tick,
            "season_duration": self.season_duration,
            "season_progress": round(self.season_progress, 4),
            "season_progress_pct": round(self.season_progress * 100.0, 1),
            "temperature": round(self.temperature, 1),
            "food_spawn_multiplier": round(self.food_spawn_multiplier, 3),
            "metabolic_cost_multiplier": round(self.metabolic_cost_multiplier, 3),
            "reproduction_cost_multiplier": round(self.reproduction_cost_multiplier, 3),
            "movement_cost_multiplier": round(self.movement_cost_multiplier, 3),
            "environmental_stress": round(self.environmental_stress, 2),
            "births_this_season": self.births_this_season,
            "deaths_this_season": self.deaths_this_season,
            "vrancos_births_season": self.vrancos_births_season,
            "vrancos_deaths_season": self.vrancos_deaths_season,
            "predators_births_season": self.predators_births_season,
            "predators_deaths_season": self.predators_deaths_season,
            "food_consumed_season": round(self.food_consumed_season, 1),
            "food_spawned_season": round(self.food_spawned_season, 1),
            "season_history": self.season_history[-8:],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnvironmentalState:
        raw_season = data.get("season", SeasonType.SPRING.value)
        try:
            season = SeasonType(raw_season)
        except Exception:
            season = SeasonType.SPRING

        return cls(
            tick=int(data.get("tick", 0)),
            year=int(data.get("year", 1)),
            season=season,
            season_tick=int(data.get("season_tick", 0)),
            season_duration=int(data.get("season_duration", 250)),
            season_progress=float(data.get("season_progress", 0.0)),
            temperature=float(data.get("temperature", 20.0)),
            food_spawn_multiplier=float(data.get("food_spawn_multiplier", 1.0)),
            metabolic_cost_multiplier=float(data.get("metabolic_cost_multiplier", 1.0)),
            reproduction_cost_multiplier=float(data.get("reproduction_cost_multiplier", 1.0)),
            movement_cost_multiplier=float(data.get("movement_cost_multiplier", 1.0)),
            environmental_stress=float(data.get("environmental_stress", 0.15)),
            births_this_season=int(data.get("births_this_season", 0)),
            deaths_this_season=int(data.get("deaths_this_season", 0)),
            vrancos_births_season=int(data.get("vrancos_births_season", 0)),
            vrancos_deaths_season=int(data.get("vrancos_deaths_season", 0)),
            predators_births_season=int(data.get("predators_births_season", 0)),
            predators_deaths_season=int(data.get("predators_deaths_season", 0)),
            food_consumed_season=float(data.get("food_consumed_season", 0.0)),
            food_spawned_season=float(data.get("food_spawned_season", 0.0)),
            season_history=list(data.get("season_history", [])),
        )
