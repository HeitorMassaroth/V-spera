"""Entidade Organismo, representando um animal autônomo com genoma, personalidade, memória e vínculos."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from .traits import OrganismTraits
from .genetics import AnimalGenome, AnimalPersonality, MutationRecord, Genotype, Phenotype, GeneticsEngine


@dataclass
class AnimalMemory:
    """Memória episódica de experiências marcantes e marcos espaciais estratégicos."""

    known_food_sources: List[Tuple[float, float, int]] = field(default_factory=list)  # [(x, y, tick)]
    danger_zones: List[Tuple[float, float, int]] = field(default_factory=list)        # [(x, y, tick)]
    lost_relatives: List[Dict[str, Any]] = field(default_factory=list)                # [{"name", "tick", "cause"}]
    safe_haven: Optional[Tuple[float, float]] = None                                  # (x, y) do ninho familiar

    def add_food_source(self, x: float, y: float, tick: int) -> None:
        """Memoriza uma localização fértil de alimento recente (mantém até 3 fontes)."""
        filtered = [s for s in self.known_food_sources if math.hypot(s[0] - x, s[1] - y) > 35.0]
        self.known_food_sources = [(round(x, 1), round(y, 1), tick)] + filtered[:2]

    def add_danger_zone(self, x: float, y: float, tick: int) -> None:
        """Memoriza local de ataque violento ou ferimento recente para evasão cautelosa."""
        filtered = [z for z in self.danger_zones if math.hypot(z[0] - x, z[1] - y) > 40.0]
        self.danger_zones = [(round(x, 1), round(y, 1), tick)] + filtered[:3]

    def add_lost_relative(self, name: str, tick: int, cause: str) -> None:
        """Registra a perda traumática de um parceiro ou filhote."""
        self.lost_relatives.append({"name": name, "tick": tick, "cause": cause})
        if len(self.lost_relatives) > 5:
            self.lost_relatives.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "known_food_sources": [[round(x, 1), round(y, 1), t] for x, y, t in self.known_food_sources],
            "danger_zones": [[round(x, 1), round(y, 1), t] for x, y, t in self.danger_zones],
            "lost_relatives": self.lost_relatives,
            "safe_haven": [round(self.safe_haven[0], 1), round(self.safe_haven[1], 1)] if self.safe_haven else None,
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
        return mem


class Organism:
    """Animal individual com genoma quantitativo, personalidade, vínculos e histórico genealógico."""

    # Papéis biológicos e cromáticos tradicionais
    ROLE_FEMALE = "FEMALE"  # Rosa (Fêmea)
    ROLE_MALE = "MALE"      # Verde (Macho)
    ROLE_CHILD = "CHILD"    # Roxo (Filhote em crescimento)

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
        traits: Optional[OrganismTraits] = None,
        genome: Optional[AnimalGenome] = None,
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
        current_state: str = STATE_FORAGING,
        carried_food: float = 0.0,
        mourning_ticks: int = 0,
        cause_of_death: Optional[str] = None,
        clan_id: Optional[int] = None,
        clan_role: Optional[str] = None,
    ) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.energy = energy
        self.age = age
        self.traits = traits if traits is not None else OrganismTraits()
        self.wander_angle = wander_angle
        self.generation = generation
        self.alive = True
        self.food_eaten = 0

        # Atributos Individuais e Genoma
        self.name = name if name else f"Animal#{id}"
        self.genome = genome if genome is not None else GeneticsEngine.generate_random_genotype(PRNG(id))
        self.genotype = self.genome
        self.personality = personality if personality is not None else AnimalPersonality()
        self.saude = saude if saude is not None else self.genome.max_saude

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
        self.current_state = current_state
        self.carried_food = carried_food

        # Ajusta propriedades físicas e cinemáticas a partir do genoma e papel
        self._sync_genome_to_traits()
        self.apply_role_traits(self.role)

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
            "wounds": round(max(0.0, self.genome.max_saude - self.saude), 1),
            "age": self.age,
            "current_state": self.current_state,
            "carried_food": round(self.carried_food, 1),
            "mourning_ticks": self.mourning_ticks,
        }

    def _sync_genome_to_traits(self) -> None:
        """Sincroniza os atributos quantitativos do genoma/fenótipo com os parâmetros físicos da simulação."""
        pheno = self.phenotype
        # Velocidade máxima calibrada por fenótipo expresso [1.0 - 120.0]
        self.traits.max_speed = 1.6 + (pheno.velocidade / 100.0) * 2.8
        # Raio de visão sensorial calibrado por fenótipo de detecção de ameaças [1.0 - 120.0]
        self.traits.vision_radius = 50.0 + (pheno.deteccao_ameacas / 100.0) * 45.0
        # Longevidade potencial expressa
        self.traits.max_age = int(max(500.0, pheno.longevidade_potencial))
        # Eficiência metabólica aprimorada por resistência e eficiência metabólica genética
        base_efficiency = max(0.40, 1.3 - (pheno.resistencia / 100.0) * 0.6)
        self.traits.metabolic_efficiency = base_efficiency / max(0.35, pheno.eficiencia_metabolica * pheno.eficiencia_coleta)

    def apply_role_traits(self, role: str) -> None:
        """Configura a cor, tamanho e limites cinemáticos baseados no papel e estágio de desenvolvimento."""
        self.role = role
        self._sync_genome_to_traits()

        if role == self.ROLE_FEMALE:
            self.sex = "F"
            self.life_stage = self.STAGE_ADULT
            self.traits.color_hue = 335.0   # Rosa vibrante (Fêmea)
            self.traits.size = 6.0
            self.traits.max_force = 0.24
        elif role == self.ROLE_MALE:
            self.sex = "M"
            self.life_stage = self.STAGE_ADULT
            self.traits.color_hue = 140.0   # Verde esmeralda (Macho)
            self.traits.size = 6.4
            self.traits.max_force = 0.28
        elif role == self.ROLE_CHILD:
            self.traits.color_hue = 280.0   # Roxo (Filhote em crescimento)
            # Calibração fina por estágio de vida
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialização completa para snapshot e consultas genealógicas detalhadas."""
        return {
            "id": self.id,
            "name": self.name,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "vx": round(self.vx, 3),
            "vy": round(self.vy, 3),
            "energy": round(self.energy, 2),
            "hunger": round(self.hunger, 2),
            "saude": round(self.saude, 2),
            "age": self.age,
            "sex": self.sex,
            "life_stage": self.life_stage,
            "life_expectancy": self.life_expectancy,
            "traits": self.traits.to_dict(),
            "genome": self.genome.to_dict(),
            "personality": self.personality.to_dict(),
            "memory": self.memory.to_dict(),
            "current_state": self.current_state,
            "carried_food": round(self.carried_food, 2),
            "wander_angle": round(self.wander_angle, 4),
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
        }

    def to_compact_dict(self) -> Dict[str, Any]:
        """Serialização compacta para streaming em tempo real de alto desempenho via WebSocket."""
        return {
            "id": self.id,
            "nm": self.name,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "e": round(self.energy, 1),
            "s": round(self.saude, 1),
            "sz": round(self.traits.size, 1),
            "h": self.traits.color_hue,
            "r": self.role[0],  # 'F' (Rosa), 'M' (Verde), 'C' (Roxo)
            "sx": self.sex,
            "st": self.life_stage[0],  # 'N' (Newborn), 'D' (Developing), 'J' (Juvenile), 'I' (Independent), 'A' (Adult)
            "act": self.current_state,
            "fam": self.family_id,
            "prt": self.partner_id,
            "cf": round(self.carried_food, 1),
            "cln": self.clan_id,
            "clr": self.clan_role[0] if self.clan_role else None, # 'A' (Alpha), 'B' (Beta), 'M' (Membro)
            "gen": self.generation,
            "a": self.age,
            "ms": round(self.genome.max_saude, 1),
            "f": round(self.genome.forca, 1),
            "v": round(self.genome.velocidade, 1),
            "res": round(self.genome.resistencia, 1),
            "i": round(self.genome.inteligencia, 1),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Organism:
        traits = OrganismTraits.from_dict(data["traits"])
        genome = AnimalGenome.from_dict(data.get("genome", {}))
        personality = AnimalPersonality.from_dict(data.get("personality", {}))
        mutations = [MutationRecord.from_dict(m) for m in data.get("mutations", [])]
        memory = AnimalMemory.from_dict(data.get("memory", {})) if "memory" in data else None

        role = data.get("role", cls.ROLE_MALE)
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
            current_state=data.get("current_state", cls.STATE_FORAGING),
            carried_food=data.get("carried_food", 0.0),
            mourning_ticks=data.get("mourning_ticks", 0),
            cause_of_death=data.get("cause_of_death"),
            clan_id=data.get("clan_id"),
            clan_role=data.get("clan_role"),
        )
        org.alive = data.get("alive", True)
        org.food_eaten = data.get("food_eaten", 0)
        return org
