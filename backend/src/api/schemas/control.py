"""Schemas Pydantic para validação e serialização da API."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ResetParams(BaseModel):
    seed: Optional[int] = Field(default=None, description="Semente do gerador pseudo-aleatório")
    width: Optional[float] = Field(default=1200.0, ge=400.0, le=4000.0)
    height: Optional[float] = Field(default=800.0, ge=300.0, le=3000.0)
    initial_organisms: Optional[int] = Field(default=None, ge=0, le=500)
    initial_predator_females: Optional[int] = Field(default=None, ge=0, le=100)
    initial_predator_males: Optional[int] = Field(default=None, ge=0, le=100)
    initial_vranco_females: Optional[int] = Field(default=None, ge=0, le=100)
    initial_vranco_males: Optional[int] = Field(default=None, ge=0, le=100)
    initial_food: Optional[int] = Field(default=120, ge=0, le=1000)
    food_spawn_rate: Optional[float] = Field(default=1.8, ge=0.0, le=20.0)
    max_food: Optional[int] = Field(default=250, ge=10, le=1500)


class SpeedParams(BaseModel):
    tps: int = Field(default=30, ge=1, le=60, description="Ticks por segundo")


class SimulationStatusResponse(BaseModel):
    status: str
    tps: int
    metrics: Dict[str, Any]
    width: float
    height: float
    seed: Optional[int]
