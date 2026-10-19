"""Testes unitários e de estabilidade para Ciclos Ambientais e Equilíbrio Ecológico."""

import math
import pytest
from core.world import World
from core.entities.organism import Organism
from core.entities.genetics import Genotype, AllelePair
from core.entities.environment import SeasonType, SEASON_ORDER, SEASON_METADATA
from core.systems.environment_system import EnvironmentSystem
from core.systems.metabolism import MetabolismSystem
from core.prng import PRNG


def test_seasonal_cycle_progression():
    """Valida a progressão contínua das 4 estações e avanço de ano."""
    env = EnvironmentSystem(season_duration_ticks=100)
    events = []

    # Tick 0: Primavera, Ano 1
    env.update(0, {}, {}, events)
    assert env.state.season == SeasonType.SPRING
    assert env.state.year == 1
    assert env.state.season_tick == 0
    assert env.state.season_progress == 0.0

    # Tick 100: Transição para Verão
    env.update(100, {}, {}, events)
    assert env.state.season == SeasonType.SUMMER
    assert env.state.year == 1
    assert any(e["type"] == "season_changed" and e["season"] == "SUMMER" for e in events)

    # Tick 200: Outono
    env.update(200, {}, {}, events)
    assert env.state.season == SeasonType.AUTUMN

    # Tick 300: Inverno
    env.update(300, {}, {}, events)
    assert env.state.season == SeasonType.WINTER

    # Tick 400: Retorno à Primavera, Ano 2
    env.update(400, {}, {}, events)
    assert env.state.season == SeasonType.SPRING
    assert env.state.year == 2
    assert len(env.state.season_history) >= 4


def test_continuous_smooth_interpolation():
    """Verifica que os parâmetros climáticos não saltam abruptamente e seguem interpolação senoidal suave."""
    env = EnvironmentSystem(season_duration_ticks=100)
    events = []

    # Início da Primavera
    env.update(0, {}, {}, events)
    spring_temp = env.state.temperature
    spring_food_mult = env.state.food_spawn_multiplier

    # Meio da Primavera (tick 50)
    env.update(50, {}, {}, events)
    mid_temp = env.state.temperature
    mid_food_mult = env.state.food_spawn_multiplier

    # Verão puro (tick 100)
    env.update(100, {}, {}, events)
    summer_temp = env.state.temperature

    # Temperatura deve subir suavemente de primavera (20°C) para verão (28°C)
    assert spring_temp < mid_temp < summer_temp
    # Multiplicador alimentar da primavera (1.30) deve decair suavemente para o do verão (1.10)
    assert spring_food_mult > mid_food_mult > env.state.food_spawn_multiplier


def test_winter_thermoregulation_and_genetic_insulation():
    """Valida que o frio do inverno aumenta o gasto metabólico, mas organismos com resistência e adaptabilidade são amortecidos."""
    metabolism = MetabolismSystem()

    # Organismo frágil ao frio
    org_fragile = Organism(
        id=1,
        x=100.0,
        y=100.0,
        vx=0.0,
        vy=0.0,
        genome=Genotype(
            resistencia_pair=AllelePair(15.0, 15.0),
            adaptabilidade_pair=AllelePair(15.0, 15.0),
        ),
    )

    # Organismo resistente ao frio
    org_hardy = Organism(
        id=2,
        x=100.0,
        y=100.0,
        vx=0.0,
        vy=0.0,
        genome=Genotype(
            resistencia_pair=AllelePair(95.0, 95.0),
            adaptabilidade_pair=AllelePair(95.0, 95.0),
        ),
    )

    # Custo em temperatura amena (20°C)
    cost_fragile_spring = metabolism.calculate_cost(org_fragile, dt=1.0, season_metabolic_mult=1.0, temperature=20.0)
    cost_hardy_spring = metabolism.calculate_cost(org_hardy, dt=1.0, season_metabolic_mult=1.0, temperature=20.0)

    # Custo no inverno rigoroso (6°C) com multiplicador metabólico de inverno (1.20)
    cost_fragile_winter = metabolism.calculate_cost(org_fragile, dt=1.0, season_metabolic_mult=1.20, temperature=6.0)
    cost_hardy_winter = metabolism.calculate_cost(org_hardy, dt=1.0, season_metabolic_mult=1.20, temperature=6.0)

    # O custo no inverno deve ser superior ao da primavera para ambos
    assert cost_fragile_winter > cost_fragile_spring
    assert cost_hardy_winter > cost_hardy_spring

    # O impacto do frio deve ser menor no organismo adaptado/resistente
    delta_fragile = cost_fragile_winter - cost_fragile_spring
    delta_hardy = cost_hardy_winter - cost_hardy_spring
    assert delta_hardy < delta_fragile


def test_seasonal_reproduction_thresholds():
    """Valida que a reprodução exige maior superávit no inverno e é facilitada na primavera sem mortes arbitrárias."""
    spring_mult = SEASON_METADATA[SeasonType.SPRING]["reproduction_cost_mult"]
    winter_mult = SEASON_METADATA[SeasonType.WINTER]["reproduction_cost_mult"]

    assert spring_mult < 1.0 < winter_mult


def test_carrying_capacity_and_resource_recovery():
    """Valida que o ecossistema rastreia capacidade de suporte, biomassa e recuperação de recursos."""
    world = World(
        width=500.0,
        height=500.0,
        seed=999,
        initial_organisms=10,
        initial_predators=5,
        initial_vrancos=5,
        initial_food=25,
        food_spawn_rate=0.5,
    )

    metrics = world.get_metrics()
    assert "season" in metrics
    assert "ecology" in metrics
    assert metrics["season"]["season"] == "SPRING"
    assert metrics["ecology"]["carrying_capacity"] > 0
    assert metrics["ecology"]["total_biomass"] > 0

    # Simula 30 ciclos para verificar acumulação e dinâmica
    for _ in range(30):
        world.step()

    metrics_after = world.get_metrics()
    assert world.tick == 30
    assert metrics_after["season"]["tick"] == 29
    assert metrics_after["ecology"]["total_biomass"] > 0


def test_coexistence_and_no_instant_extinction():
    """Valida que a passagem do tempo e as estações não extinguem sumariamente a população."""
    world = World(
        width=600.0,
        height=600.0,
        seed=42,
        initial_organisms=16,
        initial_predators=8,
        initial_vrancos=8,
        initial_food=35,
        food_spawn_rate=0.8,
    )

    # Roda uma estação completa (251 ticks para cruzar para o verão)
    for _ in range(251):
        state = world.step()
        if state["population"] == 0:
            break

    # Não deve haver extinção instantânea ou arbitrária
    metrics = world.get_metrics()
    assert metrics["population"] > 0, "A população não deve ser extinta arbitrariamente no primeiro ciclo sazonal"
    assert metrics["season"]["season"] == "SUMMER", "Deve ter completado a primavera e ingressado no verão"
