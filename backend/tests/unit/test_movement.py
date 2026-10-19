"""Testes unitários de cinemática e forças de navegação (Reynolds)."""

import math
import pytest
from core.entities.organism import Organism
from core.entities.traits import OrganismTraits
from core.systems.movement import MovementSystem


def test_velocity_is_clamped_to_max_speed():
    movement = MovementSystem(world_width=500.0, world_height=500.0)
    traits = OrganismTraits(max_speed=3.0, max_force=5.0)
    org = Organism(id=1, x=250.0, y=250.0, vx=0.0, vy=0.0, traits=traits)

    # Força massiva aplicada
    movement.update_physics(org, force_x=100.0, force_y=100.0)
    assert org.speed <= traits.max_speed + 1e-6


def test_boundary_repulsion_keeps_organism_inside():
    movement = MovementSystem(world_width=500.0, world_height=500.0, boundary_margin=40.0)
    # Organismo muito perto da borda esquerda
    org = Organism(id=1, x=5.0, y=250.0, vx=-2.0, vy=0.0)

    fx, fy = movement._boundary_repulsion(org)
    assert fx > 0.0  # Força positiva empurrando para a direita


def test_seek_force_points_towards_target():
    movement = MovementSystem(world_width=500.0, world_height=500.0)
    org = Organism(id=1, x=100.0, y=100.0, vx=0.0, vy=0.0)

    fx, fy = movement._seek(org, target_x=200.0, target_y=100.0)
    assert fx > 0.0
    assert math.isclose(fy, 0.0, abs_tol=1e-5)
