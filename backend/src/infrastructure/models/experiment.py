"""Modelo ORM para experimentos salvos."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime
from ..database import Base


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    seed = Column(Integer, nullable=True)
    world_width = Column(Float, nullable=False, default=1200.0)
    world_height = Column(Float, nullable=False, default=800.0)
    initial_organisms = Column(Integer, nullable=False, default=50)
    initial_food = Column(Integer, nullable=False, default=120)
    food_spawn_rate = Column(Float, nullable=False, default=1.8)
    max_food = Column(Integer, nullable=False, default=250)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="PAUSED")
