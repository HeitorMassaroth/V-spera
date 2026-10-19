"""Sistema de dinâmica familiar completo, vínculos permanentes, ninhos, criação parental e combate territorial."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from ..entities.organism import Organism, AnimalMemory
from ..entities.nest import Nest
from ..entities.genetics import GeneticsEngine, AnimalGenome, AnimalPersonality, MutationRecord
from ..entities.genealogy import GenealogyRegistry
from ..prng import PRNG

CLAN_NAMES = [
    "Clã Solaris", "Clã Apex", "Clã Ignis", "Clã Sylva", "Clã Terra",
    "Clã Umbra", "Clã Astra", "Clã Zephyr", "Clã Boreas", "Clã Titan",
    "Clã Vulcan", "Clã Orion", "Clã Chronos", "Clã Fenrir", "Clã Chimera"
]


def get_clan_name(family_id: int) -> str:
    """Retorna o nome cerimonial do clã familiar baseado no ID da família."""
    return CLAN_NAMES[(family_id - 1) % len(CLAN_NAMES)]


@dataclass
class Family:
    """Entidade de primeira classe representando um clã/família ativo no ecossistema."""

    id: int
    clan_name: str
    home_cluster_id: Optional[int]
    patriarch_id: Optional[int]
    matriarch_id: Optional[int]
    nest_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)
    founded_tick: int = 0
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "clan_name": self.clan_name,
            "home_cluster_id": self.home_cluster_id,
            "patriarch_id": self.patriarch_id,
            "matriarch_id": self.matriarch_id,
            "nest_id": self.nest_id,
            "children_count": len(self.children_ids),
            "founded_tick": self.founded_tick,
            "is_active": self.is_active,
        }


class FamilySystem:
    """Gerencia ciclo de vida completo de famílias, vínculos permanentes, ninhos, criação e sobrevivência."""

    def __init__(
        self,
        cluster_radius: float = 90.0,
        energy_threshold_form_family: float = 105.0,
        energy_threshold_reproduce: float = 95.0,
        maturity_threshold: int = 180,
        reproduction_cooldown: int = 120,
    ) -> None:
        self.cluster_radius = cluster_radius
        self.energy_form_family = energy_threshold_form_family
        self.energy_reproduce = energy_threshold_reproduce
        self.maturity_threshold = maturity_threshold
        self.cooldown_ticks = reproduction_cooldown
        self.families: Dict[int, Family] = {}
        self.cluster_homes: Dict[int, int] = {}  # cluster_idx -> family_id
        self.nests: Dict[int, Nest] = {}          # nest_id -> Nest
        self._next_nest_id_counter: int = 1

    def _next_nest_id(self) -> int:
        nid = self._next_nest_id_counter
        self._next_nest_id_counter += 1
        return nid

    def update(
        self,
        organisms: Dict[int, Organism],
        food_clusters: List[Tuple[float, float]],
        prng: PRNG,
        next_entity_id_fn,
        next_family_id_fn,
        genealogy: GenealogyRegistry,
        pop_averages: Dict[str, float],
        tick: int,
    ) -> Tuple[List[Organism], List[Dict[str, Any]]]:
        """Executa a lógica social, cortejo, ninhos, cuidado parental, combate e predação por tick."""
        events: List[Dict[str, Any]] = []

        # 1. Sincroniza estado das famílias, vínculos, luto por parceiros e territórios
        self._sync_families_and_partners(organisms, food_clusters, genealogy, events, tick)

        # 2. Atualiza os 5 estágios de desenvolvimento dos filhotes e dispersão de novos adultos
        self._update_growth_and_stages(organisms, prng, genealogy, events, tick)

        # 3. Formação de famílias, cortejo e construção de ninhos
        self._form_and_maintain_families(organisms, food_clusters, next_family_id_fn, genealogy, prng, events, tick)

        # 4. Reprodução condicionada à disponibilidade real de recursos e segurança
        newborns = self._food_conditioned_reproduction(
            organisms,
            prng,
            next_entity_id_fn,
            genealogy,
            pop_averages,
            events,
            tick,
        )

        # 5. Cuidado parental: entrega de comida no ninho pelo pai e amamentação/abrigo pela mãe
        self._parental_care_and_food_delivery(organisms, events, tick)

        # 6. Combate territorial do Macho e predação de filhotes vulneráveis
        self._territorial_combat_and_predation(organisms, food_clusters, events, tick)

        return newborns, events

    def _sync_families_and_partners(
        self,
        organisms: Dict[int, Organism],
        food_clusters: List[Tuple[float, float]],
        genealogy: GenealogyRegistry,
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Mantém registros de famílias vivos, lida com viuvez, luto e liberação de ninhos abandonados."""
        for org in sorted(organisms.values(), key=lambda o: o.id):
            if org.mourning_ticks > 0:
                org.mourning_ticks -= 1

            if org.partner_id is not None:
                partner = organisms.get(org.partner_id)
                if partner is None or not partner.alive:
                    lost_name = f"Parceiro#{org.partner_id}" if partner is None else partner.name
                    mourning_time = int(30 + getattr(org.personality, "sociabilidade", 0.5) * 35)
                    org.mourning_ticks = mourning_time
                    if getattr(org, "memory", None):
                        org.memory.add_lost_relative(lost_name, tick, "Falecimento do Parceiro")
                    org.partner_id = None
                    events.append({
                        "type": "partner_lost",
                        "survivor_name": org.name,
                        "lost_partner": lost_name,
                        "clan_name": get_clan_name(org.family_id) if org.family_id else "Solitário",
                        "tick": tick,
                    })
                else:
                    if org.partner_bond_tick is not None:
                        bond_duration = tick - org.partner_bond_tick
                        genealogy.update_bond_duration(org.id, bond_duration)

            if org.family_id is not None:
                if org.family_id not in self.families:
                    self.families[org.family_id] = Family(
                        id=org.family_id,
                        clan_name=get_clan_name(org.family_id),
                        home_cluster_id=org.home_cluster_id,
                        patriarch_id=org.id if org.role == Organism.ROLE_MALE else None,
                        matriarch_id=org.id if org.role == Organism.ROLE_FEMALE else None,
                        nest_id=org.nest_id,
                        founded_tick=tick,
                        is_active=True,
                    )
                else:
                    fam = self.families[org.family_id]
                    if org.role == Organism.ROLE_MALE and fam.patriarch_id is None:
                        fam.patriarch_id = org.id
                    elif org.role == Organism.ROLE_FEMALE and fam.matriarch_id is None:
                        fam.matriarch_id = org.id
                    if fam.home_cluster_id is None and org.home_cluster_id is not None:
                        fam.home_cluster_id = org.home_cluster_id
                    if fam.nest_id is None and org.nest_id is not None:
                        fam.nest_id = org.nest_id

        # Verifica integridade de cada clã/família
        for fam_id, family in list(self.families.items()):
            if not family.is_active:
                continue

            patriarch = organisms.get(family.patriarch_id) if family.patriarch_id else None
            matriarch = organisms.get(family.matriarch_id) if family.matriarch_id else None

            if patriarch is None or not patriarch.alive or patriarch.family_id != fam_id:
                family.patriarch_id = None

            if matriarch is None or not matriarch.alive or matriarch.family_id != fam_id:
                family.matriarch_id = None

            # Sincroniza vínculos entre patriarca e matriarca
            if patriarch and matriarch:
                if patriarch.partner_id is None:
                    patriarch.partner_id = matriarch.id
                    patriarch.partner_bond_tick = tick
                if matriarch.partner_id is None:
                    matriarch.partner_id = patriarch.id
                    matriarch.partner_bond_tick = tick

            family.children_ids = [
                cid for cid in family.children_ids
                if cid in organisms and organisms[cid].alive and organisms[cid].role == Organism.ROLE_CHILD
            ]

            # Se todos os membros faleceram ou dispersaram: clã é extinto
            if family.patriarch_id is None and family.matriarch_id is None and len(family.children_ids) == 0:
                family.is_active = False
                if family.home_cluster_id is not None:
                    if self.cluster_homes.get(family.home_cluster_id) == fam_id:
                        del self.cluster_homes[family.home_cluster_id]
                    family.home_cluster_id = None

                if family.nest_id is not None and family.nest_id in self.nests:
                    self.nests[family.nest_id].is_active = False

                events.append({
                    "type": "clan_extinct",
                    "clan_name": family.clan_name,
                    "family_id": fam_id,
                    "tick": tick,
                })
            else:
                if family.home_cluster_id is not None:
                    self.cluster_homes[family.home_cluster_id] = fam_id

    def _update_growth_and_stages(
        self,
        organisms: Dict[int, Organism],
        prng: PRNG,
        genealogy: GenealogyRegistry,
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Avança o desenvolvimento biológico nos 5 estágios distintos relativos ao limiar de maturidade."""
        for org in sorted(organisms.values(), key=lambda o: o.id):
            if org.reproduction_cooldown > 0:
                org.reproduction_cooldown -= 1

            if org.role == Organism.ROLE_CHILD:
                org.maturity_ticks += 1
                progress = min(1.0, org.maturity_ticks / float(self.maturity_threshold))

                old_stage = org.life_stage

                if progress >= 1.0:
                    # Estágio 5: Adulto completo e dispersão biológica natural
                    org.life_stage = Organism.STAGE_ADULT
                    if prng.random() < 0.5:
                        org.apply_role_traits(Organism.ROLE_FEMALE)
                    else:
                        org.apply_role_traits(Organism.ROLE_MALE)

                    old_fam_id = org.family_id
                    org.family_id = None
                    org.home_cluster_id = None
                    org.nest_id = None
                    org.reproduction_cooldown = 40
                    org.current_state = Organism.STATE_FORAGING

                    genealogy.update_record_stage(org.id, Organism.STAGE_ADULT, org.role)

                    events.append({
                        "type": "maturation",
                        "organism_id": org.id,
                        "name": org.name,
                        "role": org.role,
                        "clan_name": get_clan_name(old_fam_id) if old_fam_id else "Nômade",
                        "tick": tick,
                    })

                elif progress < 0.20:
                    org.life_stage = Organism.STAGE_NEWBORN
                    org.current_state = Organism.STATE_RESTING
                    org.traits.size = 3.5 + progress * 2.5
                    org.traits.max_speed = 0.0
                    org.traits.max_force = 0.0
                    org.vx = 0.0
                    org.vy = 0.0

                elif progress < 0.45:
                    org.life_stage = Organism.STAGE_DEVELOPING
                    org.current_state = Organism.STATE_WANDERING
                    org.traits.size = 3.5 + progress * 2.5
                    org.traits.max_speed = max(0.6, (1.6 + (org.genome.velocidade / 100.0) * 2.8) * 0.35)
                    org.traits.max_force = 0.08

                elif progress < 0.70:
                    org.life_stage = Organism.STAGE_JUVENILE
                    org.current_state = Organism.STATE_FORAGING
                    org.traits.size = 3.5 + progress * 2.5
                    org.traits.max_speed = max(1.2, (1.6 + (org.genome.velocidade / 100.0) * 2.8) * 0.60)
                    org.traits.max_force = 0.16

                else:
                    org.life_stage = Organism.STAGE_INDEPENDENT
                    org.current_state = Organism.STATE_FORAGING
                    org.traits.size = 3.5 + progress * 2.5
                    org.traits.max_speed = max(1.5, (1.6 + (org.genome.velocidade / 100.0) * 2.8) * 0.85)
                    org.traits.max_force = 0.22

                if org.life_stage != old_stage:
                    genealogy.update_record_stage(org.id, org.life_stage)

    def _form_and_maintain_families(
        self,
        organisms: Dict[int, Organism],
        food_clusters: List[Tuple[float, float]],
        next_family_id_fn,
        genealogy: GenealogyRegistry,
        prng: PRNG,
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Formação de novas famílias, reinvindicação de centros e cortejo em campo."""
        r2 = self.cluster_radius * self.cluster_radius

        for c_idx, (cx, cy) in enumerate(food_clusters):
            occupants: List[Organism] = []
            for org in organisms.values():
                if not org.alive:
                    continue
                dx = org.x - cx
                dy = org.y - cy
                if dx * dx + dy * dy <= r2:
                    occupants.append(org)

            owner_fam_id = self.cluster_homes.get(c_idx)
            owner_family = self.families.get(owner_fam_id) if owner_fam_id else None

            if owner_family and owner_family.is_active:
                # Viuvez: fêmea viúva acolhe macho solteiro
                if owner_family.patriarch_id is None:
                    eligible_males = [
                        o for o in occupants
                        if o.role == Organism.ROLE_MALE and o.family_id is None
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]
                    if eligible_males:
                        new_patriarch = sorted(eligible_males, key=lambda o: -o.energy)[0]
                        new_patriarch.family_id = owner_family.id
                        new_patriarch.home_cluster_id = c_idx
                        new_patriarch.reproduction_cooldown = 30
                        owner_family.patriarch_id = new_patriarch.id
                        if owner_family.matriarch_id:
                            new_patriarch.partner_id = owner_family.matriarch_id
                            matriarch = organisms.get(owner_family.matriarch_id)
                            if matriarch:
                                matriarch.partner_id = new_patriarch.id
                                matriarch.mourning_ticks = 0
                        events.append({
                            "type": "patriarch_joined",
                            "clan_name": owner_family.clan_name,
                            "macho_name": new_patriarch.name,
                            "cluster_id": c_idx,
                            "tick": tick,
                        })

                # Viuvez: macho viúvo acolhe fêmea solteira
                elif owner_family.matriarch_id is None:
                    eligible_females = [
                        o for o in occupants
                        if o.role == Organism.ROLE_FEMALE and o.family_id is None
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]
                    if eligible_females:
                        new_matriarch = sorted(eligible_females, key=lambda o: -o.energy)[0]
                        new_matriarch.family_id = owner_family.id
                        new_matriarch.home_cluster_id = c_idx
                        new_matriarch.reproduction_cooldown = 30
                        owner_family.matriarch_id = new_matriarch.id
                        if owner_family.patriarch_id:
                            new_matriarch.partner_id = owner_family.patriarch_id
                            patriarch = organisms.get(owner_family.patriarch_id)
                            if patriarch:
                                patriarch.partner_id = new_matriarch.id
                                patriarch.mourning_ticks = 0
                        events.append({
                            "type": "matriarch_joined",
                            "clan_name": owner_family.clan_name,
                            "female_name": new_matriarch.name,
                            "cluster_id": c_idx,
                            "tick": tick,
                        })

            else:
                # Centro Livre: Macho + Fêmea bem alimentados fundam novo Clã e Ninho
                unattached_males = sorted(
                    [
                        o for o in occupants
                        if o.role == Organism.ROLE_MALE and o.family_id is None
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ],
                    key=lambda o: o.id,
                )
                unattached_females = sorted(
                    [
                        o for o in occupants
                        if o.role == Organism.ROLE_FEMALE and o.family_id is None
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ],
                    key=lambda o: o.id,
                )

                if unattached_males and unattached_females:
                    male = unattached_males[0]
                    female = unattached_females[0]

                    new_fam_id = next_family_id_fn()
                    clan_name = get_clan_name(new_fam_id)

                    # Cria Ninho Familiar
                    nest_id = self._next_nest_id()
                    nest = Nest(
                        id=nest_id,
                        family_id=new_fam_id,
                        x=cx,
                        y=cy,
                        materials=30.0,
                        food_storage=15.0,
                        created_tick=tick,
                        is_active=True,
                    )
                    self.nests[nest_id] = nest

                    family = Family(
                        id=new_fam_id,
                        clan_name=clan_name,
                        home_cluster_id=c_idx,
                        patriarch_id=male.id,
                        matriarch_id=female.id,
                        nest_id=nest_id,
                        founded_tick=tick,
                        is_active=True,
                    )
                    self.families[new_fam_id] = family
                    self.cluster_homes[c_idx] = new_fam_id

                    male.family_id = new_fam_id
                    female.family_id = new_fam_id
                    male.home_cluster_id = c_idx
                    female.home_cluster_id = c_idx
                    male.nest_id = nest_id
                    female.nest_id = nest_id
                    male.partner_id = female.id
                    female.partner_id = male.id
                    male.partner_bond_tick = tick
                    female.partner_bond_tick = tick
                    male.reproduction_cooldown = 25
                    female.reproduction_cooldown = 25

                    if getattr(male, "memory", None):
                        male.memory.safe_haven = (cx, cy)
                    if getattr(female, "memory", None):
                        female.memory.safe_haven = (cx, cy)

                    genealogy.register_pair_bond(male.id, female.id, tick)

                    events.append({
                        "type": "family_founded",
                        "family_id": new_fam_id,
                        "clan_name": clan_name,
                        "male_name": male.name,
                        "female_name": female.name,
                        "cluster_id": c_idx,
                        "tick": tick,
                    })
                    events.append({
                        "type": "nest_created",
                        "clan_name": clan_name,
                        "nest_id": nest_id,
                        "x": nest.x,
                        "y": nest.y,
                        "tick": tick,
                    })

    def _food_conditioned_reproduction(
        self,
        all_organisms: Dict[int, Organism],
        prng: PRNG,
        next_entity_id_fn,
        genealogy: GenealogyRegistry,
        pop_averages: Dict[str, float],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> List[Organism]:
        """Reprodução condicionada à disponibilidade real de recursos e descanso parental."""
        newborns: List[Organism] = []

        for family in sorted(self.families.values(), key=lambda f: f.id):
            if not family.is_active or family.patriarch_id is None or family.matriarch_id is None:
                continue

            male = all_organisms.get(family.patriarch_id)
            female = all_organisms.get(family.matriarch_id)

            if male is None or female is None or not male.alive or not female.alive:
                continue

            # Ambos devem manter vínculo mútuo e cumprir o descanso metabólico
            if male.partner_id is not None and female.partner_id is not None:
                if male.partner_id != female.id or female.partner_id != male.id:
                    continue
            else:
                male.partner_id = female.id
                female.partner_id = male.id
                male.partner_bond_tick = tick
                female.partner_bond_tick = tick

            if male.reproduction_cooldown > 0 or female.reproduction_cooldown > 0:
                continue

            # Avaliação de Recursos Reais:
            if male.energy < self.energy_reproduce or female.energy < self.energy_reproduce:
                continue

            # Verificação de segurança e filhotes dependentes
            nest = self.nests.get(family.nest_id) if family.nest_id else None
            dependent_pups = [
                cid for cid in family.children_ids
                if cid in all_organisms and all_organisms[cid].alive and all_organisms[cid].life_stage in [
                    Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING, Organism.STAGE_JUVENILE
                ]
            ]
            if len(dependent_pups) >= 2 and female.energy < (self.energy_reproduce + 12.0):
                continue

            dist_partners = math.hypot(female.x - male.x, female.y - male.y)
            if dist_partners <= 85.0:
                child_id = next_entity_id_fn()
                child_gen = max(female.generation, male.generation) + 1

                # Cálculo de parentesco e endogamia entre os parceiros reprodutivos
                kinship = genealogy.calculate_kinship(male.id, female.id)
                inbreeding_coef = kinship / 2.0

                # Recombinação genética bialélica mendeliana com segregação independente, mutações e cálculo de endogamia
                child_genotype, mutations, genetic_history = GeneticsEngine.recombine_genotypes(
                    male.genotype,
                    female.genotype,
                    inbreeding_coefficient=inbreeding_coef,
                    pop_averages=pop_averages,
                    prng=prng,
                )
                child_personality, pers_mutations = GeneticsEngine.recombine_personality(
                    getattr(male, "personality", AnimalPersonality()),
                    getattr(female, "personality", AnimalPersonality()),
                    prng,
                )
                all_mutations = mutations + pers_mutations

                child_name = GeneticsEngine.generate_name(child_id, child_gen, child_id)

                birth_x = nest.x + prng.uniform(-3.0, 3.0) if nest else (female.x + male.x) / 2.0
                birth_y = nest.y + prng.uniform(-3.0, 3.0) if nest else (female.y + male.y) / 2.0

                child = Organism(
                    id=child_id,
                    x=birth_x,
                    y=birth_y,
                    name=child_name,
                    vx=0.0,
                    vy=0.0,
                    energy=50.0,
                    saude=child_genotype.max_saude,
                    age=0,
                    genome=child_genotype,
                    genotype=child_genotype,
                    personality=child_personality,
                    generation=child_gen,
                    father_id=male.id,
                    mother_id=female.id,
                    parent_id=female.id,
                    role=Organism.ROLE_CHILD,
                    sex="F" if prng.random() < 0.5 else "M",
                    life_stage=Organism.STAGE_NEWBORN,
                    family_id=family.id,
                    home_cluster_id=family.home_cluster_id,
                    nest_id=family.nest_id,
                    maturity_ticks=0,
                    reproduction_cooldown=self.cooldown_ticks,
                    children_ids=[],
                    mutations=all_mutations,
                    genetic_history=genetic_history,
                    current_state=Organism.STATE_RESTING,
                )

                family.children_ids.append(child_id)
                male.children_ids.append(child_id)
                female.children_ids.append(child_id)

                # Registro histórico na árvore genealógica perpétua
                genealogy.register_birth(
                    organism_id=child_id,
                    name=child_name,
                    role=Organism.ROLE_CHILD,
                    generation=child_gen,
                    birth_tick=tick,
                    father_id=male.id,
                    mother_id=female.id,
                    family_id=family.id,
                    genome=child_genotype,
                    personality=child_personality,
                    sex=child.sex,
                    life_stage=child.life_stage,
                    mutations=all_mutations,
                    genetic_history=genetic_history,
                    inbreeding_coefficient=inbreeding_coef,
                    lineage_id=child_genotype.lineage_id,
                    lineage_name=child_genotype.lineage_name,
                )

                # Compensação biológica: maior fertilidade demanda maior custo energético da fêmea e do macho
                fert_f = getattr(female.phenotype, "fertilidade", 1.0)
                fert_m = getattr(male.phenotype, "fertilidade", 1.0)
                female.energy -= 20.0 * (0.8 + 0.4 * fert_f)
                male.energy -= 15.0 * (0.8 + 0.4 * fert_m)
                if nest and nest.food_storage >= 8.0:
                    nest.consume_food(8.0)

                female.reproduction_cooldown = int(self.cooldown_ticks / max(0.5, fert_f))
                male.reproduction_cooldown = int(self.cooldown_ticks / max(0.5, fert_m))

                newborns.append(child)
                events.append({
                    "type": "birth",
                    "child_id": child_id,
                    "child_name": child_name,
                    "clan_name": family.clan_name,
                    "family_id": family.id,
                    "gen": child_gen,
                    "x": round(birth_x, 1),
                    "y": round(birth_y, 1),
                    "tick": tick,
                })

        return newborns

    def _parental_care_and_food_delivery(
        self,
        organisms: Dict[int, Organism],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Pai transporta recursos para o ninho; mãe abriga e alimenta filhotes recém-nascidos."""
        for family in self.families.values():
            if not family.is_active:
                continue

            nest = self.nests.get(family.nest_id) if family.nest_id else None
            patriarch = organisms.get(family.patriarch_id) if family.patriarch_id else None
            matriarch = organisms.get(family.matriarch_id) if family.matriarch_id else None

            # 1. Comportamento do Pai: Transporte de Comida para o Ninho
            if patriarch and patriarch.alive and nest:
                dist_p_to_nest = math.hypot(patriarch.x - nest.x, patriarch.y - nest.y)

                if patriarch.energy >= 70.0 and patriarch.carried_food < 20.0:
                    patriarch.carried_food = min(25.0, patriarch.carried_food + 0.35)

                if patriarch.carried_food >= 12.0:
                    patriarch.current_state = Organism.STATE_DELIVERING_FOOD
                    if dist_p_to_nest > 1e-4:
                        pull = 0.25
                        patriarch.vx += ((nest.x - patriarch.x) / dist_p_to_nest) * pull
                        patriarch.vy += ((nest.y - patriarch.y) / dist_p_to_nest) * pull

                if dist_p_to_nest <= 30.0 and patriarch.carried_food > 0.0:
                    nest.add_food(patriarch.carried_food)
                    nest.add_materials(0.40)
                    patriarch.carried_food = 0.0
                    patriarch.current_state = Organism.STATE_DEFENDING

            # 2. Comportamento da Mãe: Abrigo e Nutrição no Ninho
            if matriarch and matriarch.alive and nest:
                dist_m_to_nest = math.hypot(matriarch.x - nest.x, matriarch.y - nest.y)

                if matriarch.energy >= 50.0:
                    matriarch.current_state = Organism.STATE_NURTURING
                    if dist_m_to_nest > 25.0:
                        pull = 0.20
                        matriarch.vx += ((nest.x - matriarch.x) / dist_m_to_nest) * pull
                        matriarch.vy += ((nest.y - matriarch.y) / dist_m_to_nest) * pull
                else:
                    matriarch.current_state = Organism.STATE_FORAGING

            # 3. Filhotes: Alimentação, Amamentação e Aprendizado
            for cid in family.children_ids:
                child = organisms.get(cid)
                if child is None or not child.alive or child.role != Organism.ROLE_CHILD:
                    continue

                if child.life_stage in [Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING]:
                    if nest and nest.food_storage >= 5.0 and (child.energy < 65.0 or child.saude < child.genome.max_saude * 0.9):
                        consumed = nest.consume_food(6.0)
                        child.energy = min(100.0, child.energy + consumed * 1.5)
                        child.saude = min(child.genome.max_saude, child.saude + 5.0)
                        events.append({
                            "type": "care",
                            "parent_name": matriarch.name if matriarch else "Ninho",
                            "child_name": child.name,
                            "x": round(child.x, 1),
                            "y": round(child.y, 1),
                            "tick": tick,
                        })
                    elif matriarch and matriarch.alive and matriarch.energy >= 60.0 and child.energy < 40.0:
                        dist_m = math.hypot(matriarch.x - child.x, matriarch.y - child.y)
                        if dist_m <= 35.0:
                            transfer = 8.0
                            matriarch.energy -= transfer
                            child.energy = min(100.0, child.energy + transfer * 1.2)
                            child.saude = min(child.genome.max_saude, child.saude + 4.0)

                elif child.life_stage == Organism.STAGE_JUVENILE:
                    target_parent = matriarch if (matriarch and matriarch.alive) else patriarch
                    if target_parent and target_parent.alive:
                        dist_p = math.hypot(target_parent.x - child.x, target_parent.y - child.y)
                        if dist_p > 22.0:
                            pull = 0.16
                            child.vx += ((target_parent.x - child.x) / dist_p) * pull
                            child.vy += ((target_parent.y - child.y) / dist_p) * pull

    def _territorial_combat_and_predation(
        self,
        organisms: Dict[int, Organism],
        food_clusters: List[Tuple[float, float]],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Defesa territorial pelo Macho, proteção maternal e predação de filhotes vulneráveis."""
        for family in self.families.values():
            if not family.is_active:
                continue

            macho = organisms.get(family.patriarch_id) if family.patriarch_id else None
            matriarch = organisms.get(family.matriarch_id) if family.matriarch_id else None
            nest = self.nests.get(family.nest_id) if family.nest_id else None

            if nest:
                ref_x, ref_y = nest.x, nest.y
            elif family.home_cluster_id is not None and family.home_cluster_id < len(food_clusters):
                ref_x, ref_y = food_clusters[family.home_cluster_id]
            else:
                continue

            has_vulnerable_pups = any(
                cid in organisms and organisms[cid].alive and organisms[cid].life_stage in [
                    Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING, Organism.STAGE_JUVENILE
                ]
                for cid in family.children_ids
            )

            territory_limit = self.cluster_radius * (1.30 if has_vulnerable_pups else 1.10)

            threats: List[Tuple[Organism, float]] = []
            for other in organisms.values():
                if not other.alive or other.family_id == family.id:
                    continue

                dist_to_home = math.hypot(other.x - ref_x, other.y - ref_y)
                if dist_to_home <= territory_limit:
                    threats.append((other, dist_to_home))

            if not threats:
                if macho and macho.alive:
                    dist_m = math.hypot(macho.x - ref_x, macho.y - ref_y)
                    if dist_m > self.cluster_radius * 0.70:
                        pull = 0.16
                        macho.vx += ((ref_x - macho.x) / dist_m) * pull
                        macho.vy += ((ref_y - macho.y) / dist_m) * pull
                continue

            threats.sort(key=lambda t: t[1])
            closest_enemy, dist_enemy_home = threats[0]

            # 2. Defesa Ativa do Macho: Investe ferozmente contra a ameaça
            if macho and macho.alive:
                macho.current_state = Organism.STATE_DEFENDING
                dist_to_enemy = math.hypot(closest_enemy.x - macho.x, closest_enemy.y - macho.y)

                if dist_to_enemy > 1e-4:
                    charge_force = 0.44 + (macho.genome.velocidade / 100.0) * 0.22
                    macho.vx += ((closest_enemy.x - macho.x) / dist_to_enemy) * charge_force
                    macho.vy += ((closest_enemy.y - macho.y) / dist_to_enemy) * charge_force

                hit_range = macho.traits.size + closest_enemy.traits.size + 4.5
                if dist_to_enemy <= hit_range:
                    base_damage = (macho.genome.forca * 0.32) - (closest_enemy.genome.resistencia * 0.10)
                    damage = max(3.0, base_damage)

                    closest_enemy.saude = max(0.0, closest_enemy.saude - damage)
                    closest_enemy.energy = max(0.0, closest_enemy.energy - (damage * 0.65))

                    push_dx = closest_enemy.x - ref_x
                    push_dy = closest_enemy.y - ref_y
                    push_len = math.hypot(push_dx, push_dy)
                    pdir_x = push_dx / push_len if push_len > 1e-4 else (closest_enemy.x - macho.x) / dist_to_enemy
                    pdir_y = push_dy / push_len if push_len > 1e-4 else (closest_enemy.y - macho.y) / dist_to_enemy

                    repel = 3.6 + (macho.genome.forca / 100.0) * 1.6
                    closest_enemy.vx = pdir_x * repel
                    closest_enemy.vy = pdir_y * repel
                    closest_enemy.wander_angle = math.atan2(pdir_y, pdir_x)

                    if getattr(closest_enemy, "memory", None):
                        closest_enemy.memory.add_danger_zone(macho.x, macho.y, tick)
                    macho.energy = max(5.0, macho.energy - 0.25)

                    events.append({
                        "type": "combat",
                        "macho_name": macho.name,
                        "target_name": closest_enemy.name,
                        "damage": round(damage, 1),
                        "x": round(closest_enemy.x, 1),
                        "y": round(closest_enemy.y, 1),
                        "tick": tick,
                    })

                    if closest_enemy.saude < (closest_enemy.genome.max_saude * 0.40) and closest_enemy.alive:
                        closest_enemy.current_state = Organism.STATE_FLEEING
                        closest_enemy.vx = pdir_x * (closest_enemy.genome.velocidade * 1.4)
                        closest_enemy.vy = pdir_y * (closest_enemy.genome.velocidade * 1.4)
                        events.append({
                            "type": "flee",
                            "organism_name": closest_enemy.name,
                            "macho_name": macho.name,
                            "tick": tick,
                        })

            # 3. Predação de Filhotes Vulneráveis se o Macho estiver distante
            if has_vulnerable_pups and (macho is None or math.hypot(macho.x - closest_enemy.x, macho.y - closest_enemy.y) > 65.0):
                agress = getattr(closest_enemy.personality, "agressividade", 0.5) if hasattr(closest_enemy, "personality") else 0.5
                is_hungry_or_predator = (closest_enemy.energy < 35.0) or (agress >= 0.65)
                if is_hungry_or_predator:
                    closest_enemy.current_state = Organism.STATE_HUNTING

                    target_pup = None
                    min_pup_dist = float("inf")
                    for cid in family.children_ids:
                        pup = organisms.get(cid)
                        if pup and pup.alive and pup.life_stage in [Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING]:
                            pd = math.hypot(pup.x - closest_enemy.x, pup.y - closest_enemy.y)
                            if pd < min_pup_dist:
                                min_pup_dist = pd
                                target_pup = pup

                    if target_pup is not None:
                        if matriarch and matriarch.alive and math.hypot(matriarch.x - target_pup.x, matriarch.y - target_pup.y) <= 40.0:
                            matriarch.current_state = Organism.STATE_DEFENDING
                            matriarch_dmg = max(2.0, matriarch.genome.forca * 0.22)
                            closest_enemy.saude = max(0.0, closest_enemy.saude - matriarch_dmg)
                            matriarch.saude = max(0.0, matriarch.saude - 2.0)
                            events.append({
                                "type": "mother_defense",
                                "mother_name": matriarch.name,
                                "predator_name": closest_enemy.name,
                                "pup_name": target_pup.name,
                                "tick": tick,
                            })
                        else:
                            if min_pup_dist <= (closest_enemy.traits.size + target_pup.traits.size + 4.0):
                                target_pup.saude -= 18.0
                                if target_pup.saude <= 0.0:
                                    target_pup.alive = False
                                    target_pup.cause_of_death = "Predação"
                                    closest_enemy.energy = min(100.0, closest_enemy.energy + 35.0)
                                    events.append({
                                        "type": "predation_kill",
                                        "predator_name": closest_enemy.name,
                                        "pup_name": target_pup.name,
                                        "clan_name": family.clan_name,
                                        "tick": tick,
                                    })
                                else:
                                    events.append({
                                        "type": "predation_attempt",
                                        "predator_name": closest_enemy.name,
                                        "pup_name": target_pup.name,
                                        "tick": tick,
                                    })
