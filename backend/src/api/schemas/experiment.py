"""Schemas Pydantic para o gerenciamento de experimentos e persistência no banco SQLite."""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome identificador do ensaio científico")
    description: Optional[str] = Field(default=None, max_length=500, description="Hipótese ou descrição do experimento")


class SnapshotSummary(BaseModel):
    id: int
    tick: int
    created_at: Optional[str] = None


class ExperimentSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    seed: Optional[int] = None
    status: str
    latest_tick: int
    world_width: float
    world_height: float
    created_at: Optional[str] = None


class ExperimentDetail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    seed: Optional[int] = None
    world_width: float
    world_height: float
    initial_organisms: int
    initial_food: int
    food_spawn_rate: float
    max_food: int
    status: str
    created_at: Optional[str] = None
    snapshots: List[SnapshotSummary] = []


class SnapshotCreateResponse(BaseModel):
    snapshot_id: int
    experiment_id: str
    tick: int
    size_bytes: int
    created_at: str


class RestoreResponse(BaseModel):
    status: str
    message: str
    metrics: Dict[str, Any]
