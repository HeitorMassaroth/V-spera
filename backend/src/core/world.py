"""Estado e ciclo central do ecossistema de simulação (World State)."""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Any, Tuple
from .prng import PRNG
from .entities.organism import Organism
from .entities.food import Food
from .entities.traits import OrganismTraits
from .spatial.spatial_grid import SpatialHashGrid
from .systems.movement import MovementSystem
from .systems.metabolism import MetabolismSystem
from .systems.perception import PerceptionSystem
from .systems.family import FamilySystem
from .systems.clan_system import ClanSystem
from .entities.clan import ClanSocialStage, ClanRelation
from .entities.genetics import GeneticsEngine, AnimalGenome
from .entities.genealogy import GenealogyRegistry


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
        self.food_cluster_count = 4
        self.food_cluster_radius = 85.0

        self.prng = PRNG(seed)
        self.food_clusters = self._generate_food_clusters(self.food_cluster_count)
        self.tick = 0
        self._next_id = 1
        self._next_family_id_counter = 1
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
        self.family_system = FamilySystem(cluster_radius=self.food_cluster_radius)
        self.clan_system = ClanSystem(cooperation_radius=self.food_cluster_radius * 2.8)
        self.genealogy = GenealogyRegistry()

        # Contadores cumulativos de eventos
        self.total_births = 0
        self.total_deaths = 0
        self.total_food_consumed = 0
        self.recent_events: List[Dict[str, Any]] = []

        # Inicialização do ecossistema
        self._populate_initial(initial_organisms, initial_food)

    def _next_family_id(self) -> int:
        fid = self._next_family_id_counter
        self._next_family_id_counter += 1
        return fid

    def _next_entity_id(self) -> int:
        entity_id = self._next_id
        self._next_id += 1
        return entity_id

    def get_population_attribute_averages(self) -> Dict[str, float]:
        """Calcula a média atual de cada atributo quantitativo na população viva."""
        if not self.organisms:
            return {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

        n = float(len(self.organisms))
        return {
            "forca": sum(o.genome.forca for o in self.organisms.values()) / n,
            "velocidade": sum(o.genome.velocidade for o in self.organisms.values()) / n,
            "resistencia": sum(o.genome.resistencia for o in self.organisms.values()) / n,
            "inteligencia": sum(o.genome.inteligencia for o in self.organisms.values()) / n,
            "max_saude": sum(o.genome.max_saude for o in self.organisms.values()) / n,
        }

    def _populate_initial(self, organism_count: int, food_count: int) -> None:
        """Popula o ambiente inicial com organismos pioneiros com atributos individuais e genoma."""
        # Criação de organismos divididos entre as duas divisões (Rosa/Fêmea e Verde/Macho)
        for i in range(organism_count):
            oid = self._next_entity_id()
            x = self.prng.uniform(50.0, self.width - 50.0)
            y = self.prng.uniform(50.0, self.height - 50.0)
            initial_angle = self.prng.uniform(0.0, 2.0 * math.pi)
            initial_speed = self.prng.uniform(0.5, 2.0)
            vx = math.cos(initial_angle) * initial_speed
            vy = math.sin(initial_angle) * initial_speed

            # Duas divisões: metade Rosa (fêmea) e metade Verde (macho)
            role = Organism.ROLE_FEMALE if i % 2 == 0 else Organism.ROLE_MALE

            # Genoma individual aleatório e personalidade para a geração 0
            genome = GeneticsEngine.generate_random_genome(self.prng)
            personality = GeneticsEngine.generate_random_personality(self.prng)
            name = GeneticsEngine.generate_name(i, 0, oid)

            org = Organism(
                id=oid,
                x=x,
                y=y,
                name=name,
                vx=vx,
                vy=vy,
                energy=self.prng.uniform(85.0, 115.0),
                saude=genome.max_saude,
                traits=OrganismTraits(),
                genome=genome,
                personality=personality,
                wander_angle=self.prng.uniform(0.0, 2.0 * math.pi),
                generation=0,
                role=role,
                sex="F" if role == Organism.ROLE_FEMALE else "M",
                life_stage=Organism.STAGE_ADULT,
            )
            self.organisms[oid] = org
            self.total_births += 1

            # Registra no cartório genealógico perpétuo
            self.genealogy.register_birth(
                organism_id=oid,
                name=name,
                role=role,
                generation=0,
                birth_tick=0,
                father_id=None,
                mother_id=None,
                family_id=None,
                genome=genome,
                personality=personality,
                sex=org.sex,
                life_stage=org.life_stage,
                mutations=[],
                genetic_history=[],
                inbreeding_coefficient=getattr(genome, "inbreeding_coefficient", 0.0),
                lineage_id=getattr(genome, "lineage_id", "L0"),
                lineage_name=getattr(genome, "lineage_name", "Ancestral"),
            )

        # Criação de alimentos
        for _ in range(food_count):
            self.spawn_food()

    def _generate_food_clusters(self, count: int) -> List[Tuple[float, float]]:
        """Gera centros estáticos de fertilidade (oásis) distribuídos pelo ecossistema."""
        clusters: List[Tuple[float, float]] = []
        margin_x = min(160.0, self.width * 0.18)
        margin_y = min(130.0, self.height * 0.18)

        for _ in range(count):
            cx = self.prng.uniform(margin_x, self.width - margin_x)
            cy = self.prng.uniform(margin_y, self.height - margin_y)
            clusters.append((round(cx, 1), round(cy, 1)))

        return clusters

    def spawn_food(self) -> Optional[Food]:
        """Gera alimento concentrado em torno dos centros de recursos (oásis/clusters)."""
        if len(self.foods) >= self.max_food:
            return None

        fid = self._next_entity_id()

        # 85% de probabilidade de nascer concentrado em torno de um dos centros específicos
        if self.food_clusters and self.prng.random() < 0.85:
            center_idx = self.prng.randint(0, len(self.food_clusters) - 1)
            cx, cy = self.food_clusters[center_idx]

            # Concentração Gaussiana: maior densidade no miolo do centro, decaindo para as bordas
            sigma = self.food_cluster_radius * 0.45
            fx = self.prng.gauss(cx, sigma)
            fy = self.prng.gauss(cy, sigma)
        else:
            # 15% de esporos pioneiros/esparsos para incentivar exploração
            fx = self.prng.uniform(30.0, self.width - 30.0)
            fy = self.prng.uniform(30.0, self.height - 30.0)

        # Salvaguarda de limites
        fx = max(20.0, min(self.width - 20.0, fx))
        fy = max(20.0, min(self.height - 20.0, fy))

        food = Food(id=fid, x=round(fx, 1), y=round(fy, 1))
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

        # 2.5 Resolução física de colisão: impede sobreposição de organismos no espaço
        self.movement.resolve_organism_collisions(self.organisms, self.organism_grid)

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

            # Teste de sobrevivência (inanição / dano de combate / senescência)
            if not self.metabolism.check_survival(org):
                dead_organism_ids.append(org.id)
                cause = getattr(org, "cause_of_death", None) or "Inanição"
                self.genealogy.register_death(org.id, self.tick, cause)
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

        # 7. Dinâmica social, combate territorial do Macho e reprodução com hereditariedade
        pop_averages = self.get_population_attribute_averages()
        newborns, fam_events = self.family_system.update(
            self.organisms,
            self.food_clusters,
            self.prng,
            self._next_entity_id,
            self._next_family_id,
            self.genealogy,
            pop_averages,
            self.tick,
        )
        for child in newborns:
            self.organisms[child.id] = child
            self.total_births += 1

        if fam_events:
            self.recent_events.extend(fam_events)
            if len(self.recent_events) > 50:
                self.recent_events = self.recent_events[-50:]

        # 8. Dinâmica avançada de Clãs, Liderança Alpha/Beta, Reserva Coletiva e Diplomacia
        self.clan_system.update(
            self.organisms,
            self.family_system.families,
            self.family_system.nests,
            self.prng,
            self.genealogy,
            self.recent_events,
            self.tick,
        )

        # 9. Avanço do relógio
        self.tick += 1

        return self.get_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Calcula as métricas agregadas instantâneas do ecossistema e estatísticas genéticas."""
        pop_count = len(self.organisms)
        food_count = len(self.foods)

        if pop_count > 0:
            total_energy = sum(o.energy for o in self.organisms.values())
            avg_energy = total_energy / pop_count
            avg_speed = sum(o.speed for o in self.organisms.values()) / pop_count
            avg_age = sum(o.age for o in self.organisms.values()) / pop_count
            max_age = max(o.age for o in self.organisms.values())

            # Estatísticas dos Atributos Genéticos da População
            forcas = [o.genome.forca for o in self.organisms.values()]
            velocidades = [o.genome.velocidade for o in self.organisms.values()]
            resistencias = [o.genome.resistencia for o in self.organisms.values()]
            inteligencias = [o.genome.inteligencia for o in self.organisms.values()]
            saudes = [o.saude for o in self.organisms.values()]

            attr_stats = {
                "forca": {"avg": round(sum(forcas) / pop_count, 1), "min": round(min(forcas), 1), "max": round(max(forcas), 1)},
                "velocidade": {"avg": round(sum(velocidades) / pop_count, 1), "min": round(min(velocidades), 1), "max": round(max(velocidades), 1)},
                "resistencia": {"avg": round(sum(resistencias) / pop_count, 1), "min": round(min(resistencias), 1), "max": round(max(resistencias), 1)},
                "inteligencia": {"avg": round(sum(inteligencias) / pop_count, 1), "min": round(min(inteligencias), 1), "max": round(max(inteligencias), 1)},
                "saude": {"avg": round(sum(saudes) / pop_count, 1), "min": round(min(saudes), 1), "max": round(max(saudes), 1)},
            }
            max_generation = max(o.generation for o in self.organisms.values())
            total_mutations = sum(len(o.mutations) for o in self.organisms.values())
        else:
            avg_energy = 0.0
            avg_speed = 0.0
            avg_age = 0.0
            max_age = 0
            attr_stats = {
                "forca": {"avg": 0.0, "min": 0.0, "max": 0.0},
                "velocidade": {"avg": 0.0, "min": 0.0, "max": 0.0},
                "resistencia": {"avg": 0.0, "min": 0.0, "max": 0.0},
                "inteligencia": {"avg": 0.0, "min": 0.0, "max": 0.0},
                "saude": {"avg": 0.0, "min": 0.0, "max": 0.0},
            }
            max_generation = 0
            total_mutations = 0

        # Contagens por divisões, famílias, vínculos e estágios
        females_count = sum(1 for o in self.organisms.values() if o.role == Organism.ROLE_FEMALE)
        males_count = sum(1 for o in self.organisms.values() if o.role == Organism.ROLE_MALE)
        children_count = sum(1 for o in self.organisms.values() if o.role == Organism.ROLE_CHILD)
        families_count = len(set(o.family_id for o in self.organisms.values() if o.family_id is not None))
        family_homes_count = len(self.family_system.cluster_homes)
        bonded_pairs_count = sum(1 for o in self.organisms.values() if o.partner_id is not None) // 2
        active_nests_count = len([n for n in self.family_system.nests.values() if n.is_active])

        stage_stats = {
            "newborn": sum(1 for o in self.organisms.values() if getattr(o, "life_stage", None) == Organism.STAGE_NEWBORN),
            "developing": sum(1 for o in self.organisms.values() if getattr(o, "life_stage", None) == Organism.STAGE_DEVELOPING),
            "juvenile": sum(1 for o in self.organisms.values() if getattr(o, "life_stage", None) == Organism.STAGE_JUVENILE),
            "independent": sum(1 for o in self.organisms.values() if getattr(o, "life_stage", None) == Organism.STAGE_INDEPENDENT),
            "adult": sum(1 for o in self.organisms.values() if getattr(o, "life_stage", None) == Organism.STAGE_ADULT),
        }

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
            "females_count": females_count,
            "males_count": males_count,
            "children_count": children_count,
            "families_count": families_count,
            "family_homes_count": family_homes_count,
            "bonded_pairs_count": bonded_pairs_count,
            "nests_count": active_nests_count,
            "clans_count": len([c for c in self.clan_system.clans.values() if c.is_active]),
            "established_clans_count": len([c for c in self.clan_system.clans.values() if c.is_active and c.stage == ClanSocialStage.ESTABLISHED_CLAN]),
            "total_communal_food": round(sum(c.communal_food for c in self.clan_system.clans.values() if c.is_active), 1),
            "wars_count": sum(1 for c in self.clan_system.clans.values() for rel in c.diplomacy.values() if rel == ClanRelation.WAR) // 2,
            "stage_stats": stage_stats,
            "max_generation": max_generation,
            "total_mutations": total_mutations,
            "attr_stats": attr_stats,
            "evolution": self.genealogy.get_evolution_metrics(list(self.organisms.values()), list(self.clan_system.clans.values())),
        }

    def get_evolution_report(self) -> Dict[str, Any]:
        """Gera relatório completo de evolução biológica, diversidade genética e linhagens."""
        return self.genealogy.get_evolution_metrics(list(self.organisms.values()), list(self.clan_system.clans.values()))

    def get_compact_state(self) -> Dict[str, Any]:
        """Gera payload compacto para streaming em tempo real via WebSocket."""
        return {
            "t": self.tick,
            "orgs": [o.to_compact_dict() for o in self.organisms.values()],
            "foods": [[f.id, round(f.x, 1), round(f.y, 1)] for f in self.foods.values()],
            "clusters": self.food_clusters,
            "cluster_homes": self.family_system.cluster_homes,
            "families": [f.to_dict() for f in self.family_system.families.values() if f.is_active],
            "nests": [n.to_dict() for n in self.family_system.nests.values() if n.is_active],
            "clans": [c.to_dict() for c in self.clan_system.clans.values() if c.is_active],
            "metrics": self.get_metrics(),
            "events": self.recent_events[-15:],
        }

    def spawn_food_at(self, x: float, y: float, energy: float = 30.0) -> Food:
        """Permite que o usuário insira alimento interativamente no mundo pelo canvas."""
        food_id = self._next_entity_id()
        clamped_x = max(10.0, min(self.width - 10.0, x))
        clamped_y = max(10.0, min(self.height - 10.0, y))
        food = Food(id=food_id, x=clamped_x, y=clamped_y, energy_value=energy)
        self.foods[food_id] = food
        return food

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
            "food_clusters": self.food_clusters,
            "food_cluster_radius": self.food_cluster_radius,
            "next_id": self._next_id,
            "next_family_id": self._next_family_id_counter,
            "cluster_homes": {str(k): v for k, v in self.family_system.cluster_homes.items()},
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "total_food_consumed": self.total_food_consumed,
            "organisms": [o.to_dict() for o in self.organisms.values()],
            "foods": [f.to_dict() for f in self.foods.values()],
            "genealogy": self.genealogy.to_snapshot(),
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
        world._next_family_id_counter = snapshot.get("next_family_id", 1)
        world.prng.set_state(snapshot["prng_state"])
        world.total_births = snapshot["total_births"]
        world.total_deaths = snapshot["total_deaths"]
        world.total_food_consumed = snapshot["total_food_consumed"]
        world.food_clusters = snapshot.get("food_clusters", world._generate_food_clusters(4))
        world.food_cluster_radius = snapshot.get("food_cluster_radius", 85.0)
        world.family_system.cluster_homes = {
            int(k): v for k, v in snapshot.get("cluster_homes", {}).items()
        }
        if "genealogy" in snapshot:
            world.genealogy.from_snapshot(snapshot["genealogy"])

        for o_data in snapshot["organisms"]:
            org = Organism.from_dict(o_data)
            world.organisms[org.id] = org

        for f_data in snapshot["foods"]:
            food = Food.from_dict(f_data)
            world.foods[food.id] = food

        return world
