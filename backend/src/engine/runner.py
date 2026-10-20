"""Orquestrador do ciclo contínuo de simulação (Simulation Runner)."""

from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from core.world import World

logger = logging.getLogger("vespera.runner")


class SimulationRunner:
    """Controla o avanço temporal assíncrono do ecossistema e despacha deltas para a rede."""

    def __init__(
        self,
        world: Optional[World] = None,
        broadcast_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        tps: int = 30,
    ) -> None:
        self.world = world if world is not None else World()
        self.broadcast_callback = broadcast_callback
        self.tps = max(1, min(60, tps))
        self.status = "PAUSED"
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self.status == "RUNNING"

    async def start(self) -> None:
        """Inicia o loop contínuo de simulação."""
        async with self._lock:
            if self._loop_task is None or self._loop_task.done():
                self.status = "RUNNING"
                self._loop_task = asyncio.create_task(self._run_loop())
                logger.info(f"SimulationRunner iniciado a {self.tps} TPS.")
            else:
                self.status = "RUNNING"

    async def pause(self) -> None:
        """Pausa o avanço do tempo sem destruir o estado."""
        async with self._lock:
            self.status = "PAUSED"
            logger.info("SimulationRunner pausado.")

    async def step(self) -> Dict[str, Any]:
        """Executa exatamente um tick de avanço temporal (passo único)."""
        async with self._lock:
            metrics = self.world.step()
            await self._broadcast_current_state()
            return metrics

    async def reset(
        self,
        seed: Optional[int] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        initial_organisms: Optional[int] = None,
        initial_predator_females: Optional[int] = None,
        initial_predator_males: Optional[int] = None,
        initial_vranco_females: Optional[int] = None,
        initial_vranco_males: Optional[int] = None,
        initial_food: Optional[int] = None,
        food_spawn_rate: Optional[float] = None,
        max_food: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Reinicia o ecossistema com novos parâmetros ou parâmetros padrão."""
        async with self._lock:
            target_seed = seed if seed is not None else self.world.seed
            w = width if width is not None else self.world.width
            h = height if height is not None else self.world.height
            pop = initial_organisms
            food = initial_food if initial_food is not None else 120
            rate = food_spawn_rate if food_spawn_rate is not None else self.world.food_spawn_rate
            max_f = max_food if max_food is not None else self.world.max_food

            self.world = World(
                width=w,
                height=h,
                seed=target_seed,
                initial_organisms=pop,
                initial_predator_females=initial_predator_females,
                initial_predator_males=initial_predator_males,
                initial_vranco_females=initial_vranco_females,
                initial_vranco_males=initial_vranco_males,
                initial_food=food,
                food_spawn_rate=rate,
                max_food=max_f,
            )
            await self._broadcast_current_state()
            logger.info(f"SimulationRunner reiniciado com seed={target_seed}.")
            return self.world.get_metrics()

    def set_tps(self, tps: int) -> int:
        """Ajusta a taxa de ticks por segundo (1 a 60)."""
        self.tps = max(1, min(60, tps))
        logger.info(f"Taxa de simulação alterada para {self.tps} TPS.")
        return self.tps

    async def stop(self) -> None:
        """Encerra a execução do runner."""
        async with self._lock:
            self.status = "STOPPED"
            if self._loop_task and not self._loop_task.done():
                self._loop_task.cancel()
                try:
                    await self._loop_task
                except asyncio.CancelledError:
                    pass

    async def _run_loop(self) -> None:
        """Loop principal assíncrono que respeita a cadência definida de TPS."""
        try:
            while self.status != "STOPPED":
                if self.status == "RUNNING":
                    # Passo da física
                    self.world.step()

                    # Transmissão para clientes WebSocket
                    await self._broadcast_current_state()

                # Intervalo dinâmico baseado em TPS
                delay = 1.0 / self.tps
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f"Erro inesperado no loop da simulação: {e}")
            self.status = "PAUSED"

    async def _broadcast_current_state(self) -> None:
        if self.broadcast_callback:
            try:
                state = self.world.get_compact_state()
                state["status"] = self.status
                state["tps"] = self.tps
                await self.broadcast_callback(state)
            except Exception as e:
                logger.debug(f"Erro no broadcast do estado: {e}")
