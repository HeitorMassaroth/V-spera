"""Testes unitários para o endpoint de inspeção detalhada e genealogia do organismo."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_get_organism_details_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Obtém estado inicial para pegar o ID de um organismo existente
        state_resp = await client.get("/api/simulation/state")
        assert state_resp.status_code == 200

        # Pega a árvore e status do primeiro organismo (ID 1)
        resp = await client.get("/api/simulation/organism/1")
        assert resp.status_code == 200
        data = resp.json()

        assert "family_tree" in data
        assert "is_alive" in data
        assert "current_stats" in data
        assert "population_averages" in data

        tree = data["family_tree"]
        assert "animal" in tree
        animal = tree["animal"]
        assert animal["id"] == 1
        assert "genome" in animal
        assert "forca" in animal["genome"]
        assert "velocidade" in animal["genome"]
        assert "resistencia" in animal["genome"]
        assert "inteligencia" in animal["genome"]
        assert "max_saude" in animal["genome"]

        # Testa animal inexistente
        not_found_resp = await client.get("/api/simulation/organism/999999")
        assert not_found_resp.status_code == 404
