"""Modelo ORM para snapshots de ponto no tempo da simulação."""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, DateTime
from ..database import Base


class SimulationSnapshotModel(Base):
    __tablename__ = "simulation_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    tick = Column(Integer, nullable=False)
    compressed_state = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
