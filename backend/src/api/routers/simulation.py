"""Rotas de controle e canais WebSocket da simulação."""

from __future__ import annotations
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from api.schemas.control import ResetParams, SpeedParams, SimulationStatusResponse
from engine.runner import SimulationRunner
from api.websocket_manager import WebSocketManager

logger = logging.getLogger("vespera.api")

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def create_simulation_router(
    runner: SimulationRunner,
    ws_manager: WebSocketManager,
) -> APIRouter:
    """Fábrica de rotas com injeção de dependências do runner e websocket manager."""

    @router.post("/start", response_model=Dict[str, Any])
    async def start_simulation():
        await runner.start()
        return {"status": runner.status, "message": "Simulação iniciada."}

    @router.post("/pause", response_model=Dict[str, Any])
    async def pause_simulation():
        await runner.pause()
        return {"status": runner.status, "message": "Simulação pausada."}

    @router.post("/step", response_model=Dict[str, Any])
    async def step_simulation():
        metrics = await runner.step()
        return {"status": runner.status, "metrics": metrics}

    @router.post("/reset", response_model=Dict[str, Any])
    async def reset_simulation(params: ResetParams):
        metrics = await runner.reset(
            seed=params.seed,
            width=params.width,
            height=params.height,
            initial_organisms=params.initial_organisms,
            initial_food=params.initial_food,
            food_spawn_rate=params.food_spawn_rate,
            max_food=params.max_food,
        )
        return {"status": runner.status, "metrics": metrics}

    @router.post("/speed", response_model=Dict[str, Any])
    async def set_speed(params: SpeedParams):
        new_tps = runner.set_tps(params.tps)
        return {"tps": new_tps}

    @router.get("/state", response_model=SimulationStatusResponse)
    async def get_state():
        return SimulationStatusResponse(
            status=runner.status,
            tps=runner.tps,
            metrics=runner.world.get_metrics(),
            width=runner.world.width,
            height=runner.world.height,
            seed=runner.world.seed,
        )

    # Rota WebSocket
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            # Envia estado inicial imediato
            initial_state = runner.world.get_compact_state()
            initial_state["status"] = runner.status
            initial_state["tps"] = runner.tps
            await websocket.send_text(json.dumps(initial_state))

            while True:
                data_text = await websocket.receive_text()
                try:
                    data = json.loads(data_text)
                    action = data.get("action")
                    if action == "start":
                        await runner.start()
                    elif action == "pause":
                        await runner.pause()
                    elif action == "step":
                        await runner.step()
                    elif action == "reset":
                        await runner.reset(seed=data.get("seed"))
                    elif action == "set_speed":
                        if "tps" in data:
                            runner.set_tps(int(data["tps"]))
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            logger.warning(f"Exceção no WebSocket: {e}")
            ws_manager.disconnect(websocket)

    return router
