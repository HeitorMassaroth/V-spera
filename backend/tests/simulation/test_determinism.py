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


def test_complete_snapshot_roundtrip_restoration():
    """Garante fidelidade de 100% no snapshot/restore, preservando clãs, famílias, ninhos, territórios e trajetória idêntica."""
    world = World(width=1000.0, height=700.0, seed=777, initial_organisms=40, initial_food=80)

    # Executa ciclos suficientes para formar famílias, ninhos, clãs e territórios
    for _ in range(80):
        world.step()

    snapshot = world.to_snapshot()
    assert "families" in snapshot
    assert "nests" in snapshot
    assert "clans" in snapshot
    assert "territories" in snapshot
    assert "family_coop" in snapshot

    # Restaura novo mundo
    restored = World.from_snapshot(snapshot)

    assert restored.tick == world.tick
    assert len(restored.organisms) == len(world.organisms)
    assert len(restored.foods) == len(world.foods)
    assert len(restored.family_system.families) == len(world.family_system.families)
    assert len(restored.family_system.nests) == len(world.family_system.nests)
    assert len(restored.clan_system.clans) == len(world.clan_system.clans)
    assert len(restored.territory_system.zones) == len(world.territory_system.zones)

    # Grids espaciais re-populados
    assert restored.food_grid.item_count == len(world.foods)
    assert restored.organism_grid.item_count == len(world.organisms)

    # Ambos os mundos devem prosseguir de forma 100% idêntica por mais 30 ciclos
    for _ in range(30):
        world.step()
        restored.step()

    assert compute_snapshot_hash(world) == compute_snapshot_hash(restored)

