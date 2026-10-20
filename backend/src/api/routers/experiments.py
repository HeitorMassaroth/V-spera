"""Rotas REST para persistência, gerenciamento de ensaios e snapshots no banco SQLite."""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from infrastructure.services.experiment_service import ExperimentService
from api.schemas.experiment import (
    ExperimentCreate,
    ExperimentSummary,
    ExperimentDetail,
    SnapshotCreateResponse,
    RestoreResponse,
)
from engine.runner import SimulationRunner
from core.world import World

logger = logging.getLogger("vespera.api.experiments")

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def create_experiment_router(runner: SimulationRunner) -> APIRouter:
    """Fábrica de rotas de experimentos com injeção de dependência do SimulationRunner."""

    @router.post("", response_model=Dict[str, Any])
    async def create_experiment(payload: ExperimentCreate):
        """Salva o estado atual da simulação como um novo experimento no banco SQLite."""
        try:
            result = await ExperimentService.save_experiment(
                name=payload.name,
                world=runner.world,
                description=payload.description,
                status=runner.status,
            )
            return result
        except Exception as e:
            logger.exception("Falha ao salvar experimento no SQLite")
            raise HTTPException(status_code=500, detail=f"Erro ao salvar experimento: {str(e)}")

    @router.get("", response_model=List[ExperimentSummary])
    async def list_experiments():
        """Lista todos os experimentos salvos no banco de dados SQLite."""
        try:
            return await ExperimentService.list_experiments()
        except Exception as e:
            logger.exception("Falha ao listar experimentos")
            raise HTTPException(status_code=500, detail=f"Erro ao listar experimentos: {str(e)}")

    @router.get("/{experiment_id}", response_model=ExperimentDetail)
    async def get_experiment(experiment_id: str):
        """Obtém detalhes do experimento e lista de snapshots salvos."""
        exp = await ExperimentService.get_experiment(experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Experimento não encontrado no banco de dados.")
        return exp

    @router.post("/{experiment_id}/snapshots", response_model=SnapshotCreateResponse)
    async def save_snapshot(experiment_id: str):
        """Grava um novo ponto de restauração (checkpoint) comprimido com zlib para o experimento."""
        try:
            return await ExperimentService.save_snapshot_checkpoint(experiment_id, runner.world)
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logger.exception("Falha ao salvar checkpoint")
            raise HTTPException(status_code=500, detail=f"Erro ao salvar checkpoint: {str(e)}")

    @router.post("/{experiment_id}/restore", response_model=RestoreResponse)
    async def restore_experiment(
        experiment_id: str,
        snapshot_id: Optional[int] = Query(default=None, description="ID do snapshot específico ou o mais recente"),
    ):
        """Restaura o ecossistema ativo a partir do snapshot gravado no banco de dados SQLite."""
        try:
            snapshot_dict = await ExperimentService.load_experiment_snapshot(experiment_id, snapshot_id)
            restored_world = World.from_snapshot(snapshot_dict)
            metrics = await runner.restore_world(restored_world)

            return RestoreResponse(
                status="ok",
                message=f"Experimento restaurado com sucesso no ciclo #{restored_world.tick}",
                metrics=metrics,
            )
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logger.exception("Falha ao restaurar experimento")
            raise HTTPException(status_code=500, detail=f"Erro ao restaurar experimento: {str(e)}")

    @router.delete("/{experiment_id}", response_model=Dict[str, Any])
    async def delete_experiment(experiment_id: str):
        """Exclui o experimento e todos os seus snapshots e séries temporais do SQLite."""
        deleted = await ExperimentService.delete_experiment(experiment_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Experimento não encontrado para exclusão.")
        return {"status": "ok", "message": f"Experimento {experiment_id} excluído com sucesso."}

    return router
