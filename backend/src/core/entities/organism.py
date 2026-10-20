"""Entidade Organismo, representando um animal autônomo com genoma, personalidade, memória e vínculos."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from .traits import OrganismTraits
from .genetics import AnimalGenome, AnimalPersonality, MutationRecord, Genotype, Phenotype, GeneticsEngine
from .social import SocialRelationship
from .knowledge import AnimalKnowledge
from ..prng import PRNG


@dataclass
class EpisodicMemory:
    """Registro individual de um acontecimento marcante na vida do animal."""

    event_type: str                   # "ATTACKED_BY", "SURVIVED_COMBAT", "FOUND_FOOD", "RECEIVED_HELP", "GAVE_HELP", "LOST_RELATIVE", "EXPELLED", "WITNESSED_DEATH"
    description: str                  # Descrição legível para UI e análise
    tick: int                         # Momento exato em que ocorreu
    x: float                          # Coordenada X
    y: float                          # Coordenada Y
    intensity: float = 0.50           # Intensidade emocional/comportamental inicial [0.0, 1.0]
    relevance: float = 1.00           # Grau de relevância atual [0.0, 1.0] (decaimento com o tempo)
    involved_id: Optional[int] = None # ID do indivíduo envolvido (agressor, benfeitor, vítima)
    involved_name: Optional[str] = None # Nome do indivíduo envolvido

    def decay(self, elapsed_ticks: int, rate: float = 0.0008) -> float:
        """Aplica decaimento gradual de relevância temporal preservando piso emocional."""
        self.relevance = max(0.05, round(1.0 - (elapsed_ticks * rate), 2))
        return self.relevance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "tick": self.tick,
            "x": self.x,
            "y": self.y,
            "intensity": self.intensity,
            "relevance": self.relevance,
            "involved_id": self.involved_id,
            "involved_name": self.involved_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EpisodicMemory:
        return cls(
            event_type=str(data.get("event_type", "GENERIC")),
            description=str(data.get("description", "")),
            tick=int(data.get("tick", 0)),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            intensity=float(data.get("intensity", 0.5)),
            relevance=float(data.get("relevance", 1.0)),
            involved_id=data.get("involved_id"),
            involved_name=data.get("involved_name"),
        )


@dataclass
class AnimalMemory:
    """Memória episódica e espacial de experiências marcantes e marcos estratégicos."""

    known_food_sources: List[Tuple[float, float, int]] = field(default_factory=list)  # [(x, y, tick)]
    danger_zones: List[Tuple[float, float, int]] = field(default_factory=list)        # [(x, y, tick)]
    lost_relatives: List[Dict[str, Any]] = field(default_factory=list)                # [{"name", "tick", "cause"}]
    safe_haven: Optional[Tuple[float, float]] = None                                  # (x, y) do ninho familiar
    episodes: List[EpisodicMemory] = field(default_factory=list)                      # Memórias episódicas individuais
    max_episodes: int = 12

    def add_episode(
        self,
        event_type: str,
        description: str,
        tick: int,
        x: float,
        y: float,
        intensity: float = 0.50,
        relevance: float = 1.00,
        involved_id: Optional[int] = None,
        involved_name: Optional[str] = None,
    ) -> EpisodicMemory:
        """Registra acontecimento marcante e compacta mantendo apenas as memórias mais relevantes."""
        # Previne duplicação do mesmo evento para o mesmo indivíduo em intervalo curto (<= 4 ticks)
        for ep in self.episodes:
            if ep.event_type == event_type and ep.involved_id == involved_id and abs(ep.tick - tick) <= 4:
                ep.intensity = max(ep.intensity, min(1.0, max(0.1, intensity)))
                ep.relevance = max(ep.relevance, min(1.0, max(0.05, relevance)))
                return ep

        episode = EpisodicMemory(
            event_type=event_type,
            description=description,
            tick=tick,
            x=x,
            y=y,
            intensity=min(1.0, max(0.1, intensity)),
            relevance=min(1.0, max(0.05, relevance)),
            involved_id=involved_id,
            involved_name=involved_name,
        )
        self.episodes.append(episode)

        # Sincroniza com as coleções espaciais clássicas
        if event_type == "FOUND_FOOD":
            self.add_food_source(x, y, tick)
        elif event_type in ("ATTACKED_BY", "WITNESSED_DEATH"):
            self.add_danger_zone(x, y, tick)
        elif event_type == "LOST_RELATIVE" and involved_name:
            self.add_lost_relative(involved_name, tick, description)

        # Limite estrito de quantidade com mecanismo de compactação (descarta as de menor relevância ponderada)
        if len(self.episodes) > self.max_episodes:
            self.episodes.sort(key=lambda ep: ep.relevance * ep.intensity, reverse=True)
            self.episodes = self.episodes[:self.max_episodes]

        return episode

    def decay_memories(self, current_tick: int, rate: float = 0.0008) -> None:
        """Decai a relevância temporal das memórias ativas."""
        for ep in self.episodes:
            elapsed = max(0, current_tick - ep.tick)
            ep.decay(elapsed, rate)

    def get_grudge_score(self, target_id: int) -> float:
        """Calcula intensidade de ressentimento ou trauma em relação a um agressor específico."""
        score = 0.0
        for ep in self.episodes:
            if ep.event_type == "ATTACKED_BY" and ep.involved_id == target_id:
                score += ep.intensity * ep.relevance
        return min(2.0, score)

    def get_gratitude_score(self, target_id: int) -> float:
        """Calcula afinidade e gratidão em relação a quem prestou auxílio ou proteção."""
        score = 0.0
        for ep in self.episodes:
            if ep.event_type == "RECEIVED_HELP" and ep.involved_id == target_id:
                score += ep.intensity * ep.relevance
        return min(2.0, score)

    def has_memory_of_type(self, event_type: str) -> bool:
        """Verifica se o animal possui memórias ativas relevantes de um determinado tipo."""
        return any(ep.event_type == event_type and ep.relevance > 0.15 for ep in self.episodes)

    def add_food_source(self, x: float, y: float, tick: int) -> None:
        """Memoriza uma localização fértil de alimento recente (mantém até 3 fontes)."""
        filtered = [s for s in self.known_food_sources if math.hypot(s[0] - x, s[1] - y) > 35.0]
        self.known_food_sources = [(x, y, tick)] + filtered[:2]

    def add_danger_zone(self, x: float, y: float, tick: int) -> None:
        """Memoriza local de ataque violento ou ferimento recente para evasão cautelosa."""
        filtered = [z for z in self.danger_zones if math.hypot(z[0] - x, z[1] - y) > 40.0]
        self.danger_zones = [(x, y, tick)] + filtered[:3]

    def add_lost_relative(self, name: str, tick: int, cause: str) -> None:
        """Registra a perda traumática de um parceiro ou filhote."""
        self.lost_relatives.append({"name": name, "tick": tick, "cause": cause})
        if len(self.lost_relatives) > 5:
            self.lost_relatives.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "known_food_sources": [[x, y, t] for x, y, t in self.known_food_sources],
            "danger_zones": [[x, y, t] for x, y, t in self.danger_zones],
            "lost_relatives": self.lost_relatives,
            "safe_haven": [self.safe_haven[0], self.safe_haven[1]] if self.safe_haven else None,
            "episodes": [ep.to_dict() for ep in self.episodes],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnimalMemory:
        mem = cls()
        mem.known_food_sources = [(float(s[0]), float(s[1]), int(s[2])) for s in data.get("known_food_sources", [])]
        mem.danger_zones = [(float(z[0]), float(z[1]), int(z[2])) for z in data.get("danger_zones", [])]
        mem.lost_relatives = data.get("lost_relatives", [])
        haven = data.get("safe_haven")
        if haven:
            mem.safe_haven = (float(haven[0]), float(haven[1]))
        mem.episodes = [EpisodicMemory.from_dict(ep) for ep in data.get("episodes", [])]
        return mem


# Raças do Ecossistema
SPECIES_PREDATOR = "PREDATOR"
SPECIES_VRANCO = "VRANCO"

# Estados Comportamentais
STATE_FORAGING = "PROCURANDO_COMIDA"
STATE_RESTING = "DESCANSANDO"
STATE_COURTING = "CORTEJANDO"
STATE_DEFENDING = "DEFENDENDO_NINHO"
STATE_FLEEING = "FUGINDO"
STATE_HUNTING = "PREDANDO"
STATE_NURTURING = "CUIDANDO_FILHOTES"
STATE_DELIVERING_FOOD = "LEVANDO_COMIDA"
STATE_WANDERING = "EXPLORANDO"


class Organism:
    """Animal individual com genoma quantitativo, personalidade, vínculos e histórico genealógico."""

    # Raças do Ecossistema
    SPECIES_PREDATOR = SPECIES_PREDATOR
    SPECIES_VRANCO = SPECIES_VRANCO

    # Papéis biológicos e cromáticos tradicionais
    ROLE_FEMALE = "FEMALE"  # Fêmea
    ROLE_MALE = "MALE"      # Macho
    ROLE_CHILD = "CHILD"    # Filhote em crescimento

    # 5 Estágios de Desenvolvimento da Vida
    STAGE_NEWBORN = "NEWBORN"                  # 1. Recém-nascido: imóvel no ninho, 100% dependente
    STAGE_DEVELOPING = "DEVELOPING"            # 2. Filhote em desenvolvimento: passos curtos perto do ninho
    STAGE_JUVENILE = "JUVENILE"                # 3. Jovem: segue adultos e imita comportamentos
    STAGE_INDEPENDENT = "INDEPENDENT"          # 4. Jovem independente: forrageia e explora só
    STAGE_ADULT = "ADULT"                      # 5. Adulto: corteja, reproduz e funda territórios

    # Estados Comportamentais Dinâmicos
    STATE_FORAGING = "PROCURANDO_COMIDA"
    STATE_RESTING = "DESCANSANDO"
    STATE_COURTING = "CORTEJANDO"
    STATE_DEFENDING = "DEFENDENDO_NINHO"
    STATE_FLEEING = "FUGINDO"
    STATE_HUNTING = "PREDANDO"
    STATE_NURTURING = "CUIDANDO_FILHOTES"
    STATE_DELIVERING_FOOD = "LEVANDO_COMIDA"
    STATE_WANDERING = "EXPLORANDO"

    def __init__(
        self,
        id: int,
        x: float,
        y: float,
        name: str = "",
        vx: float = 0.0,
        vy: float = 0.0,
        energy: float = 100.0,
        saude: Optional[float] = None,
        age: int = 0,
        species: str = SPECIES_PREDATOR,
        traits: Optional[OrganismTraits] = None,
        genome: Optional[AnimalGenome] = None,
        genotype: Optional[Genotype] = None,
        personality: Optional[AnimalPersonality] = None,
        wander_angle: float = 0.0,
        generation: int = 0,
        father_id: Optional[int] = None,
        mother_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        role: str = ROLE_MALE,
        sex: Optional[str] = None,
        life_stage: Optional[str] = None,
        family_id: Optional[int] = None,
        home_cluster_id: Optional[int] = None,
        nest_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        partner_bond_tick: Optional[int] = None,
        maturity_ticks: int = 0,
        reproduction_cooldown: int = 0,
        children_ids: Optional[List[int]] = None,
        mutations: Optional[List[MutationRecord]] = None,
        genetic_history: Optional[List[Dict[str, Any]]] = None,
        memory: Optional[AnimalMemory] = None,
        knowledge: Optional[AnimalKnowledge] = None,
        current_state: str = STATE_FORAGING,
        carried_food: float = 0.0,
        mourning_ticks: int = 0,
        cause_of_death: Optional[str] = None,
        clan_id: Optional[int] = None,
        clan_role: Optional[str] = None,
        relationships: Optional[Dict[int, SocialRelationship]] = None,
        max_relationships: int = 15,
        territory_id: Optional[int] = None,
        territory_cooldown: int = 0,
        target_migration_zone: Optional[Tuple[float, float]] = None,
    ) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.energy = energy
        self.age = age
        self.species = species
        self._custom_max_age = traits.max_age if traits is not None else None
        self.traits = traits if traits is not None else OrganismTraits()
        self.wander_angle = wander_angle
        self.generation = generation
        self.alive = True
        self.food_eaten = 0

        # Atributos Individuais e Genoma
        self.name = name if name else f"{'Vranco' if species == self.SPECIES_VRANCO else 'Animal'}#{id}"
        g = genotype if genotype is not None else genome
        self.genome = g if g is not None else Genotype()
        self.genotype = self.genome
        self.personality = personality if personality is not None else AnimalPersonality()
        self.saude = saude if saude is not None else self.max_saude

        # Sexo biológico e estágio de vida
        if sex is not None:
            self.sex = sex
        else:
            self.sex = "F" if role == self.ROLE_FEMALE else "M"

        if life_stage is not None:
            self.life_stage = life_stage
        else:
            self.life_stage = self.STAGE_ADULT if role != self.ROLE_CHILD else self.STAGE_NEWBORN

        # Expectativa de vida projetada
        self.life_expectancy = int(1400 + (self.genome.resistencia / 100.0) * 1200)

        # Genealogia e parentesco
        self.father_id = father_id
        self.mother_id = mother_id
        self.parent_id = parent_id if parent_id is not None else mother_id
        self.children_ids: List[int] = children_ids if children_ids is not None else []
        self.mutations: List[MutationRecord] = mutations if mutations is not None else []
        self.genetic_history: List[Dict[str, Any]] = genetic_history if genetic_history is not None else []

        # Propriedades familiares e sociais permanentes
        self.role = role
        self.family_id = family_id
        self.home_cluster_id = home_cluster_id
        self.nest_id = nest_id
        self.partner_id = partner_id
        self.partner_bond_tick = partner_bond_tick
        self.maturity_ticks = maturity_ticks
        self.reproduction_cooldown = reproduction_cooldown
        self.mourning_ticks = mourning_ticks
        self.cause_of_death = cause_of_death
        self.clan_id = clan_id
        self.clan_role = clan_role

        # Memória e dinâmica comportamental
        self.memory = memory if memory is not None else AnimalMemory()
        self.knowledge = knowledge if knowledge is not None else AnimalKnowledge()
        self.current_state = current_state
        self.carried_food = carried_food

        # Relações sociais seletivas e reputação individual
        self.relationships: Dict[int, SocialRelationship] = relationships if relationships is not None else {}
        self.max_relationships: int = max_relationships

        # Território e Migração
        self.territory_id: Optional[int] = territory_id
        self.territory_cooldown: int = territory_cooldown
        self.target_migration_zone: Optional[Tuple[float, float]] = target_migration_zone

        # Ajusta propriedades físicas e cinemáticas a partir do genoma e papel apenas se traits não foram fornecidos
        if traits is None:
            self._sync_genome_to_traits()
            self.apply_role_traits(self.role)

    def distance_to(self, x: float, y: float) -> float:
        """Calcula a distância euclidiana até coordenadas alvo no ambiente."""
        return math.hypot(x - self.x, y - self.y)

    @property
    def max_saude(self) -> float:
        """Saúde máxima efetiva calibrada por espécie e fenótipo."""
        base = getattr(self.genome, "max_saude", 100.0)
        return round(base * 0.60, 1) if getattr(self, "species", self.SPECIES_PREDATOR) == self.SPECIES_VRANCO else round(base, 1)

    @property
    def phenotype(self) -> Phenotype:
        """Calcula o fenótipo expresso do indivíduo (interação de genótipo, ontogenia, estado de saúde e endogamia)."""
        return Phenotype.calculate(
            genotype=self.genome,
            life_stage=self.life_stage,
            energy=self.energy,
            saude=self.saude,
        )

    @property
    def current_state_info(self) -> Dict[str, Any]:
        """Separação rigorosa do estado atual temporário (fome, energia, ferimentos, cansaço)."""
        return {
            "energy": round(self.energy, 1),
            "saude": round(self.saude, 1),
            "hunger": round(self.hunger, 1),
            "wounds": round(max(0.0, self.max_saude - self.saude), 1),
            "age": self.age,
            "current_state": self.current_state,
            "carried_food": round(self.carried_food, 1),
            "mourning_ticks": self.mourning_ticks,
            "species": self.species,
        }

    def _sync_genome_to_traits(self) -> None:
        """Sincroniza os atributos quantitativos do genoma/fenótipo com os parâmetros físicos da simulação."""
        pheno = self.phenotype
        is_vranco = getattr(self, "species", self.SPECIES_PREDATOR) == self.SPECIES_VRANCO

        if is_vranco:
            # Vrancos: velocidade ampliada [2.4 - 5.8], sentidos aguçados, biomassa menor
            self.traits.max_speed = 2.4 + (pheno.velocidade / 100.0) * 3.4
            self.traits.vision_radius = 65.0 + (pheno.deteccao_ameacas / 100.0) * 55.0
            if getattr(self, "_custom_max_age", None) is not None:
                self.traits.max_age = self._custom_max_age
            else:
                self.traits.max_age = int(max(400.0, pheno.longevidade_potencial * 0.90))
            base_efficiency = max(0.35, 1.15 - (pheno.resistencia / 100.0) * 0.50)
            self.traits.metabolic_efficiency = base_efficiency / max(0.35, pheno.eficiencia_metabolica * pheno.eficiencia_coleta)
        else:
            # Predadores tradicionais
            self.traits.max_speed = 1.6 + (pheno.velocidade / 100.0) * 2.8
            self.traits.vision_radius = 50.0 + (pheno.deteccao_ameacas / 100.0) * 45.0
            if getattr(self, "_custom_max_age", None) is not None:
                self.traits.max_age = self._custom_max_age
            else:
                self.traits.max_age = int(max(500.0, pheno.longevidade_potencial))
            base_efficiency = max(0.40, 1.3 - (pheno.resistencia / 100.0) * 0.6)
            self.traits.metabolic_efficiency = base_efficiency / max(0.35, pheno.eficiencia_metabolica * pheno.eficiencia_coleta)

    def apply_role_traits(self, role: str) -> None:
        """Configura a cor, tamanho e limites cinemáticos baseados no papel, espécie e estágio de desenvolvimento."""
        self.role = role
        self._sync_genome_to_traits()

        is_vranco = getattr(self, "species", self.SPECIES_PREDATOR) == self.SPECIES_VRANCO

        if role == self.ROLE_FEMALE:
            self.sex = "F"
            self.life_stage = self.STAGE_ADULT
            if is_vranco:
                self.traits.color_hue = 55.0   # Âmbar suave / canário (Fêmea Vranco)
                self.traits.size = 3.8
                self.traits.max_force = 0.28
            else:
                self.traits.color_hue = 335.0  # Rosa vibrante (Fêmea Predadora)
                self.traits.size = 6.0
                self.traits.max_force = 0.24
        elif role == self.ROLE_MALE:
            self.sex = "M"
            self.life_stage = self.STAGE_ADULT
            if is_vranco:
                self.traits.color_hue = 45.0   # Dourado âmbar quente (Macho Vranco)
                self.traits.size = 4.2
                self.traits.max_force = 0.32
            else:
                self.traits.color_hue = 140.0  # Verde esmeralda (Macho Predador)
                self.traits.size = 6.4
                self.traits.max_force = 0.28
        elif role == self.ROLE_CHILD:
            if is_vranco:
                self.traits.color_hue = 35.0   # Areia / creme pálido (Filhote Vranco)
                if self.life_stage == self.STAGE_NEWBORN:
                    self.traits.size = 2.4
                    self.traits.max_speed = 0.0
                    self.traits.max_force = 0.0
                    self.vx = 0.0
                    self.vy = 0.0
                elif self.life_stage == self.STAGE_DEVELOPING:
                    self.traits.size = 2.8
                    self.traits.max_speed = max(0.8, self.traits.max_speed * 0.40)
                    self.traits.max_force = 0.10
                elif self.life_stage == self.STAGE_JUVENILE:
                    self.traits.size = 3.2
                    self.traits.max_speed = max(1.5, self.traits.max_speed * 0.65)
                    self.traits.max_force = 0.18
                elif self.life_stage == self.STAGE_INDEPENDENT:
                    self.traits.size = 3.6
                    self.traits.max_speed = max(1.8, self.traits.max_speed * 0.88)
                    self.traits.max_force = 0.24
                else:
                    growth_progress = min(1.0, self.maturity_ticks / 180.0)
                    self.traits.size = 2.4 + growth_progress * 1.4
                    self.traits.max_speed = max(1.4, self.traits.max_speed * 0.75)
                    self.traits.max_force = 0.20
            else:
                self.traits.color_hue = 280.0  # Roxo (Filhote Predador)
                if self.life_stage == self.STAGE_NEWBORN:
                    self.traits.size = 3.5
                    self.traits.max_speed = 0.0     # Imóvel no ninho
                    self.traits.max_force = 0.0
                    self.vx = 0.0
                    self.vy = 0.0
                elif self.life_stage == self.STAGE_DEVELOPING:
                    self.traits.size = 3.8
                    self.traits.max_speed = max(0.6, self.traits.max_speed * 0.35)
                    self.traits.max_force = 0.08
                elif self.life_stage == self.STAGE_JUVENILE:
                    self.traits.size = 4.6
                    self.traits.max_speed = max(1.2, self.traits.max_speed * 0.60)
                    self.traits.max_force = 0.16
                elif self.life_stage == self.STAGE_INDEPENDENT:
                    self.traits.size = 5.4
                    self.traits.max_speed = max(1.5, self.traits.max_speed * 0.85)
                    self.traits.max_force = 0.22
                else:
                    growth_progress = min(1.0, self.maturity_ticks / 180.0)
                    self.traits.size = 3.5 + growth_progress * 2.5
                    self.traits.max_speed = max(1.2, self.traits.max_speed * 0.75)
                    self.traits.max_force = 0.18

    @property
    def speed(self) -> float:
        """Módulo da velocidade escalar atual."""
        return math.hypot(self.vx, self.vy)

    @property
    def heading(self) -> float:
        """Ângulo direcional do vetor velocidade em radianos."""
        return math.atan2(self.vy, self.vx)

    @property
    def hunger(self) -> float:
        """Nível de fome [0.0 - 100.0], complementar à reserva de energia."""
        return max(0.0, 100.0 - self.energy)

    @property
    def is_alive(self) -> bool:
        """Indica se o organismo está vivo no ecossistema."""
        return self.alive

    def get_relationship(self, target_id: int) -> Optional[SocialRelationship]:
        """Obtém o relacionamento social com outro indivíduo se já registrado."""
        return self.relationships.get(target_id)

    def get_or_create_relationship(
        self,
        target_id: int,
        target_name: str = "",
        target_species: str = "PREDATOR",
    ) -> SocialRelationship:
        """Obtém ou instancia relação social seletiva aplicando baselines biológicos e de parentesco."""
        if target_id in self.relationships:
            rel = self.relationships[target_id]
            if target_name and not rel.target_name:
                rel.target_name = target_name
            return rel

        # Baselines biológicos e sociais baseados em parentesco e espécie
        is_partner = (target_id == self.partner_id)
        is_parent = (target_id in (self.father_id, self.mother_id))
        is_child = (target_id in self.children_ids)
        is_same_fam = (self.family_id is not None and target_id == self.family_id)
        is_vranco_both = (self.species == SPECIES_VRANCO and target_species == SPECIES_VRANCO)
        is_diff_species = (self.species != target_species)

        if is_partner:
            base_trust, base_affinity, base_fear, base_host = 0.90, 0.95, 0.0, 0.0
        elif is_parent or is_child:
            base_trust, base_affinity, base_fear, base_host = 0.85, 0.88, 0.0, 0.0
        elif is_same_fam:
            base_trust, base_affinity, base_fear, base_host = 0.75, 0.75, 0.0, 0.0
        elif is_vranco_both:
            base_trust, base_affinity, base_fear, base_host = 0.65, 0.70, 0.0, 0.0
        elif is_diff_species:
            base_trust = 0.10
            base_affinity = 0.10
            base_fear = 0.45 if self.species == SPECIES_VRANCO else 0.0
            base_host = 0.40 if self.species == SPECIES_PREDATOR else 0.0
        else:
            base_trust, base_affinity, base_fear, base_host = 0.50, 0.50, 0.0, 0.0

        rel = SocialRelationship(
            target_id=target_id,
            target_name=target_name,
            target_species=target_species,
            trust=base_trust,
            affinity=base_affinity,
            fear=base_fear,
            rivalry=0.0,
            hostility=base_host,
            cooperation_count=0,
            last_interaction_tick=getattr(self, "age", 0),
        )
        self.relationships[target_id] = rel

        if len(self.relationships) > self.max_relationships:
            self.prune_relationships()

        return rel

    def update_social_interaction(
        self,
        target_id: int,
        interaction_type: str,
        intensity: float = 1.0,
        tick: int = 0,
        target_name: str = "",
        target_species: str = "PREDATOR",
    ) -> SocialRelationship:
        """
        Atualiza dinamicamente as dimensões de relacionamento conforme a interação ocorrida.
        Tipos: 'HELP_RECEIVED', 'HELP_GIVEN', 'ATTACK_RECEIVED', 'ATTACK_DEALT', 'COOPERATION',
               'RESOURCE_SHARING', 'COMPETITION', 'DESERTION', 'EXPULSION'
        """
        rel = self.get_or_create_relationship(target_id, target_name=target_name, target_species=target_species)
        rel.last_interaction_tick = tick
        if target_name:
            rel.target_name = target_name

        intensity = min(1.0, max(0.1, intensity))
        coragem_val = getattr(self.personality, "coragem", 0.5)
        cautela_val = getattr(self.personality, "cautela", 0.5)
        soc_val = getattr(self.personality, "sociabilidade", 0.5)

        if interaction_type == "HELP_RECEIVED":
            rel.trust = min(1.0, rel.trust + 0.18 * intensity * (0.8 + 0.4 * soc_val))
            rel.affinity = min(1.0, rel.affinity + 0.20 * intensity * (0.8 + 0.4 * soc_val))
            rel.fear = max(0.0, rel.fear - 0.25 * intensity)
            rel.hostility = max(0.0, rel.hostility - 0.30 * intensity)
            rel.cooperation_count += 1

        elif interaction_type == "HELP_GIVEN":
            rel.affinity = min(1.0, rel.affinity + 0.10 * intensity * (0.8 + 0.4 * soc_val))
            rel.trust = min(1.0, rel.trust + 0.08 * intensity)
            rel.cooperation_count += 1

        elif interaction_type == "ATTACK_RECEIVED":
            rel.trust = max(-1.0, rel.trust - 0.40 * intensity)
            rel.affinity = max(-1.0, rel.affinity - 0.35 * intensity)
            rel.hostility = min(1.0, rel.hostility + 0.35 * intensity)
            fear_gain = 0.40 * intensity * (0.5 + 0.5 * cautela_val) * (1.2 - 0.6 * coragem_val)
            rel.fear = min(1.0, rel.fear + fear_gain)
            if coragem_val >= 0.55:
                rel.rivalry = min(1.0, rel.rivalry + 0.30 * intensity * coragem_val)

        elif interaction_type == "ATTACK_DEALT":
            rel.hostility = min(1.0, rel.hostility + 0.15 * intensity)
            rel.rivalry = min(1.0, rel.rivalry + 0.20 * intensity)

        elif interaction_type in ("COOPERATION", "RESOURCE_SHARING"):
            rel.trust = min(1.0, rel.trust + 0.14 * intensity * (0.7 + 0.6 * soc_val))
            rel.affinity = min(1.0, rel.affinity + 0.15 * intensity * (0.7 + 0.6 * soc_val))
            rel.rivalry = max(0.0, rel.rivalry - 0.15 * intensity)
            rel.hostility = max(0.0, rel.hostility - 0.20 * intensity)
            rel.cooperation_count += 1

        elif interaction_type == "COMPETITION":
            rel.rivalry = min(1.0, rel.rivalry + 0.20 * intensity)
            rel.trust = max(-1.0, rel.trust - 0.10 * intensity)
            rel.affinity = max(-1.0, rel.affinity - 0.10 * intensity)

        elif interaction_type == "DESERTION":
            rel.trust = max(-1.0, rel.trust - 0.35 * intensity)
            rel.affinity = max(-1.0, rel.affinity - 0.30 * intensity)

        elif interaction_type == "EXPULSION":
            rel.trust = max(-1.0, rel.trust - 0.50 * intensity)
            rel.affinity = max(-1.0, rel.affinity - 0.45 * intensity)
            rel.hostility = min(1.0, rel.hostility + 0.40 * intensity)
            rel.rivalry = min(1.0, rel.rivalry + 0.35 * intensity)

        rel.trust = round(rel.trust, 3)
        rel.affinity = round(rel.affinity, 3)
        rel.fear = round(rel.fear, 3)
        rel.rivalry = round(rel.rivalry, 3)
        rel.hostility = round(rel.hostility, 3)

        return rel

    def decay_relationships(self, current_tick: int, rate: float = 0.0003) -> None:
        """Aplica decaimento gradual a relações sem interações recentes."""
        for rel in list(self.relationships.values()):
            elapsed = max(0, current_tick - rel.last_interaction_tick)
            rel.decay(elapsed, rate)

    def prune_relationships(self) -> None:
        """Descarta relacionamentos de menor significância mantendo vínculos essenciais."""
        if len(self.relationships) <= self.max_relationships:
            return

        protected_ids = {self.partner_id, self.father_id, self.mother_id} | set(self.children_ids)
        protected_ids.discard(None)

        sorted_rels = sorted(
            self.relationships.items(),
            key=lambda item: (item[0] in protected_ids, item[1].significance()),
            reverse=True,
        )

        self.relationships = dict(sorted_rels[:self.max_relationships])

    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa para snapshot e consultas genealógicas detalhadas."""
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "energy": self.energy,
            "hunger": self.hunger,
            "saude": self.saude,
            "age": self.age,
            "sex": self.sex,
            "life_stage": self.life_stage,
            "life_expectancy": self.life_expectancy,
            "traits": self.traits.to_dict(),
            "genome": self.genome.to_dict(),
            "personality": self.personality.to_dict(),
            "memory": self.memory.to_dict(),
            "knowledge": self.knowledge.to_dict(),
            "current_state": self.current_state,
            "carried_food": self.carried_food,
            "wander_angle": self.wander_angle,
            "generation": self.generation,
            "father_id": self.father_id,
            "mother_id": self.mother_id,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "mutations": [m.to_dict() for m in self.mutations],
            "genetic_history": self.genetic_history,
            "alive": self.alive,
            "food_eaten": self.food_eaten,
            "role": self.role,
            "family_id": self.family_id,
            "home_cluster_id": self.home_cluster_id,
            "nest_id": self.nest_id,
            "partner_id": self.partner_id,
            "partner_bond_tick": self.partner_bond_tick,
            "maturity_ticks": self.maturity_ticks,
            "reproduction_cooldown": self.reproduction_cooldown,
            "mourning_ticks": self.mourning_ticks,
            "cause_of_death": self.cause_of_death,
            "clan_id": self.clan_id,
            "clan_role": self.clan_role,
            "genotype": self.genome.to_detailed_dict(),
            "phenotype": self.phenotype.to_dict(),
            "current_state_info": self.current_state_info,
            "inbreeding_coefficient": self.genome.inbreeding_coefficient,
            "lineage_id": self.genome.lineage_id,
            "lineage_name": self.genome.lineage_name,
            "species": self.species,
            "relationships": [r.to_dict() for r in self.relationships.values()],
            "territory_id": self.territory_id,
            "territory_cooldown": self.territory_cooldown,
            "target_migration_zone": list(self.target_migration_zone) if self.target_migration_zone else None,
        }

    def to_compact_dict(self) -> Dict[str, Any]:
        """Serialização compacta para streaming em tempo real de alto desempenho via WebSocket."""
        return {
            "id": self.id,
            "nm": self.name,
            "sp": "V" if self.species == self.SPECIES_VRANCO else "P",
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "e": round(self.energy, 1),
            "s": round(self.saude, 1),
            "sz": round(self.traits.size, 1),
            "h": self.traits.color_hue,
            "r": self.role[0],  # 'F' (Rosa/Âmbar suave), 'M' (Verde/Dourado), 'C' (Roxo/Areia)
            "sx": self.sex,
            "st": self.life_stage[0],  # 'N' (Newborn), 'D' (Developing), 'J' (Juvenile), 'I' (Independent), 'A' (Adult)
            "act": self.current_state,
            "fam": self.family_id,
            "prt": self.partner_id,
            "cf": round(self.carried_food, 1),
            "cln": self.clan_id,
            "clr": (
                "A" if self.clan_role == "ALPHA"
                else "B" if self.clan_role == "BETA"
                else "G" if self.clan_role == "GUARDIAN"
                else "K" if self.clan_role == "COLLECTOR"
                else "N" if self.clan_role == "NURSE"
                else ("M" if self.clan_role else None)
            ),
            "tid": self.territory_id,
            "gen": self.generation,
            "a": self.age,
            "ms": round(self.max_saude, 1),
            "f": round(self.genome.forca, 1),
            "v": round(self.genome.velocidade, 1),
            "res": round(self.genome.resistencia, 1),
            "i": round(self.genome.inteligencia, 1),
            "xp": round(self.knowledge.experience_points, 1),
            "evs": round(self.knowledge.tactical_skills.evasion_proficiency, 2),
            "hts": round(self.knowledge.tactical_skills.hunting_proficiency, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Organism:
        traits = OrganismTraits.from_dict(data["traits"])
        genome = AnimalGenome.from_dict(data.get("genome", {}))
        personality = AnimalPersonality.from_dict(data.get("personality", {}))
        mutations = [MutationRecord.from_dict(m) for m in data.get("mutations", [])]
        memory = AnimalMemory.from_dict(data.get("memory", {})) if "memory" in data else None
        knowledge = AnimalKnowledge.from_dict(data.get("knowledge", {})) if "knowledge" in data else None

        role = data.get("role", cls.ROLE_MALE)
        species = data.get("species", cls.SPECIES_PREDATOR)
        org = cls(
            id=data["id"],
            name=data.get("name", f"Animal#{data['id']}"),
            x=data["x"],
            y=data["y"],
            vx=data.get("vx", 0.0),
            vy=data.get("vy", 0.0),
            energy=data.get("energy", 100.0),
            saude=data.get("saude"),
            age=data.get("age", 0),
            species=species,
            traits=traits,
            genome=genome,
            personality=personality,
            wander_angle=data.get("wander_angle", 0.0),
            generation=data.get("generation", 0),
            father_id=data.get("father_id"),
            mother_id=data.get("mother_id"),
            parent_id=data.get("parent_id"),
            role=role,
            sex=data.get("sex", "F" if role == cls.ROLE_FEMALE else "M"),
            life_stage=data.get("life_stage", cls.STAGE_ADULT if role != cls.ROLE_CHILD else cls.STAGE_NEWBORN),
            family_id=data.get("family_id"),
            home_cluster_id=data.get("home_cluster_id"),
            nest_id=data.get("nest_id"),
            partner_id=data.get("partner_id"),
            partner_bond_tick=data.get("partner_bond_tick"),
            maturity_ticks=data.get("maturity_ticks", 0),
            reproduction_cooldown=data.get("reproduction_cooldown", 0),
            children_ids=data.get("children_ids", []),
            mutations=mutations,
            genetic_history=data.get("genetic_history", []),
            memory=memory,
            knowledge=knowledge,
            current_state=data.get("current_state", cls.STATE_FORAGING),
            carried_food=data.get("carried_food", 0.0),
            mourning_ticks=data.get("mourning_ticks", 0),
            cause_of_death=data.get("cause_of_death"),
            clan_id=data.get("clan_id"),
            clan_role=data.get("clan_role"),
            territory_id=data.get("territory_id"),
            territory_cooldown=data.get("territory_cooldown", 0),
            target_migration_zone=tuple(data["target_migration_zone"]) if data.get("target_migration_zone") else None,
        )
        if "relationships" in data:
            org.relationships = {
                int(r["target_id"]): SocialRelationship.from_dict(r)
                for r in data["relationships"]
            }
        org.alive = data.get("alive", True)
        org.food_eaten = data.get("food_eaten", 0)
        return org
