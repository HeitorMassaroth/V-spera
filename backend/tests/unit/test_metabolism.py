"""Testes unitários do sistema metabólico e balanço energético."""

import pytest
from core.entities.organism import Organism
from core.entities.traits import OrganismTraits
from core.entities.food import Food
from core.spatial.spatial_grid import SpatialHashGrid
from core.systems.metabolism import MetabolismSystem


def test_metabolic_cost_increases_with_speed():
    metabolism = MetabolismSystem()
    traits = OrganismTraits(size=5.0)

    org_stopped = Organism(id=1, x=100.0, y=100.0, vx=0.0, vy=0.0, traits=traits)
    org_moving = Organism(id=2, x=100.0, y=100.0, vx=2.0, vy=0.0, traits=traits)

    cost_stopped = metabolism.calculate_cost(org_stopped)
    cost_moving = metabolism.calculate_cost(org_moving)

    assert cost_moving > cost_stopped


def test_energy_deduction():
    metabolism = MetabolismSystem()
    org = Organism(id=1, x=50.0, y=50.0, energy=100.0)
    initial_energy = org.energy

    cost = metabolism.apply_metabolism(org)
    assert org.energy == initial_energy - cost


def test_feeding_consumption():
    metabolism = MetabolismSystem()
    org = Organism(id=1, x=50.0, y=50.0, energy=50.0)
    food = Food(id=10, x=51.0, y=50.0, energy_value=40.0)

    food_grid = SpatialHashGrid[Food]()
    food_grid.insert(food, food.x, food.y)

    consumed = metabolism.process_feeding(org, food_grid)
    assert len(consumed) == 1
    assert consumed[0].id == 10
    assert org.energy == 90.0
    assert org.food_eaten == 1


def test_mortality_by_starvation():
    metabolism = MetabolismSystem()
    org = Organism(id=1, x=50.0, y=50.0, energy=0.0)

    survived = metabolism.check_survival(org)
    assert not survived
    assert not org.alive


def test_mortality_by_senescence():
    metabolism = MetabolismSystem()
    traits = OrganismTraits(max_age=100)
    org = Organism(id=1, x=50.0, y=50.0, energy=50.0, age=99, traits=traits)

    survived = metabolism.check_survival(org)
    assert not survived
    assert not org.alive
