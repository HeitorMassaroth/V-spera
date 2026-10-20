"""Testes unitários para os endpoints de exportação e restauração de snapshots completos."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_snapshot_export_and_restore():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Executa alguns passos para acumular estado
        step_resp = await client.post("/api/simulation/step")
        assert step_resp.status_code == 200

        # 2. Obtém snapshot completo do mundo
        snap_resp = await client.get("/api/simulation/snapshot")
        assert snap_resp.status_code == 200
        snapshot_data = snap_resp.json()

        assert "tick" in snapshot_data
        assert "width" in snapshot_data
        assert "height" in snapshot_data
        assert "organisms" in snapshot_data
        assert "foods" in snapshot_data
        assert "genealogy" in snapshot_data
        assert "chronicle" in snapshot_data

        saved_tick = snapshot_data["tick"]

        # 3. Avança a simulação mais 3 ticks
        for _ in range(3):
            await client.post("/api/simulation/step")

        later_state = await client.get("/api/simulation/state")
        assert later_state.json()["metrics"]["tick"] == saved_tick + 3

        # 4. Restaura o snapshot anterior
        restore_resp = await client.post("/api/simulation/restore-snapshot", json=snapshot_data)
        assert restore_resp.status_code == 200
        restore_json = restore_resp.json()
        assert restore_json["status"] == "ok"
        assert f"#{saved_tick}" in restore_json["message"]

        # 5. Verifica se o mundo retornou perfeitamente ao tick salvo
        restored_state = await client.get("/api/simulation/state")
        assert restored_state.json()["metrics"]["tick"] == saved_tick
