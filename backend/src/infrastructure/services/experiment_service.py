"""Serviço de persistência assíncrona SQLite para experimentos, snapshots e métricas do VÉSPERA."""

from __future__ import annotations
import json
import zlib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, delete, desc

from infrastructure.database import AsyncSessionLocal
from infrastructure.models.experiment import ExperimentModel
from infrastructure.models.snapshot import SimulationSnapshotModel
from infrastructure.models.metrics import TickMetricsModel
from core.world import World

logger = logging.getLogger("vespera.services.experiment")


class ExperimentService:
    """Gerencia o ciclo de vida e persistência no banco SQLite de ensaios e snapshots contrafactuais."""

    @staticmethod
    async def save_experiment(
        name: str,
        world: World,
        description: Optional[str] = None,
        status: str = "PAUSED",
    ) -> Dict[str, Any]:
        """Cria ou salva um novo experimento com snapshot inicial compactado com zlib."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                experiment = ExperimentModel(
                    name=name,
                    description=description,
                    seed=world.seed,
                    world_width=world.width,
                    world_height=world.height,
                    initial_organisms=len(world.organisms),
                    initial_food=len(world.foods),
                    food_spawn_rate=world.food_spawn_rate,
                    max_food=world.max_food,
                    status=status,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(experiment)
                await session.flush()

                # Compactação determinística de snapshot via Zlib
                snapshot_dict = world.to_snapshot()
                json_bytes = json.dumps(snapshot_dict).encode("utf-8")
                compressed = zlib.compress(json_bytes, level=6)

                snapshot_entry = SimulationSnapshotModel(
                    experiment_id=experiment.id,
                    tick=world.tick,
                    compressed_state=compressed,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(snapshot_entry)

            logger.info(
                f"Experimento '{name}' (ID: {experiment.id}) salvo com snapshot no ciclo #{world.tick} "
                f"(Bytes: {len(json_bytes)} -> {len(compressed)} comprimido)."
            )

            return {
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "seed": experiment.seed,
                "tick": world.tick,
                "created_at": experiment.created_at.isoformat(),
                "status": experiment.status,
                "population": len(world.organisms),
                "food_count": len(world.foods),
            }

    @staticmethod
    async def list_experiments() -> List[Dict[str, Any]]:
        """Lista todos os experimentos salvos no banco SQLite ordenados por data decrescente."""
        async with AsyncSessionLocal() as session:
            stmt = select(ExperimentModel).order_by(desc(ExperimentModel.created_at))
            result = await session.execute(stmt)
            experiments = result.scalars().all()

            results = []
            for exp in experiments:
                snap_stmt = (
                    select(SimulationSnapshotModel.tick)
                    .where(SimulationSnapshotModel.experiment_id == exp.id)
                    .order_by(desc(SimulationSnapshotModel.tick))
                    .limit(1)
                )
                snap_res = await session.execute(snap_stmt)
                latest_tick = snap_res.scalar_one_or_none() or 0

                results.append({
                    "id": exp.id,
                    "name": exp.name,
                    "description": exp.description,
                    "seed": exp.seed,
                    "created_at": exp.created_at.isoformat() if exp.created_at else None,
                    "status": exp.status,
                    "latest_tick": latest_tick,
                    "world_width": exp.world_width,
                    "world_height": exp.world_height,
                })
            return results

    @staticmethod
    async def get_experiment(experiment_id: str) -> Optional[Dict[str, Any]]:
        """Recupera detalhes de um experimento específico e a contagem de checkpoints gravados."""
        async with AsyncSessionLocal() as session:
            stmt = select(ExperimentModel).where(ExperimentModel.id == experiment_id)
            result = await session.execute(stmt)
            exp = result.scalar_one_or_none()
            if not exp:
                return None

            snap_stmt = (
                select(SimulationSnapshotModel.id, SimulationSnapshotModel.tick, SimulationSnapshotModel.created_at)
                .where(SimulationSnapshotModel.experiment_id == exp.id)
                .order_by(desc(SimulationSnapshotModel.tick))
            )
            snap_res = await session.execute(snap_stmt)
            snapshots = [
                {
                    "id": row.id,
                    "tick": row.tick,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in snap_res.all()
            ]

            return {
                "id": exp.id,
                "name": exp.name,
                "description": exp.description,
                "seed": exp.seed,
                "world_width": exp.world_width,
                "world_height": exp.world_height,
                "initial_organisms": exp.initial_organisms,
                "initial_food": exp.initial_food,
                "food_spawn_rate": exp.food_spawn_rate,
                "max_food": exp.max_food,
                "status": exp.status,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "snapshots": snapshots,
            }

    @staticmethod
    async def save_snapshot_checkpoint(experiment_id: str, world: World) -> Dict[str, Any]:
        """Salva um novo ponto de restauração (checkpoint) comprimido para o experimento."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = select(ExperimentModel).where(ExperimentModel.id == experiment_id)
                exp = (await session.execute(stmt)).scalar_one_or_none()
                if not exp:
                    raise ValueError(f"Experimento {experiment_id} não encontrado.")

                snapshot_dict = world.to_snapshot()
                json_bytes = json.dumps(snapshot_dict).encode("utf-8")
                compressed = zlib.compress(json_bytes, level=6)

                snapshot_entry = SimulationSnapshotModel(
                    experiment_id=experiment_id,
                    tick=world.tick,
                    compressed_state=compressed,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(snapshot_entry)
                await session.flush()

                return {
                    "snapshot_id": snapshot_entry.id,
                    "experiment_id": experiment_id,
                    "tick": world.tick,
                    "size_bytes": len(compressed),
                    "created_at": snapshot_entry.created_at.isoformat(),
                }

    @staticmethod
    async def load_experiment_snapshot(experiment_id: str, snapshot_id: Optional[int] = None) -> Dict[str, Any]:
        """Recupera e descomprime um snapshot de simulação salvo no banco de dados SQLite."""
        async with AsyncSessionLocal() as session:
            if snapshot_id is not None:
                stmt = (
                    select(SimulationSnapshotModel)
                    .where(
                        SimulationSnapshotModel.experiment_id == experiment_id,
                        SimulationSnapshotModel.id == snapshot_id,
                    )
                )
            else:
                stmt = (
                    select(SimulationSnapshotModel)
                    .where(SimulationSnapshotModel.experiment_id == experiment_id)
                    .order_by(desc(SimulationSnapshotModel.tick))
                    .limit(1)
                )

            res = await session.execute(stmt)
            entry = res.scalar_one_or_none()
            if not entry:
                raise ValueError(f"Nenhum snapshot encontrado para o experimento {experiment_id}.")

            decompressed = zlib.decompress(entry.compressed_state)
            snapshot_dict = json.loads(decompressed.decode("utf-8"))
            return snapshot_dict

    @staticmethod
    async def delete_experiment(experiment_id: str) -> bool:
        """Exclui um experimento e todos os seus snapshots e métricas em cascata."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = delete(ExperimentModel).where(ExperimentModel.id == experiment_id)
                res = await session.execute(stmt)
                return res.rowcount > 0
