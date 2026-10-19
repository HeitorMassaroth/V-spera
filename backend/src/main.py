"""Ponto de entrada principal do servidor FastAPI — VÉSPERA."""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.websocket_manager import WebSocketManager
from engine.runner import SimulationRunner
from api.routers.simulation import create_simulation_router

from infrastructure.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vespera")

# Instâncias globais da aplicação
ws_manager = WebSocketManager()
runner = SimulationRunner(broadcast_callback=ws_manager.broadcast)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciador de ciclo de vida do servidor (inicialização e encerramento limpo)."""
    logger.info("Iniciando motor de simulação VÉSPERA...")
    await init_db()
    yield
    logger.info("Encerrando motor de simulação VÉSPERA...")
    await runner.stop()


app = FastAPI(
    title="VÉSPERA API",
    description="Motor de Simulação de Vida Artificial e Ecossistemas Computacionais",
    version="0.1.0",
    lifespan=lifespan,
)

# Configuração de CORS permissivo para desenvolvimento local (Vite/React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas
app.include_router(create_simulation_router(runner, ws_manager))


@app.get("/api/health")
async def health_check():
    """Endpoint de verificação de integridade da API."""
    return {
        "status": "healthy",
        "service": "vespera-simulation-engine",
        "simulation_status": runner.status,
        "tick": runner.world.tick,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
