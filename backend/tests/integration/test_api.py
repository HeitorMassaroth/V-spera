"""Testes de integração para as rotas REST do FastAPI."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app, runner


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vespera-simulation-engine"


@pytest.mark.asyncio
async def test_simulation_control_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reset
        reset_res = await client.post(
            "/api/simulation/reset",
            json={"seed": 12345, "initial_organisms": 25, "initial_food": 50},
        )
        assert reset_res.status_code == 200
        assert reset_res.json()["metrics"]["tick"] == 0
        assert reset_res.json()["metrics"]["population"] == 25

        # 2. Step único
        step_res = await client.post("/api/simulation/step")
        assert step_res.status_code == 200
        assert step_res.json()["metrics"]["tick"] == 1

        # 3. Ajuste de velocidade
        speed_res = await client.post("/api/simulation/speed", json={"tps": 45})
        assert speed_res.status_code == 200
        assert speed_res.json()["tps"] == 45

        # 4. Iniciar simulação
        start_res = await client.post("/api/simulation/start")
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "RUNNING"

        # 5. Pausar simulação
        pause_res = await client.post("/api/simulation/pause")
        assert pause_res.status_code == 200
        assert pause_res.json()["status"] == "PAUSED"

        # 6. Consultar estado
        state_res = await client.get("/api/simulation/state")
        assert state_res.status_code == 200
        state_data = state_res.json()
        assert state_data["status"] == "PAUSED"
        assert state_data["seed"] == 12345
        assert state_data["tps"] == 45
