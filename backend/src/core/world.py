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
from .systems.territory_system import TerritorySystem
from .systems.environment_system import EnvironmentSystem
from .systems.learning_system import LearningSystem
from .entities.environment import SeasonType
from .entities.clan import ClanSocialStage, ClanRelation
from .entities.genetics import GeneticsEngine, AnimalGenome
from .entities.genealogy import GenealogyRegistry
from .entities.chronicle import EcosystemChronicle, ChronicleEvent, ChronicleEventType


class World:
    """Representa o ecossistema 2D isolado, contendo todas as entidades e relógio discreto."""

    def __init__(
        self,
        width: float = 1200.0,
        height: float = 800.0,
        seed: Optional[int] = 42,
        initial_organisms: int = 50,
        initial_predators: Optional[int] = None,
        initial_vrancos: Optional[int] = None,
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
        self.territory_system = TerritorySystem(self.width, self.height, self.food_clusters, self.prng)
        self.environment_system = EnvironmentSystem(season_duration_ticks=250)
        self.learning_system = LearningSystem()
        self.genealogy = GenealogyRegistry()
        self.chronicle = EcosystemChronicle()
        self._last_recorded_season: Optional[str] = None
        self._vrancos_extinct_recorded: bool = False
        self._predators_extinct_recorded: bool = False

        # Contadores cumulativos de eventos
        self.total_births = 0
        self.total_deaths = 0
        self.total_food_consumed = 0
        self.recent_events: List[Dict[str, Any]] = []

        # Determinação equilibrada das populações iniciais das duas raças
        if initial_predators is None and initial_vrancos is None:
            pred_count = initial_organisms // 2
            vran_count = initial_organisms - pred_count
        elif initial_predators is not None and initial_vrancos is None:
            pred_count = initial_predators
            vran_count = max(0, initial_organisms - pred_count)
        elif initial_predators is None and initial_vrancos is not None:
            vran_count = initial_vrancos
            pred_count = max(0, initial_organisms - vran_count)
        else:
            pred_count = initial_predators or 0
            vran_count = initial_vrancos or 0

        # Inicialização do ecossistema com ambas as raças coexistindo
        self._populate_initial(pred_count, vran_count, initial_food)

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

    def _populate_initial(self, predator_count: int, vranco_count: int, food_count: int) -> None:
        """Popula o ambiente inicial com Predadores e Vrancos pioneiros."""
        # 1. Povoamento dos Predadores pioneiros
        for i in range(predator_count):
            oid = self._next_entity_id()
            x = self.prng.uniform(80.0, self.width - 80.0)
            y = self.prng.uniform(80.0, self.height - 80.0)
            initial_angle = self.prng.uniform(0.0, 2.0 * math.pi)
            initial_speed = self.prng.uniform(0.5, 1.8)
            vx = math.cos(initial_angle) * initial_speed
            vy = math.sin(initial_angle) * initial_speed

            role = Organism.ROLE_FEMALE if i % 2 == 0 else Organism.ROLE_MALE
            genome = GeneticsEngine.generate_random_genome(self.prng, is_vranco=False)
            personality = GeneticsEngine.generate_random_personality(self.prng, is_vranco=False, genome=genome)
            name = GeneticsEngine.generate_name(i, 0, oid, is_vranco=False)

            pred = Organism(
                id=oid,
                x=x,
                y=y,
                name=name,
                vx=vx,
                vy=vy,
                energy=self.prng.uniform(85.0, 115.0),
                saude=genome.max_saude,
                species=Organism.SPECIES_PREDATOR,
                traits=OrganismTraits(),
                genome=genome,
                personality=personality,
                wander_angle=self.prng.uniform(0.0, 2.0 * math.pi),
                generation=0,
                role=role,
                sex="F" if role == Organism.ROLE_FEMALE else "M",
                life_stage=Organism.STAGE_ADULT,
            )
            self.organisms[oid] = pred
            self.total_births += 1

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
                sex=pred.sex,
                life_stage=pred.life_stage,
                mutations=[],
                genetic_history=[],
                inbreeding_coefficient=0.0,
                lineage_id=genome.lineage_id,
                lineage_name=genome.lineage_name,
            )

            self.chronicle.record_event(
                event_type=ChronicleEventType.BIRTH.value,
                title=f"Gênese Ancestral: {name}",
                description=f"{name} surgiu como indivíduo pioneiro da espécie Predador (Linhagem {genome.lineage_name}).",
                tick=0,
                cause="Gênese primordial do ecossistema",
                result="População fundadora estabelecida",
                importance=2,
                location=(x, y),
                primary_organism_id=oid,
                primary_organism_name=name,
                species=Organism.SPECIES_PREDATOR,
                metadata={"role": role, "generation": 0, "lineage": genome.lineage_name},
            )

        # 2. Povoamento dos Vrancos pioneiros (Tendência natural a ocupar regiões periféricas)
        cx, cy = self.width / 2.0, self.height / 2.0
        max_r = min(self.width, self.height) * 0.44

        for j in range(vranco_count):
            oid = self._next_entity_id()
            angle = self.prng.uniform(0.0, 2.0 * math.pi)
            r_dist = self.prng.uniform(max_r * 0.55, max_r)
            vx_pos = max(45.0, min(self.width - 45.0, cx + math.cos(angle) * r_dist))
            vy_pos = max(45.0, min(self.height - 45.0, cy + math.sin(angle) * r_dist))

            initial_angle = self.prng.uniform(0.0, 2.0 * math.pi)
            initial_speed = self.prng.uniform(1.0, 2.5)
            vx = math.cos(initial_angle) * initial_speed
            vy = math.sin(initial_angle) * initial_speed

            role = Organism.ROLE_FEMALE if j % 2 == 0 else Organism.ROLE_MALE
            genome = GeneticsEngine.generate_random_genome(self.prng, is_vranco=True)
            personality = GeneticsEngine.generate_random_personality(self.prng, is_vranco=True, genome=genome)
            name = GeneticsEngine.generate_name(j, 0, oid, is_vranco=True)

            vranco = Organism(
                id=oid,
                x=vx_pos,
                y=vy_pos,
                name=name,
                vx=vx,
                vy=vy,
                energy=self.prng.uniform(85.0, 115.0),
                saude=genome.max_saude * 0.60,
                species=Organism.SPECIES_VRANCO,
                traits=OrganismTraits(),
                genome=genome,
                personality=personality,
                wander_angle=self.prng.uniform(0.0, 2.0 * math.pi),
                generation=0,
                role=role,
                sex="F" if role == Organism.ROLE_FEMALE else "M",
                life_stage=Organism.STAGE_ADULT,
            )
            self.organisms[oid] = vranco
            self.total_births += 1

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
                sex=vranco.sex,
                life_stage=vranco.life_stage,
                species=Organism.SPECIES_VRANCO,
                mutations=[],
                genetic_history=[],
                inbreeding_coefficient=0.0,
                lineage_id=genome.lineage_id,
                lineage_name=genome.lineage_name,
            )

            self.chronicle.record_event(
                event_type=ChronicleEventType.BIRTH.value,
                title=f"Gênese Ancestral: {name}",
                description=f"{name} surgiu como indivíduo pioneiro da espécie Vranco (Linhagem {genome.lineage_name}).",
                tick=0,
                cause="Gênese primordial do ecossistema",
                result="População fundadora estabelecida na periferia",
                importance=2,
                location=(vx_pos, vy_pos),
                primary_organism_id=oid,
                primary_organism_name=name,
                species=Organism.SPECIES_VRANCO,
                metadata={"role": role, "generation": 0, "lineage": genome.lineage_name},
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

            # Recursos finitos e dinâmicos: modulação pela fertilidade da zona territorial e ciclo sazonal
            season_mult = self.environment_system.state.food_spawn_multiplier if hasattr(self, "environment_system") else 1.0
            if hasattr(self, "territory_system") and self.territory_system:
                zone = self.territory_system.get_zone_at(cx, cy)
                if zone:
                    fertility_ratio = (zone.current_fertility / max(0.1, zone.base_fertility)) * season_mult
                    # Zonas sobrecarregadas ou em inverno rigoroso reduzem brotamento vegetal
                    if fertility_ratio < 0.95 and self.prng.random() > fertility_ratio:
                        return None

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
        if hasattr(self, "environment_system"):
            self.environment_system.record_food_spawned(food.energy_value)
        return food

    def step(self) -> Dict[str, Any]:
        """Executa um ciclo discreto completo de simulação determinística."""
        # Coleta de eventos factuais gerados durante o presente ciclo
        tick_events: List[Dict[str, Any]] = []

        # 0. Atualização do Ciclo Ambiental, Estações do Ano e Equilíbrio Ecológico
        prev_season = self.environment_system.state.season.value if hasattr(self, "environment_system") and self.environment_system.state.season else None
        self.environment_system.update(self.tick, self.organisms, self.foods, tick_events)
        curr_season = self.environment_system.state.season.value if hasattr(self, "environment_system") and self.environment_system.state.season else None

        if prev_season != curr_season and curr_season is not None:
            self._last_recorded_season = curr_season
            self.chronicle.record_event(
                event_type=ChronicleEventType.ENVIRONMENTAL_SEASON.value,
                title=f"Transição Climática: Início do(a) {curr_season}",
                description=f"O ecossistema adentrou o período de {curr_season}. Temperatura média: {self.environment_system.state.temperature:.1f}°C, biomassa {self.environment_system.state.food_spawn_multiplier:.2f}x.",
                tick=self.tick,
                cause="Ciclo astronômico periódico das estações do ano",
                result=f"Custos metabólicos ajustados para {self.environment_system.state.metabolic_cost_multiplier:.2f}x",
                importance=3,
                metadata={"season": curr_season, "temperature": self.environment_system.state.temperature},
            )

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
            fx, fy = self.movement.calculate_steering(org, nearest_food, self.prng, organism_grid=self.organism_grid)
            self.movement.update_physics(org, fx, fy)

        # 2.5 Resolução física de colisão: impede sobreposição de organismos no espaço
        self.movement.resolve_organism_collisions(self.organisms, self.organism_grid)

        # 3. Metabolismo, alimentação e vitalidade
        consumed_food_ids = set()
        dead_in_metabolism: List[Organism] = []

        for org in list(self.organisms.values()):
            # Débito metabólico modulado pela temperatura e estação climática
            self.metabolism.apply_metabolism(
                org,
                season_metabolic_mult=self.environment_system.state.metabolic_cost_multiplier,
                temperature=self.environment_system.state.temperature,
            )

            # Consumo de comida
            eaten_foods = self.metabolism.process_feeding(org, self.food_grid)
            for food in eaten_foods:
                consumed_food_ids.add(food.id)
                self.total_food_consumed += 1
                self.environment_system.record_food_consumed(food.energy_value)
                # Aprendizado empírico individual de hotspots de alimentação
                self.learning_system.record_feeding(org, food.x, food.y, self.tick)

            # Verificação periódica de extinção / desatualização de hotspots
            if self.tick % 5 == 0:
                self.learning_system.check_food_site_extinction(org, self.food_grid, self.tick)

            # Teste de sobrevivência (inanição / senescência)
            if not self.metabolism.check_survival(org):
                dead_in_metabolism.append(org)

        # Remoção de alimentos consumidos
        for fid in consumed_food_ids:
            self.foods.pop(fid, None)

        # Processamento e descarte imediato dos mortos no metabolismo
        for dead_org in dead_in_metabolism:
            self._process_organism_death(
                dead_org,
                cause=getattr(dead_org, "cause_of_death", None) or "Inanição",
                tick_events=tick_events,
            )

        # 6. Renovação estocástica de alimentos (Spawn acumulativo com modulação sazonal)
        self._food_accumulator += self.food_spawn_rate * self.environment_system.state.food_spawn_multiplier
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
            season_reproduction_factor=self.environment_system.state.reproduction_cost_multiplier,
        )
        if fam_events:
            tick_events.extend(fam_events)

        # Processa e remove IMEDIATAMENTE quaisquer baixas resultantes de combate físico
        combat_casualties = [o for o in list(self.organisms.values()) if not o.alive or o.saude <= 0.0]
        for dead_combatant in combat_casualties:
            self._process_organism_death(
                dead_combatant,
                cause=getattr(dead_combatant, "cause_of_death", None) or "Combate",
                tick_events=tick_events,
            )

        for child in newborns:
            self.organisms[child.id] = child
            self.total_births += 1
            self.environment_system.record_birth(child)

            # Registro biográfico factual na Crônica Histórica
            clan = self.clan_system.clans.get(child.clan_id) if child.clan_id else None
            parents_desc = []
            f_rec = self.genealogy.get_record(child.father_id) if child.father_id else None
            m_rec = self.genealogy.get_record(child.mother_id) if child.mother_id else None
            if f_rec:
                parents_desc.append(f"pai: {f_rec.name}")
            if m_rec:
                parents_desc.append(f"mãe: {m_rec.name}")
            parents_str = f" ({', '.join(parents_desc)})" if parents_desc else ""

            related_ids = []
            if child.father_id:
                related_ids.extend([e.id for e in self.chronicle._events[-20:] if child.father_id in e.involved_organism_ids])
            if child.mother_id:
                related_ids.extend([e.id for e in self.chronicle._events[-20:] if child.mother_id in e.involved_organism_ids])
            related_ids = list(dict.fromkeys(related_ids))[:4]

            self.chronicle.record_event(
                event_type=ChronicleEventType.BIRTH.value,
                title=f"Nascimento de {child.name}",
                description=f"{child.name} nasceu na Geração {child.generation} ({child.species}){parents_str}." + (f" Pertence ao {clan.name}." if clan else ""),
                tick=self.tick,
                cause="Reprodução biológica bem-sucedida" + parents_str,
                result="Aumento da população ativa",
                importance=2,
                location=(child.x, child.y),
                primary_organism_id=child.id,
                primary_organism_name=child.name,
                clan_id=child.clan_id,
                clan_name=clan.name if clan else None,
                species=child.species,
                related_event_ids=related_ids,
                metadata={"role": child.role, "generation": child.generation, "lineage": getattr(child.genome, "lineage_name", None)},
            )

        # 8. Dinâmica avançada de Clãs, Liderança Alpha/Beta, Reserva Coletiva e Diplomacia
        self.clan_system.update(
            self.organisms,
            self.family_system.families,
            self.family_system.nests,
            self.prng,
            self.genealogy,
            tick_events,
            self.tick,
        )

        # 8.2 Dinâmica territorial, qualidade ambiental, ocupação, migrações fundamentadas e disputas
        self.territory_system.update(
            self.organisms,
            self.foods,
            self.family_system.families,
            self.family_system.nests,
            self.clan_system.clans,
            self.tick,
            tick_events,
        )

        # 8.5 Decaimento periódico e limpeza de memórias episódicas e relações sociais
        if self.tick % 30 == 0:
            for o in self.organisms.values():
                if getattr(o, "memory", None):
                    o.memory.decay_memories(self.tick)
                if hasattr(o, "decay_relationships"):
                    o.decay_relationships(self.tick)

        # 8.6 Aprendizado social contínuo (transmissão de rotas e táticas) e manutenção cognitiva
        self.learning_system.process_social_transmission(
            self.organisms,
            self.organism_grid,
            self.tick,
            tick_events,
            self.prng,
        )
        self.learning_system.decay_and_maintain(self.organisms, self.tick)

        # 8.7 Ingestão factual de acontecimentos dos subsistemas na Crônica Histórica
        self._process_tick_chronicle_events(tick_events)

        # Preserva os eventos recentes mantendo teto estrito de 50 entradas
        if tick_events:
            self.recent_events.extend(tick_events)
            if len(self.recent_events) > 50:
                self.recent_events = self.recent_events[-50:]

        # 8.8 Verificação factual de extinções de espécies
        vran_alive = any(o.species == Organism.SPECIES_VRANCO for o in self.organisms.values())
        pred_alive = any(o.species == Organism.SPECIES_PREDATOR for o in self.organisms.values())

        if not vran_alive and not self._vrancos_extinct_recorded and self.total_births > 0:
            self._vrancos_extinct_recorded = True
            self.chronicle.record_event(
                event_type=ChronicleEventType.SPECIES_EXTINCTION.value,
                title="Extinção da Espécie: Vrancos",
                description="O último exemplar vivo da espécie Vranco pereceu. A espécie está oficialmente extinta no ecossistema.",
                tick=self.tick,
                cause="Colapso populacional decorrente de predação crônica ou escassez prolongada",
                result="Fim da linhagem de aves Vrancos na simulação",
                species=Organism.SPECIES_VRANCO,
                importance=5,
            )

        if not pred_alive and not self._predators_extinct_recorded and self.total_births > 0:
            self._predators_extinct_recorded = True
            self.chronicle.record_event(
                event_type=ChronicleEventType.SPECIES_EXTINCTION.value,
                title="Extinção da Espécie: Predadores",
                description="O último exemplar vivo da espécie Predador pereceu. A espécie está oficialmente extinta no ecossistema.",
                tick=self.tick,
                cause="Inanição aguda por falta de alimento ou ferimentos graves em combate",
                result="Fim da linhagem carnívora no ecossistema",
                species=Organism.SPECIES_PREDATOR,
                importance=5,
            )

        # 9. Avanço do relógio
        self.tick += 1

        return self.get_metrics()

    def _process_organism_death(
        self,
        org: Organism,
        cause: Optional[str] = None,
        tick_events: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Processamento centralizado e unificado de morte biológica:
        - Registro na Genealogia e Sistema Ambiental
        - Perda cultural de conhecimento empírico
        - Registro de falecimento e sucessão de liderança na Crônica Histórica
        - Notificação episódica e aprendizado de perigo para parentes e testemunhas locais
        - Remoção definitiva de self.organisms
        """
        org.alive = False
        org.saude = 0.0
        actual_cause = cause or getattr(org, "cause_of_death", None) or "Inanição"
        org.cause_of_death = actual_cause

        self.genealogy.register_death(org.id, self.tick, actual_cause)
        self.total_deaths += 1
        self.environment_system.record_death(org, actual_cause)

        target_events = tick_events if tick_events is not None else self.recent_events
        self.learning_system.on_organism_death(org, self.organisms, self.tick, target_events)

        clan = self.clan_system.clans.get(org.clan_id) if org.clan_id else None
        is_alpha = clan and clan.alpha_id == org.id
        is_beta = clan and clan.beta_id == org.id
        importance = 4 if is_alpha else (3 if (actual_cause in ("Predação", "Combate", "Defesa Coletiva dos Vrancos") or org.age > 800) else 2)

        related_ids = [
            e.id for e in self.chronicle._events[-20:]
            if org.id in e.involved_organism_ids and e.event_type in (
                ChronicleEventType.COMBAT_ENGAGEMENT.value,
                ChronicleEventType.MOBBING_DEFENSE.value
            )
        ]

        death_event = self.chronicle.record_event(
            event_type=ChronicleEventType.DEATH.value,
            title=f"Morte de {org.name}" + (" (Líder Alpha)" if is_alpha else (" (Guardião Beta)" if is_beta else "")),
            description=f"{org.name} ({org.species}) faleceu aos {org.age} ciclos no estágio {org.life_stage}. Causa: {actual_cause}.",
            tick=self.tick,
            cause=f"Falecimento confirmado por {actual_cause}",
            result="Fim da trajetória biológica individual" + (f"; vacância da liderança no {clan.name}" if is_alpha else ""),
            importance=importance,
            location=(org.x, org.y),
            primary_organism_id=org.id,
            primary_organism_name=org.name,
            clan_id=org.clan_id,
            clan_name=clan.name if clan else None,
            species=org.species,
            related_event_ids=related_ids,
            metadata={"age": org.age, "cause": actual_cause, "is_alpha": is_alpha, "is_beta": is_beta},
        )

        if is_alpha and clan:
            self.chronicle.record_event(
                event_type=ChronicleEventType.LEADERSHIP_SUCCESSION.value,
                title=f"Vacância de Liderança no {clan.name}",
                description=f"Com o falecimento do Alpha {org.name}, o {clan.name} iniciou transição de comando.",
                tick=self.tick,
                cause=f"Morte do líder titular {org.name} ({actual_cause})",
                result="Convocação de eleição para o posto de Alpha",
                importance=4,
                clan_id=clan.id,
                clan_name=clan.name,
                primary_organism_id=org.id,
                primary_organism_name=org.name,
                related_event_ids=[death_event.id],
            )

        for other in self.organisms.values():
            if other.id != org.id and other.alive and getattr(other, "memory", None):
                is_relative = (
                    (other.family_id is not None and other.family_id == org.family_id) or
                    other.partner_id == org.id or
                    other.id in (org.father_id, org.mother_id) or
                    org.id in (other.father_id, other.mother_id)
                )
                if is_relative:
                    other.memory.add_episode(
                        event_type="LOST_RELATIVE",
                        description=f"Perdeu o parente {org.name} ({actual_cause})",
                        tick=self.tick,
                        x=org.x,
                        y=org.y,
                        intensity=0.9,
                        relevance=0.95,
                        involved_id=org.id,
                        involved_name=org.name,
                    )
                elif math.hypot(other.x - org.x, other.y - org.y) <= 90.0:
                    other.memory.add_episode(
                        event_type="WITNESSED_DEATH",
                        description=f"Presenciou a morte de {org.name}",
                        tick=self.tick,
                        x=org.x,
                        y=org.y,
                        intensity=0.65,
                        relevance=0.75,
                        involved_id=org.id,
                        involved_name=org.name,
                    )
                    if actual_cause in ("Predação", "Combate", "Defesa Coletiva dos Vrancos") and getattr(other, "knowledge", None):
                        other.knowledge.record_danger(org.x, org.y, "KILL_SITE", danger_level=0.75, tick=self.tick)
                        other.knowledge.tactical_skills.improve("evasion_proficiency", 0.05)

        self.organisms.pop(org.id, None)

    def _process_tick_chronicle_events(self, events_or_batch_start: Any) -> None:
        """Processa e converte eventos factuais ocorridos nos subsistemas em registros da Crônica Histórica."""
        if isinstance(events_or_batch_start, int):
            batch_start = events_or_batch_start
            if batch_start >= len(self.recent_events):
                return
            events_to_process = self.recent_events[batch_start:]
        elif isinstance(events_or_batch_start, list):
            events_to_process = events_or_batch_start
        else:
            return

        for ev in events_to_process:
            ev_type = ev.get("type")

            if ev_type == "clan_formed":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.CLAN_FOUNDED.value,
                    title=f"Fundação do {ev['clan_name']}",
                    description=f"O grupo cooperativo uniu-se formalmente, estabelecendo o {ev['clan_name']} ({ev.get('families_count', 0)} famílias no estágio {ev.get('stage', '')}).",
                    tick=self.tick,
                    cause="Consolidação de laços de cooperação mútua recorrente entre famílias vizinhas",
                    result="Novo clã ativo com reserva coletiva de alimentos e defesa integrada",
                    importance=4,
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                    metadata={"families_count": ev.get("families_count"), "stage": ev.get("stage")},
                )

            elif ev_type == "clan_stage_changed":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.CLAN_STAGE_CHANGE.value,
                    title=f"Evolução Social: {ev['clan_name']}",
                    description=f"O {ev['clan_name']} avançou em sua estrutura social atingindo o estágio {ev.get('stage', '')}.",
                    tick=self.tick,
                    cause="Intensificação contínua da cooperação mútua e compartilhamento comunitário",
                    result="Organização social e governança aprimoradas",
                    importance=3,
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                    metadata={"stage": ev.get("stage")},
                )

            elif ev_type == "alpha_elected":
                related_ids = [
                    e.id for e in self.chronicle._events[-20:]
                    if e.clan_id == ev.get("clan_id") and e.event_type in (
                        ChronicleEventType.DEATH.value,
                        ChronicleEventType.LEADERSHIP_SUCCESSION.value
                    )
                ]
                self.chronicle.record_event(
                    event_type=ChronicleEventType.LEADERSHIP_ELECTED.value,
                    title=f"Eleição de Líder Alpha: {ev['leader_name']} ({ev['clan_name']})",
                    description=f"{ev['leader_name']} foi aclamado Alpha supremo do {ev['clan_name']} (Aprovação: {ev.get('approval_rating', 1.0)*100:.0f}%, Força: {ev.get('score', 0):.1f}).",
                    tick=self.tick,
                    cause="Consenso por dominância física, maturidade e alta aprovação social dos membros",
                    result=f"{ev['leader_name']} assume o comando de deslocamento e prerrogativas de liderança",
                    importance=4,
                    primary_organism_id=ev.get("leader_id"),
                    primary_organism_name=ev.get("leader_name"),
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                    related_event_ids=related_ids,
                    metadata={"score": ev.get("score"), "approval_rating": ev.get("approval_rating")},
                )

            elif ev_type == "beta_elected":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.LEADERSHIP_ELECTED.value,
                    title=f"Nomeação de Guardião Beta: {ev['beta_name']} ({ev['clan_name']})",
                    description=f"{ev['beta_name']} assumiu o posto de Guardião Beta do {ev['clan_name']} (Aptidão defensiva: {ev.get('score', 0):.1f}).",
                    tick=self.tick,
                    cause="Aptidão combativa superior para liderança tática de defesa territorial",
                    result=f"{ev['beta_name']} torna-se a primeira linha de proteção armada da comunidade",
                    importance=3,
                    primary_organism_id=ev.get("beta_id"),
                    primary_organism_name=ev.get("beta_name"),
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                    metadata={"score": ev.get("score")},
                )

            elif ev_type == "clan_desertion":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.LEADERSHIP_DEPOSED.value,
                    title=f"Deserção do {ev['clan_name']}: {ev['organism_name']}",
                    description=f"{ev['organism_name']} abandonou voluntariamente o {ev['clan_name']}.",
                    tick=self.tick,
                    cause=ev.get("reason", "Hostilidade e colapso irreversível de confiança com a liderança"),
                    result="Indivíduo passa à condição de predador nômade solitário desprovido de território seguro",
                    importance=3,
                    primary_organism_id=ev.get("organism_id"),
                    primary_organism_name=ev.get("organism_name"),
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                )

            elif ev_type == "family_expelled":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.CLAN_SPLIT.value,
                    title=f"Expulsão do {ev['clan_name']}: Família #{ev['family_id']}",
                    description=f"A família #{ev['family_id']} foi banida pelo conselho do {ev['clan_name']}.",
                    tick=self.tick,
                    cause=ev.get("reason", "Parasitismo persistente da despensa comum sem contribuição laboral"),
                    result="Banimento territorial e corte do acesso à reserva coletiva",
                    importance=3,
                    clan_id=ev.get("clan_id"),
                    clan_name=ev.get("clan_name"),
                    metadata={"family_id": ev.get("family_id")},
                )

            elif ev_type == "clan_war_declared":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.WAR_DECLARED.value,
                    title=f"Declaração de Guerra: {ev['clan1_name']} vs {ev['clan2_name']}",
                    description=f"Conflito armado e estado de guerra instaurado entre {ev['clan1_name']} e {ev['clan2_name']}.",
                    tick=self.tick,
                    cause="Invasão territorial mútua combinada com escassez de caça e lideranças agressivas",
                    result="Batalhas ativas nas linhas fronteiriças e suspensão de relações neutras",
                    importance=4,
                    metadata={"clan1": ev["clan1_name"], "clan2": ev["clan2_name"]},
                )

            elif ev_type == "clan_truce_agreed":
                related_ids = [
                    e.id for e in self.chronicle._events[-40:]
                    if e.event_type == ChronicleEventType.WAR_DECLARED.value and (
                        ev["clan1_name"] in (e.metadata.get("clan1"), e.metadata.get("clan2"))
                    )
                ]
                self.chronicle.record_event(
                    event_type=ChronicleEventType.TRUCE_SIGNED.value,
                    title=f"Trégua Firmada: {ev['clan1_name']} e {ev['clan2_name']}",
                    description=f"{ev['clan1_name']} e {ev['clan2_name']} selaram armistício e cessaram hostilidades armadas.",
                    tick=self.tick,
                    cause="Exaustão de guerra severa e escassez crítica nas reservas alimentares de ambas as partes",
                    result="Cessar-fogo provisório de 120 ciclos e recuo recíproco das patrulhas bélicas",
                    importance=4,
                    related_event_ids=related_ids,
                    metadata={"clan1": ev["clan1_name"], "clan2": ev["clan2_name"]},
                )

            elif ev_type == "territory_migration":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.MIGRATION.value,
                    title=f"Migração de Vrancos: {ev['origin_zone']} -> {ev['dest_zone']}",
                    description=f"Um contingente de {ev.get('count', 1)} Vrancos migrou de {ev['origin_zone']} para {ev['dest_zone']}.",
                    tick=self.tick,
                    cause=ev.get("reason", "Insegurança crítica ou exaustão de sementes na região de origem"),
                    result=f"Reassentamento na zona fértil {ev['dest_zone']}",
                    importance=3,
                    species=Organism.SPECIES_VRANCO,
                    metadata={"origin": ev["origin_zone"], "destination": ev["dest_zone"], "count": ev.get("count")},
                )

            elif ev_type == "clan_territory_migrated":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.MIGRATION.value,
                    title=f"Êxodo Territorial do {ev['clan_name']}: {ev['origin_zone']} -> {ev['dest_zone']}",
                    description=f"O {ev['clan_name']} ({ev.get('members_count', 0)} indivíduos) abandonou {ev['origin_zone']} e estabeleceu novo território em {ev['dest_zone']}.",
                    tick=self.tick,
                    cause=ev.get("reason", "Esgotamento severo da capacidade de suporte e risco de inanição"),
                    result="Transferência da sede territorial e criação de novo santuário comunitário",
                    importance=4,
                    clan_name=ev.get("clan_name"),
                    metadata={"origin": ev["origin_zone"], "destination": ev["dest_zone"], "members": ev.get("members_count")},
                )

            elif ev_type == "clan_peaceful_retreat":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.TERRITORY_LOST.value,
                    title=f"Recuo Estratégico: {ev['clan_name']}",
                    description=f"O {ev['clan_name']} recuou ordenadamente da zona {ev['origin_zone']} para {ev['dest_zone']}.",
                    tick=self.tick,
                    cause=ev.get("reason", "Desvantagem de poder e preservação cautelosa da integridade do grupo"),
                    result=f"Cedência pacífica de {ev['origin_zone']} para evitar confronto suicida",
                    importance=3,
                    clan_name=ev.get("clan_name"),
                    metadata={"origin": ev["origin_zone"], "destination": ev["dest_zone"], "retreat_count": ev.get("retreat_count")},
                )

            elif ev_type == "territory_contested":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.TERRITORY_CONTESTED.value,
                    title=f"Disputa de Domínio em {ev['zone_name']}: {ev['clan1']} vs {ev['clan2']}",
                    description=f"A zona {ev['zone_name']} tornou-se teatro de disputa territorial acirrada entre {ev['clan1']} e {ev['clan2']}.",
                    tick=self.tick,
                    cause="Pressão concorrente por oásis de recursos e proximidade mútua de patrulhas",
                    result="Fronteira contestada sob vigília constante de ambos os lados",
                    importance=3,
                    metadata={"zone": ev["zone_name"], "clan1": ev["clan1"], "clan2": ev["clan2"]},
                )

            elif ev_type == "vranco_collective_defense":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.MOBBING_DEFENSE.value,
                    title=f"Defesa Coletiva dos Vrancos contra {ev.get('predator_name', 'Predador')}",
                    description=f"Bando coordenado de {ev.get('participants_count', 0)} Vrancos (Força {ev.get('collective_power', 0)}) executou manobra de mobbing repelindo o predador {ev.get('predator_name', '')}.",
                    tick=self.tick,
                    cause="Incursão predatória com risco aos ninhos e infantes da comunidade",
                    result=f"Predador contra-atacado com {ev.get('damage', 0)} de dano e afugentado com sucesso",
                    importance=3,
                    location=(ev.get("x", 0.0), ev.get("y", 0.0)),
                    species=Organism.SPECIES_VRANCO,
                    clan_name=ev.get("clan_name"),
                    metadata={"participants": ev.get("participants_count"), "damage": ev.get("damage")},
                )

            elif ev_type == "predator_defeated":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.COMBAT_ENGAGEMENT.value,
                    title=f"Predador Abatido: {ev.get('predator_name', '')}",
                    description=f"O predador {ev.get('predator_name', '')} sucumbiu em combate direto contra a defesa integrada dos Vrancos ({ev.get('clan_name', 'Bando')}).",
                    tick=self.tick,
                    cause="Agressão de caça neutralizada por sobrepujança numérica em retaliação organizada",
                    result="Morte do predador em combate ativo",
                    importance=3,
                    clan_name=ev.get("clan_name"),
                )

            elif ev_type == "cultural_loss":
                self.chronicle.record_event(
                    event_type=ChronicleEventType.CULTURAL_LOSS.value,
                    title=f"Perda de Conhecimento Cultural: {ev.get('veteran_name', '')}",
                    description=f"{ev.get('veteran_name', '')} faleceu sem conseguir transmitir o conhecimento empírico exclusivo de {ev.get('lost_hotspots', 0)} sítio(s) de recursos.",
                    tick=self.tick,
                    cause="Falecimento de ancião antes da conclusão do ciclo de aprendizado social com os jovens",
                    result="Extinção cultural localizada de rotas e sítios estratégicos",
                    importance=3,
                    primary_organism_name=ev.get("veteran_name"),
                    metadata={"lost_hotspots": ev.get("lost_hotspots"), "xp_lost": ev.get("experience_lost")},
                )

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

        # Contagens por raça, coesão social e distribuição periférica
        vrancos = [o for o in self.organisms.values() if getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO]
        predators = [o for o in self.organisms.values() if getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_PREDATOR]

        vrancos_count = len(vrancos)
        predators_count = len(predators)

        # Média de indivíduos por grupo de Vrancos (vizinhança gregária de 90px)
        if vrancos_count > 0:
            group_sizes = []
            for v in vrancos:
                nearby_count = sum(1 for v2 in vrancos if math.hypot(v2.x - v.x, v2.y - v.y) <= 90.0)
                group_sizes.append(nearby_count)
            avg_vranco_group_size = round(sum(group_sizes) / vrancos_count, 1)
        else:
            avg_vranco_group_size = 0.0

        # Distribuição espacial (periferia vs centro)
        cx, cy = self.width / 2.0, self.height / 2.0
        center_thresh = min(self.width, self.height) * 0.38
        vrancos_in_periphery = sum(1 for v in vrancos if math.hypot(v.x - cx, v.y - cy) >= center_thresh)
        vrancos_periphery_pct = round((vrancos_in_periphery / vrancos_count * 100.0) if vrancos_count > 0 else 0.0, 1)

        predators_in_periphery = sum(1 for p in predators if math.hypot(p.x - cx, p.y - cy) >= center_thresh)
        predators_periphery_pct = round((predators_in_periphery / predators_count * 100.0) if predators_count > 0 else 0.0, 1)

        # Estatísticas de confrontos e predação a partir dos eventos recentes
        flee_count = sum(1 for e in self.recent_events if e.get("type") == "flee")
        combat_count = sum(1 for e in self.recent_events if e.get("type") == "combat")
        collective_defenses_count = sum(1 for e in self.recent_events if e.get("type") == "vranco_collective_defense")
        predation_attempts = sum(1 for e in self.recent_events if e.get("type") == "predation_attempt")
        predation_kills = sum(1 for e in self.recent_events if e.get("type") == "predation_kill")
        predators_defeated = sum(1 for e in self.recent_events if e.get("type") == "predator_defeated")

        total_hunt_interactions = predation_attempts + predation_kills
        hunting_success_rate = round((predation_kills / max(1, total_hunt_interactions)) * 100.0, 1) if total_hunt_interactions > 0 else 0.0

        return {
            "tick": self.tick,
            "population": pop_count,
            "vrancos_count": vrancos_count,
            "predators_count": predators_count,
            "vranco_avg_group_size": avg_vranco_group_size,
            "vrancos_periphery_pct": vrancos_periphery_pct,
            "predators_periphery_pct": predators_periphery_pct,
            "flee_count": flee_count,
            "combat_count": combat_count,
            "collective_defenses_count": collective_defenses_count,
            "predation_attempts": predation_attempts,
            "predation_kills": predation_kills,
            "predators_defeated": predators_defeated,
            "hunting_success_rate": hunting_success_rate,
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
            "settled_territories_count": sum(1 for z in self.territory_system.zones.values() if z.status == "SETTLED") if hasattr(self, "territory_system") else 0,
            "contested_territories_count": sum(1 for z in self.territory_system.zones.values() if z.status == "CONTESTED") if hasattr(self, "territory_system") else 0,
            "degraded_territories_count": sum(1 for z in self.territory_system.zones.values() if z.status == "DEGRADED") if hasattr(self, "territory_system") else 0,
            "avg_territory_quality": round(sum(z.quality_score for z in self.territory_system.zones.values()) / max(1, len(self.territory_system.zones)), 1) if hasattr(self, "territory_system") and self.territory_system.zones else 0.0,
            "stage_stats": stage_stats,
            "max_generation": max_generation,
            "total_mutations": total_mutations,
            "attr_stats": attr_stats,
            "season": self.environment_system.state.to_dict() if hasattr(self, "environment_system") else None,
            "ecology": self.environment_system.get_ecology_metrics(
                self.organisms,
                self.foods,
                self.territory_system.zones if hasattr(self, "territory_system") else {},
            ) if hasattr(self, "environment_system") else None,
            "evolution": self.genealogy.get_evolution_metrics(list(self.organisms.values()), list(self.clan_system.clans.values())),
            "culture": self.learning_system.get_cultural_metrics(self.organisms) if hasattr(self, "learning_system") else None,
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
            "territories": [z.to_dict() for z in self.territory_system.zones.values()] if hasattr(self, "territory_system") else [],
            "season": self.environment_system.state.to_dict() if hasattr(self, "environment_system") else None,
            "ecology": self.environment_system.get_ecology_metrics(
                self.organisms,
                self.foods,
                self.territory_system.zones if hasattr(self, "territory_system") else {},
            ) if hasattr(self, "environment_system") else None,
            "culture": self.learning_system.get_cultural_metrics(self.organisms) if hasattr(self, "learning_system") else None,
            "chronicle": self.chronicle.get_recent_summary(limit=10),
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
            "chronicle": self.chronicle.to_snapshot(),
            "environment": self.environment_system.state.to_dict() if hasattr(self, "environment_system") else None,
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
        if "chronicle" in snapshot:
            world.chronicle.load_from_snapshot(snapshot["chronicle"])

        for o_data in snapshot["organisms"]:
            org = Organism.from_dict(o_data)
            world.organisms[org.id] = org

        for f_data in snapshot["foods"]:
            food = Food.from_dict(f_data)
            world.foods[food.id] = food

        if hasattr(world, "environment_system"):
            world.environment_system.update(world.tick, world.organisms, world.foods, world.recent_events)

        return world
