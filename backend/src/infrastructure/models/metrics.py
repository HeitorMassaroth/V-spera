"""Modelo ORM para séries temporais de métricas de simulação."""

from __future__ import annotations
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Index
from ..database import Base


class TickMetricsModel(Base):
    __tablename__ = "tick_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    tick = Column(Integer, nullable=False)
    population = Column(Integer, nullable=False)
    food_count = Column(Integer, nullable=False)
    avg_energy = Column(Float, nullable=False)
    avg_speed = Column(Float, nullable=False)
    avg_age = Column(Float, nullable=False)
    max_age = Column(Integer, nullable=False)
    total_births = Column(Integer, nullable=False)
    total_deaths = Column(Integer, nullable=False)
    total_food_consumed = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_experiment_tick", "experiment_id", "tick"),
    )
