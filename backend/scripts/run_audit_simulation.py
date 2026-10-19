"""Script de benchmark e medição empírica de métricas para a Auditoria de Integração."""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import time
import json
from typing import Dict, Any, List
from src.core.world import World
from src.core.entities.organism import Organism


def run_benchmark_simulation(seed: int, ticks: int = 250) -> Dict[str, Any]:
    print(f"\n--- Iniciando Simulação Controlada (Semente: {seed}, Duração: {ticks} ciclos) ---")
    start_real_time = time.perf_counter()

    world = World(
        width=1200.0,
        height=800.0,
        seed=seed,
        initial_predators=25,
        initial_vrancos=25,
        initial_food=120,
        food_spawn_rate=1.8,
        max_food=250,
    )

    tick_times: List[float] = []
    pop_progression: List[int] = []

    # Execução discreta
    for t in range(ticks):
        t_start = time.perf_counter()
        metrics = world.step()
        t_end = time.perf_counter()

        tick_times.append((t_end - t_start) * 1000.0) # em ms
        pop_progression.append(metrics["population"])

    total_duration_s = time.perf_counter() - start_real_time

    # Métricas finais medidas diretamente do estado do World
    final_predators = sum(1 for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR)
    final_vrancos = sum(1 for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO)

    # Causas de óbito registradas na genealogia
    deaths_by_cause: Dict[str, int] = {}
    lifespans: List[int] = []
    for rec in world.genealogy._records.values():
        if rec.death_tick is not None:
            cause = rec.cause_of_death or "Desconhecida"
            deaths_by_cause[cause] = deaths_by_cause.get(cause, 0) + 1
            lifespans.append(rec.death_tick - rec.birth_tick)
        else:
            lifespans.append(world.tick - rec.birth_tick)

    avg_lifespan = round(sum(lifespans) / max(1, len(lifespans)), 1)

    # Contagem de eventos da Crônica Histórica
    chronicle_events_by_type: Dict[str, int] = {}
    for ev in world.chronicle._events:
        chronicle_events_by_type[ev.event_type] = chronicle_events_by_type.get(ev.event_type, 0) + 1

    # Desempenho computacional
    avg_ms_per_tick = round(sum(tick_times) / max(1, len(tick_times)), 2)
    min_ms = round(min(tick_times), 2)
    max_ms = round(max(tick_times), 2)

    result = {
        "seed": seed,
        "ticks": ticks,
        "real_duration_seconds": round(total_duration_s, 2),
        "initial_population": 50,
        "initial_predators": 25,
        "initial_vrancos": 25,
        "final_population": len(world.organisms),
        "final_predators": final_predators,
        "final_vrancos": final_vrancos,
        "total_births": world.total_births,
        "total_deaths": world.total_deaths,
        "avg_survival_time_ticks": avg_lifespan,
        "deaths_by_cause": deaths_by_cause,
        "final_food_count": len(world.foods),
        "total_food_consumed": world.total_food_consumed,
        "clans_count": len(world.clan_system.clans),
        "active_clans": sum(1 for c in world.clan_system.clans.values() if c.is_active),
        "chronicle_events_total": len(world.chronicle._events),
        "chronicle_events_breakdown": chronicle_events_by_type,
        "avg_ms_per_tick": avg_ms_per_tick,
        "min_ms_per_tick": min_ms,
        "max_ms_per_tick": max_ms,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    seeds = [42, 101, 777]
    all_results = []
    for s in seeds:
        res = run_benchmark_simulation(s, ticks=250)
        all_results.append(res)

    print("\n================== RESUMO AGREGADO (3 EXECUÇÕES) ==================")
    avg_time = round(sum(r["avg_ms_per_tick"] for r in all_results) / len(all_results), 2)
    total_births_avg = round(sum(r["total_births"] for r in all_results) / len(all_results), 1)
    total_deaths_avg = round(sum(r["total_deaths"] for r in all_results) / len(all_results), 1)
    avg_survival_avg = round(sum(r["avg_survival_time_ticks"] for r in all_results) / len(all_results), 1)
    print(f"Tempo médio computacional por ciclo: {avg_time} ms/tick")
    print(f"Média de nascimentos por ciclo de 250 ticks: {total_births_avg}")
    print(f"Média de óbitos por ciclo de 250 ticks: {total_deaths_avg}")
    print(f"Tempo médio de sobrevivência dos organismos: {avg_survival_avg} ciclos")


if __name__ == "__main__":
    main()
