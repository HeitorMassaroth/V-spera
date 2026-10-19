"""Testes unitários da estrutura de dados SpatialHashGrid."""

import math
import pytest
from core.spatial.spatial_grid import SpatialHashGrid


def test_spatial_grid_insertion_and_query():
    grid = SpatialHashGrid[str](cell_size=50.0)
    grid.insert("itemA", 10.0, 10.0)
    grid.insert("itemB", 20.0, 20.0)
    grid.insert("itemC", 200.0, 200.0)

    # Consulta ao redor de (15, 15) com raio 20
    results = grid.query_radius(15.0, 15.0, radius=20.0)
    items = [item for item, _ in results]

    assert "itemA" in items
    assert "itemB" in items
    assert "itemC" not in items


def test_spatial_grid_nearest_query():
    grid = SpatialHashGrid[str](cell_size=40.0)
    grid.insert("itemFar", 100.0, 100.0)
    grid.insert("itemClose", 10.0, 10.0)

    nearest, dist = grid.query_nearest(0.0, 0.0, max_radius=150.0)
    assert nearest == "itemClose"
    assert math.isclose(dist, math.hypot(10.0, 10.0), rel_tol=1e-5)


def test_spatial_grid_clear():
    grid = SpatialHashGrid[int](cell_size=30.0)
    grid.insert(1, 10.0, 10.0)
    grid.insert(2, 20.0, 20.0)
    assert grid.item_count == 2

    grid.clear()
    assert grid.item_count == 0
    assert len(grid.query_radius(15.0, 15.0, 50.0)) == 0


def test_spatial_grid_matches_brute_force():
    """Garante que a busca indexada em grid retorne exatamente os mesmos itens que a busca linear ingênua."""
    import random
    rng = random.Random(12345)
    grid = SpatialHashGrid[int](cell_size=50.0)

    points = [(i, rng.uniform(0, 500), rng.uniform(0, 500)) for i in range(100)]
    for pid, px, py in points:
        grid.insert(pid, px, py)

    query_x = 250.0
    query_y = 250.0
    query_radius = 80.0

    # Força bruta O(N)
    brute_force = []
    for pid, px, py in points:
        d = math.hypot(px - query_x, py - query_y)
        if d <= query_radius:
            brute_force.append(pid)

    # Grid O(1)
    grid_results = [item for item, _ in grid.query_radius(query_x, query_y, query_radius)]

    assert sorted(brute_force) == sorted(grid_results)
