"""Rotas de controle e canais WebSocket da simulação."""

from __future__ import annotations
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from api.schemas.control import ResetParams, SpeedParams, SimulationStatusResponse
from engine.runner import SimulationRunner
from api.websocket_manager import WebSocketManager
from core.entities.clan import calculate_leadership_score

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

    @router.get("/organism/{organism_id}", response_model=Dict[str, Any])
    async def get_organism_details(organism_id: int):
        family_tree = runner.world.genealogy.get_family_tree(organism_id)
        if not family_tree:
            raise HTTPException(status_code=404, detail="Animal não encontrado no registro genealógico.")

        is_alive = organism_id in runner.world.organisms
        current_stats = None
        nest_info = None

        if is_alive:
            org = runner.world.organisms[organism_id]
            bond_duration = (runner.world.tick - org.partner_bond_tick) if org.partner_bond_tick is not None else 0
            if org.nest_id and org.nest_id in runner.world.family_system.nests:
                nest_info = runner.world.family_system.nests[org.nest_id].to_dict()

            current_stats = {
                "age": org.age,
                "saude": round(org.saude, 1),
                "energy": round(org.energy, 1),
                "hunger": round(org.hunger, 1),
                "x": round(org.x, 2),
                "y": round(org.y, 2),
                "role": org.role,
                "sex": org.sex,
                "life_stage": org.life_stage,
                "life_expectancy": org.life_expectancy,
                "current_state": org.current_state,
                "carried_food": round(org.carried_food, 1),
                "partner_id": org.partner_id,
                "partner_bond_duration": bond_duration,
                "mourning_ticks": org.mourning_ticks,
                "personality": org.personality.to_dict(),
                "memory": org.memory.to_dict(),
                "nest": nest_info,
                "cause_of_death": org.cause_of_death,
                "clan_id": org.clan_id,
                "clan_role": org.clan_role,
                "leadership_score": calculate_leadership_score(org),
                "genotype": org.genotype.to_dict(),
                "phenotype": org.phenotype.to_dict(),
                "current_state_info": org.current_state_info,
                "inbreeding_coefficient": org.genotype.inbreeding_coefficient,
                "lineage_id": org.genotype.lineage_id,
                "lineage_name": org.genotype.lineage_name,
            }
        else:
            rec = runner.world.genealogy.get_record(organism_id)
            if rec:
                age_at_death = (rec.death_tick - rec.birth_tick) if rec.death_tick is not None else 0
                current_stats = {
                    "age": age_at_death,
                    "saude": 0.0,
                    "energy": 0.0,
                    "hunger": 100.0,
                    "x": 0.0,
                    "y": 0.0,
                    "role": rec.role,
                    "sex": rec.sex,
                    "life_stage": rec.life_stage,
                    "life_expectancy": 2000,
                    "current_state": "FALECIDO",
                    "carried_food": 0.0,
                    "partner_id": rec.partner_id,
                    "partner_bond_duration": rec.partner_bond_duration,
                    "mourning_ticks": 0,
                    "personality": rec.personality.to_dict() if hasattr(rec.personality, "to_dict") else rec.personality,
                    "memory": {
                        "known_food_sources": [],
                        "danger_zones": [],
                        "lost_relatives": [],
                        "safe_haven": None,
                    },
                    "nest": None,
                    "cause_of_death": rec.cause_of_death,
                    "clan_id": None,
                    "clan_role": None,
                    "leadership_score": 0.0,
                    "genotype": rec.genome,
                    "phenotype": rec.genome,
                    "current_state_info": {"state": "FALECIDO", "age": age_at_death},
                    "inbreeding_coefficient": rec.inbreeding_coefficient,
                    "lineage_id": rec.lineage_id,
                    "lineage_name": rec.lineage_name,
                }

        metrics = runner.world.get_metrics()
        return {
            "family_tree": family_tree,
            "is_alive": is_alive,
            "current_stats": current_stats,
            "population_averages": metrics.get("attr_stats", {}),
            "evolution": metrics.get("evolution", {}),
        }

    @router.get("/evolution", response_model=Dict[str, Any])
    async def get_evolution():
        return runner.world.get_evolution_report()

    @router.get("/clans", response_model=List[Dict[str, Any]])
    async def get_clans():
        return [c.to_dict() for c in runner.world.clan_system.clans.values() if c.is_active]

    @router.get("/clan/{clan_id}", response_model=Dict[str, Any])
    async def get_clan_detail(clan_id: int):
        clan = runner.world.clan_system.clans.get(clan_id)
        if not clan or not clan.is_active:
            raise HTTPException(status_code=404, detail="Clã não encontrado.")
        return clan.to_dict()

    @router.post("/spawn-food", response_model=Dict[str, Any])
    async def spawn_food_endpoint(params: Dict[str, Any]):
        x = float(params.get("x", runner.world.width / 2.0))
        y = float(params.get("y", runner.world.height / 2.0))
        food = runner.world.spawn_food_at(x, y)
        return {"status": "ok", "food_id": food.id, "x": food.x, "y": food.y}

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
                    elif action == "spawn_food":
                        x = float(data.get("x", runner.world.width / 2.0))
                        y = float(data.get("y", runner.world.height / 2.0))
                        runner.world.spawn_food_at(x, y)
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            logger.warning(f"Exceção no WebSocket: {e}")
            ws_manager.disconnect(websocket)

    return router
