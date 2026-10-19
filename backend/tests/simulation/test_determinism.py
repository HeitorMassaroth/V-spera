"""Teste científico de determinismo estrito com sementes PRNG."""

import json
import hashlib
import pytest
from core.world import World


def compute_snapshot_hash(world: World) -> str:
    snapshot = world.to_snapshot()
    # Converte para JSON canônico ordenado
    dumped = json.dumps(snapshot, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def test_strict_prng_determinism():
    """Garante que duas simulações inicializadas com a mesma semente produzam exatamente o mesmo estado após N ciclos."""
    seed = 424242
    ticks_to_run = 150

    world_a = World(width=800.0, height=600.0, seed=seed, initial_organisms=30, initial_food=60)
    world_b = World(width=800.0, height=600.0, seed=seed, initial_organisms=30, initial_food=60)

    for _ in range(ticks_to_run):
        world_a.step()
        world_b.step()

    hash_a = compute_snapshot_hash(world_a)
    hash_b = compute_snapshot_hash(world_b)

    assert hash_a == hash_b
    assert world_a.tick == world_b.tick
    assert len(world_a.organisms) == len(world_b.organisms)
    assert len(world_a.foods) == len(world_b.foods)

    for oid, org_a in world_a.organisms.items():
        org_b = world_b.organisms[oid]
        assert org_a.x == org_b.x
        assert org_a.y == org_b.y
        assert org_a.vx == org_b.vx
        assert org_a.vy == org_b.vy
        assert org_a.energy == org_b.energy
        assert org_a.age == org_b.age


def test_different_seeds_produce_different_trajectories():
    """Garante que sementes distintas produzam trajetórias estocásticas divergentes."""
    world_a = World(width=800.0, height=600.0, seed=111, initial_organisms=20, initial_food=40)
    world_b = World(width=800.0, height=600.0, seed=222, initial_organisms=20, initial_food=40)

    for _ in range(50):
        world_a.step()
        world_b.step()

    hash_a = compute_snapshot_hash(world_a)
    hash_b = compute_snapshot_hash(world_b)

    assert hash_a != hash_b
