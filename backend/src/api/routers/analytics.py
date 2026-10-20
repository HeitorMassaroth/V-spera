"""Rotas REST analíticas para genealogia filogenética, linhagens e diversidade populacional."""

from __future__ import annotations
import logging
from typing import Dict, Any
from fastapi import APIRouter
from engine.runner import SimulationRunner

logger = logging.getLogger("vespera.api.analytics")

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def create_analytics_router(runner: SimulationRunner) -> APIRouter:
    """Fábrica de rotas analíticas avançadas."""

    @router.get("/phylogeny", response_model=Dict[str, Any])
    async def get_phylogeny():
        """Retorna o grafo filogenético completo com nós de animais, links ancestrais e linhagens."""
        living_ids = set(runner.world.organisms.keys())
        return runner.world.genealogy.get_phylogeny_tree(living_ids=living_ids)

    @router.get("/summary", response_model=Dict[str, Any])
    async def get_analytics_summary():
        """Retorna resumo estatístico consolidado de ecologia, diversidade e dinastia."""
        world = runner.world
        metrics = world.get_metrics()

        return {
            "tick": world.tick,
            "population": len(world.organisms),
            "food_count": len(world.foods),
            "evolution": metrics.get("evolution"),
            "ecology": metrics.get("ecology"),
            "season": metrics.get("season"),
            "attr_stats": metrics.get("attr_stats"),
        }

    return router
