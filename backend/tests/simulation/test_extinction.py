"""Teste científico de extinção biológica controlada."""

import pytest
from core.world import World


def test_controlled_extinction_without_food():
    """Valida que em um ambiente sem regeneração de alimentos (R=0) e sem alimento inicial,

    a população inevitavelmente atinge a extinção por inanição.
    """
    initial_pop = 15
    world = World(
        width=600.0,
        height=600.0,
        seed=777,
        initial_organisms=initial_pop,
        initial_food=0,
        food_spawn_rate=0.0,
        max_food=0,
    )

    max_ticks = 4000
    extinct_tick = None

    for _ in range(max_ticks):
        metrics = world.step()
        if metrics["is_extinct"]:
            extinct_tick = metrics["tick"]
            break

    assert extinct_tick is not None, "A população deveria ter sido extinta por inanição."
    assert len(world.organisms) == 0
    assert world.total_deaths == initial_pop
    assert world.get_metrics()["is_extinct"] is True
