"""Testes unitários para persistência de experimentos, listagem e snapshots no banco SQLite."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from infrastructure.database import init_db


@pytest.mark.asyncio
async def test_experiment_sqlite_lifecycle():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Executa alguns passos de simulação
        await client.post("/api/simulation/step")
        await client.post("/api/simulation/step")

        # 2. Salva o experimento no banco de dados SQLite
        create_payload = {
            "name": "Ensaio Evolutivo Pioneiro #1",
            "description": "Teste de viabilidade sob regime de seleção natural estrita",
        }
        create_resp = await client.post("/api/experiments", json=create_payload)
        assert create_resp.status_code == 200
        exp_data = create_resp.json()
        assert "id" in exp_data
        assert exp_data["name"] == create_payload["name"]
        exp_id = exp_data["id"]

        # 3. Lista experimentos no banco
        list_resp = await client.get("/api/experiments")
        assert list_resp.status_code == 200
        experiments = list_resp.json()
        assert any(e["id"] == exp_id for e in experiments)

        # 4. Obtém detalhes do experimento salvo
        get_resp = await client.get(f"/api/experiments/{exp_id}")
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["id"] == exp_id
        assert len(detail["snapshots"]) >= 1

        # 5. Salva um novo checkpoint para este experimento
        await client.post("/api/simulation/step")
        snap_resp = await client.post(f"/api/experiments/{exp_id}/snapshots")
        assert snap_resp.status_code == 200
        snap_data = snap_resp.json()
        assert snap_data["experiment_id"] == exp_id
        assert snap_data["size_bytes"] > 0

        # 6. Restaura o experimento salvo no banco SQLite
        restore_resp = await client.post(f"/api/experiments/{exp_id}/restore")
        assert restore_resp.status_code == 200
        restore_data = restore_resp.json()
        assert restore_data["status"] == "ok"

        # 7. Exclui o experimento do SQLite
        del_resp = await client.delete(f"/api/experiments/{exp_id}")
        assert del_resp.status_code == 200

        # 8. Confirma que foi excluído
        not_found = await client.get(f"/api/experiments/{exp_id}")
        assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_analytics_phylogeny_and_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Testa rota de filogenia
        phy_resp = await client.get("/api/analytics/phylogeny")
        assert phy_resp.status_code == 200
        phy_data = phy_resp.json()
        assert "nodes" in phy_data
        assert "links" in phy_data
        assert "lineages" in phy_data
        assert "max_generation" in phy_data

        # Testa rota de sumário analítico
        summary_resp = await client.get("/api/analytics/summary")
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        assert "tick" in summary_data
        assert "population" in summary_data
        assert "evolution" in summary_data
