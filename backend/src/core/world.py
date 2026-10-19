"""Estado e ciclo central do ecossistema de simulação (World State)."""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Any
from .prng import PRNG
from .entities.organism import Organism
from .entities.food import Food
from .entities.traits import OrganismTraits
from .spatial.spatial_grid import SpatialHashGrid
from .systems.movement import MovementSystem
from .systems.metabolism import MetabolismSystem
from .systems.perception import PerceptionSystem


class World:
    """Representa o ecossistema 2D isolado, contendo todas as entidades e relógio discreto."""

    def __init__(
        self,
        width: float = 1200.0,
        height: float = 800.0,
        seed: Optional[int] = 42,
        initial_organisms: int = 50,
        initial_food: int = 120,
        food_spawn_rate: float = 1.8,
        max_food: int = 250,
    ) -> None:
        self.width = float(width)
        self.height = float(height)
        self.seed = seed
        self.food_spawn_rate = float(food_spawn_rate)
        self.max_food = int(max_food)

        self.prng = PRNG(seed)
        self.tick = 0
        self._next_id = 1
        self._food_accumulator = 0.0

        # Coleções de entidades ativas
        self.organisms: Dict[int, Organism] = {}
        self.foods: Dict[int, Food] = {}

        # Grids espaciais para aceleração O(1)
        self.food_grid = SpatialHashGrid[Food](cell_size=60.0)
        self.organism_grid = SpatialHashGrid[Organism](cell_size=60.0)

        # Sistemas de regras
        self.movement = MovementSystem(self.width, self.height)
        self.metabolism = MetabolismSystem()
        self.perception = PerceptionSystem()

        # Contadores cumulativos de eventos
        self.total_births = 0
        self.total_deaths = 0
        self.total_food_consumed = 0

        # Inicialização do ecossistema
        self._populate_initial(initial_organisms, initial_food)

    def _next_entity_id(self) -> int:
        entity_id = self._next_id
        self._next_id += 1
        return entity_id

    def _populate_initial(self, organism_count: int, food_count: int) -> None:
        """Popula o ambiente inicial com organismos e alimentos distribuídos uniformemente."""
        # Criação de organismos
        for _ in range(organism_count):
            oid = self._next_entity_id()
            x = self.prng.uniform(50.0, self.width - 50.0)
            y = self.prng.uniform(50.0, self.height - 50.0)
            initial_angle = self.prng.uniform(0.0, 2.0 * math.pi)
            initial_speed = self.prng.uniform(0.5, 2.0)
            vx = math.cos(initial_angle) * initial_speed
            vy = math.sin(initial_angle) * initial_speed

            org = Organism(
                id=oid,
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                energy=self.prng.uniform(80.0, 120.0),
                traits=OrganismTraits(),
                wander_angle=self.prng.uniform(0.0, 2.0 * math.pi),
            )
            self.organisms[oid] = org
            self.total_births += 1

        # Criação de alimentos
        for _ in range(food_count):
            self.spawn_food()

    def spawn_food(self) -> Optional[Food]:
        """Gera um novo recurso alimentar em posição estocástica dentro dos limites."""
        if len(self.foods) >= self.max_food:
            return None

        fid = self._next_entity_id()
        fx = self.prng.uniform(30.0, self.width - 30.0)
        fy = self.prng.uniform(30.0, self.height - 30.0)
        food = Food(id=fid, x=fx, y=fy)
        self.foods[fid] = food
        return food

    def step(self) -> Dict[str, Any]:
        """Executa um ciclo discreto completo de simulação determinística."""
        # 1. Indexação espacial das entidades ativas
        self.food_grid.clear()
        for food in self.foods.values():
            self.food_grid.insert(food, food.x, food.y)

        self.organism_grid.clear()
        for org in self.organisms.values():
            self.organism_grid.insert(org, org.x, org.y)

        # 2. Percepção, tomada de decisão e física de movimento
        for org in self.organisms.values():
            nearest_food, _ = self.perception.find_nearest_food(org, self.food_grid)
            fx, fy = self.movement.calculate_steering(org, nearest_food, self.prng)
            self.movement.update_physics(org, fx, fy)

        # 3. Metabolismo, alimentação e vitalidade
        consumed_food_ids = set()
        dead_organism_ids = []

        for org in self.organisms.values():
            # Débito metabólico
            self.metabolism.apply_metabolism(org)

            # Consumo de comida
            eaten_foods = self.metabolism.process_feeding(org, self.food_grid)
            for food in eaten_foods:
                consumed_food_ids.add(food.id)
                self.total_food_consumed += 1

            # Teste de sobrevivência (inanição / idade)
            if not self.metabolism.check_survival(org):
                dead_organism_ids.append(org.id)
                self.total_deaths += 1

        # 4. Remoção de alimentos consumidos
        for fid in consumed_food_ids:
            self.foods.pop(fid, None)

        # 5. Remoção de organismos mortos
        for oid in dead_organism_ids:
            self.organisms.pop(oid, None)

        # 6. Renovação estocástica de alimentos (Spawn acumulativo)
        self._food_accumulator += self.food_spawn_rate
        while self._food_accumulator >= 1.0:
            self.spawn_food()
            self._food_accumulator -= 1.0

        # 7. Avanço do relógio
        self.tick += 1

        return self.get_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Calcula as métricas agregadas instantâneas do ecossistema."""
        pop_count = len(self.organisms)
        food_count = len(self.foods)

        if pop_count > 0:
            total_energy = sum(o.energy for o in self.organisms.values())
            avg_energy = total_energy / pop_count
            avg_speed = sum(o.speed for o in self.organisms.values()) / pop_count
            avg_age = sum(o.age for o in self.organisms.values()) / pop_count
            max_age = max(o.age for o in self.organisms.values())
        else:
            avg_energy = 0.0
            avg_speed = 0.0
            avg_age = 0.0
            max_age = 0

        return {
            "tick": self.tick,
            "population": pop_count,
            "food_count": food_count,
            "avg_energy": round(avg_energy, 2),
            "avg_speed": round(avg_speed, 2),
            "avg_age": round(avg_age, 1),
            "max_age": max_age,
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "total_food_consumed": self.total_food_consumed,
            "is_extinct": pop_count == 0,
        }

    def get_compact_state(self) -> Dict[str, Any]:
        """Gera payload compacto para streaming em tempo real via WebSocket."""
        return {
            "t": self.tick,
            "orgs": [o.to_compact_dict() for o in self.organisms.values()],
            "foods": [[f.id, round(f.x, 1), round(f.y, 1)] for f in self.foods.values()],
            "metrics": self.get_metrics(),
        }

    def to_snapshot(self) -> Dict[str, Any]:
        """Gera o estado completo serializado para checkpoint e persistência."""
        return {
            "tick": self.tick,
            "seed": self.seed,
            "prng_state": self.prng.get_state(),
            "width": self.width,
            "height": self.height,
            "food_spawn_rate": self.food_spawn_rate,
            "max_food": self.max_food,
            "next_id": self._next_id,
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "total_food_consumed": self.total_food_consumed,
            "organisms": [o.to_dict() for o in self.organisms.values()],
            "foods": [f.to_dict() for f in self.foods.values()],
        }

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> World:
        """Restaura o estado exato da simulação a partir de um snapshot."""
        world = cls(
            width=snapshot["width"],
            height=snapshot["height"],
            seed=snapshot.get("seed"),
            initial_organisms=0,
            initial_food=0,
            food_spawn_rate=snapshot["food_spawn_rate"],
            max_food=snapshot["max_food"],
        )
        world.tick = snapshot["tick"]
        world._next_id = snapshot["next_id"]
        world.prng.set_state(snapshot["prng_state"])
        world.total_births = snapshot["total_births"]
        world.total_deaths = snapshot["total_deaths"]
        world.total_food_consumed = snapshot["total_food_consumed"]

        for o_data in snapshot["organisms"]:
            org = Organism.from_dict(o_data)
            world.organisms[org.id] = org

        for f_data in snapshot["foods"]:
            food = Food.from_dict(f_data)
            world.foods[food.id] = food

        return world
