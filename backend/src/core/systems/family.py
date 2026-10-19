"""Sistema de dinâmica familiar completo, vínculos permanentes, ninhos, criação parental e combate territorial."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from ..entities.organism import Organism, AnimalMemory
from ..entities.nest import Nest
from ..entities.genetics import GeneticsEngine, AnimalGenome, AnimalPersonality, MutationRecord, VRANCO_NAME_PREFIXES
from ..entities.genealogy import GenealogyRegistry
from ..prng import PRNG

CLAN_NAMES = [
    "Clã Solaris", "Clã Apex", "Clã Ignis", "Clã Sylva", "Clã Terra",
    "Clã Umbra", "Clã Astra", "Clã Zephyr", "Clã Boreas", "Clã Titan",
    "Clã Vulcan", "Clã Orion", "Clã Chronos", "Clã Fenrir", "Clã Chimera"
]


def get_clan_name(family_id: int, species: str = Organism.SPECIES_PREDATOR) -> str:
    """Retorna o nome cerimonial do clã familiar baseado no ID da família e na espécie."""
    if species == Organism.SPECIES_VRANCO:
        return f"Tribo Vranco {VRANCO_NAME_PREFIXES[(family_id - 1) % len(VRANCO_NAME_PREFIXES)]}"
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
        vranco_energy_reproduce: float = 45.0,
        vranco_reproduction_cooldown: int = 35,
        vranco_carrying_capacity: int = 70,
    ) -> None:
        self.cluster_radius = cluster_radius
        self.energy_form_family = energy_threshold_form_family
        self.energy_reproduce = energy_threshold_reproduce
        self.maturity_threshold = maturity_threshold
        self.cooldown_ticks = reproduction_cooldown
        self.vranco_energy_reproduce = vranco_energy_reproduce
        self.vranco_cooldown_ticks = vranco_reproduction_cooldown
        self.vranco_carrying_capacity = vranco_carrying_capacity
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
        season_reproduction_factor: float = 1.0,
    ) -> Tuple[List[Organism], List[Dict[str, Any]]]:
        """Executa a lógica social, cortejo, ninhos, cuidado parental, combate e predação por tick."""
        events: List[Dict[str, Any]] = []

        # 1. Sincroniza estado das famílias, vínculos, luto por parceiros e territórios
        self._sync_families_and_partners(organisms, food_clusters, genealogy, events, tick)

        # 2. Atualiza os 5 estágios de desenvolvimento dos filhotes e dispersão de novos adultos
        self._update_growth_and_stages(organisms, prng, genealogy, events, tick)

        # 3. Formação de famílias, cortejo e construção de ninhos
        self._form_and_maintain_families(organisms, food_clusters, next_family_id_fn, genealogy, prng, events, tick)

        # 4a. Reprodução condicionada de Predadores (vínculo permanente de casal e ninho)
        predator_newborns = self._food_conditioned_reproduction(
            organisms,
            prng,
            next_entity_id_fn,
            genealogy,
            pop_averages,
            events,
            tick,
            season_reproduction_factor=season_reproduction_factor,
        )

        # 4b. Reprodução flexível sem parceiro fixo dos Vrancos (machos e fêmeas adultos elegíveis)
        vranco_newborns = self._reproduce_vrancos_flexible(
            organisms,
            prng,
            next_entity_id_fn,
            genealogy,
            pop_averages,
            events,
            tick,
            season_reproduction_factor=season_reproduction_factor,
        )

        newborns = predator_newborns + vranco_newborns

        # 5. Cuidado parental: Predadores (ninho e pais) e Vrancos (cuidado comunitário/aloparental)
        self._parental_care_and_food_delivery(organisms, events, tick)
        self._vranco_cooperative_pup_care(organisms, genealogy, events, tick)

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

            if org.partner_id is not None and org.species == Organism.SPECIES_PREDATOR:
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

            # Sincroniza vínculos entre patriarca e matriarca (exclusivo para Predadores)
            if patriarch and matriarch:
                sp = getattr(patriarch, "species", Organism.SPECIES_PREDATOR)
                if sp == Organism.SPECIES_PREDATOR:
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
                owner_sp = getattr(organisms.get(owner_family.matriarch_id or owner_family.patriarch_id or -1), "species", Organism.SPECIES_PREDATOR)
                # Viuvez: fêmea viúva acolhe macho solteiro da mesma espécie
                if owner_family.patriarch_id is None:
                    eligible_males = [
                        o for o in occupants
                        if o.role == Organism.ROLE_MALE and o.family_id is None
                        and o.species == owner_sp
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]
                    if eligible_males:
                        matriarch = organisms.get(owner_family.matriarch_id) if owner_family.matriarch_id else None
                        def male_compatibility(m: Organism) -> float:
                            rel = matriarch.relationships.get(m.id) if matriarch and hasattr(matriarch, "relationships") else None
                            if rel and (rel.hostility > 0.65 or rel.trust < -0.40):
                                return -999.0
                            soc = getattr(m.personality, "sociabilidade", 0.5)
                            rel_bonus = (rel.affinity * 0.5 + rel.trust * 0.5) if rel else 0.5
                            return (m.energy * 0.4) + (rel_bonus * 30.0) + (soc * 20.0)

                        compatible_males = [m for m in eligible_males if male_compatibility(m) > -500.0]
                        new_patriarch = max(compatible_males, key=male_compatibility) if compatible_males else sorted(eligible_males, key=lambda o: -o.energy)[0]
                        new_patriarch.family_id = owner_family.id
                        new_patriarch.home_cluster_id = c_idx
                        new_patriarch.reproduction_cooldown = 30
                        owner_family.patriarch_id = new_patriarch.id
                        if owner_sp == Organism.SPECIES_PREDATOR:
                            if owner_family.matriarch_id:
                                new_patriarch.partner_id = owner_family.matriarch_id
                                if matriarch:
                                    matriarch.partner_id = new_patriarch.id
                                    matriarch.mourning_ticks = 0
                                    new_patriarch.update_social_interaction(matriarch.id, "COOPERATION", intensity=0.8, tick=tick, target_name=matriarch.name, target_species=matriarch.species)
                                    matriarch.update_social_interaction(new_patriarch.id, "COOPERATION", intensity=0.8, tick=tick, target_name=new_patriarch.name, target_species=new_patriarch.species)
                        events.append({
                            "type": "patriarch_joined",
                            "clan_name": owner_family.clan_name,
                            "macho_name": new_patriarch.name,
                            "cluster_id": c_idx,
                            "tick": tick,
                        })

                # Viuvez: macho viúvo acolhe fêmea solteira da mesma espécie
                elif owner_family.matriarch_id is None:
                    eligible_females = [
                        o for o in occupants
                        if o.role == Organism.ROLE_FEMALE and o.family_id is None
                        and o.species == owner_sp
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]
                    if eligible_females:
                        patriarch = organisms.get(owner_family.patriarch_id) if owner_family.patriarch_id else None
                        def female_compatibility(f: Organism) -> float:
                            rel = patriarch.relationships.get(f.id) if patriarch and hasattr(patriarch, "relationships") else None
                            if rel and (rel.hostility > 0.65 or rel.trust < -0.40):
                                return -999.0
                            soc = getattr(f.personality, "sociabilidade", 0.5)
                            rel_bonus = (rel.affinity * 0.5 + rel.trust * 0.5) if rel else 0.5
                            return (f.energy * 0.4) + (rel_bonus * 30.0) + (soc * 20.0)

                        compatible_females = [f for f in eligible_females if female_compatibility(f) > -500.0]
                        new_matriarch = max(compatible_females, key=female_compatibility) if compatible_females else sorted(eligible_females, key=lambda o: -o.energy)[0]
                        new_matriarch.family_id = owner_family.id
                        new_matriarch.home_cluster_id = c_idx
                        new_matriarch.reproduction_cooldown = 30
                        owner_family.matriarch_id = new_matriarch.id
                        if owner_sp == Organism.SPECIES_PREDATOR:
                            if owner_family.patriarch_id:
                                new_matriarch.partner_id = owner_family.patriarch_id
                                if patriarch:
                                    patriarch.partner_id = new_matriarch.id
                                    patriarch.mourning_ticks = 0
                                    new_matriarch.update_social_interaction(patriarch.id, "COOPERATION", intensity=0.8, tick=tick, target_name=patriarch.name, target_species=patriarch.species)
                                    patriarch.update_social_interaction(new_matriarch.id, "COOPERATION", intensity=0.8, tick=tick, target_name=new_matriarch.name, target_species=new_matriarch.species)
                        events.append({
                            "type": "matriarch_joined",
                            "clan_name": owner_family.clan_name,
                            "female_name": new_matriarch.name,
                            "cluster_id": c_idx,
                            "tick": tick,
                        })

            else:
                # Centro Livre: Macho + Fêmea da mesma espécie fundam novo Clã/Tribo e Ninho
                for target_species in (Organism.SPECIES_PREDATOR, Organism.SPECIES_VRANCO):
                    candidates_m = [
                        o for o in occupants
                        if o.role == Organism.ROLE_MALE and o.family_id is None
                        and o.species == target_species
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]
                    candidates_f = [
                        o for o in occupants
                        if o.role == Organism.ROLE_FEMALE and o.family_id is None
                        and o.species == target_species
                        and o.partner_id is None and getattr(o, "clan_role", None) not in ("ALPHA", "BETA")
                        and o.energy >= self.energy_form_family and o.mourning_ticks == 0
                    ]

                    if candidates_m and candidates_f:
                        # Seleção de fundadores baseada em compatibilidade social, ausência de hostilidade e sociabilidade
                        best_pair = None
                        best_score = -999.0
                        for cand_m in candidates_m:
                            for cand_f in candidates_f:
                                rel_mf = cand_m.relationships.get(cand_f.id) if hasattr(cand_m, "relationships") else None
                                rel_fm = cand_f.relationships.get(cand_m.id) if hasattr(cand_f, "relationships") else None
                                if (rel_mf and (rel_mf.hostility > 0.60 or rel_mf.trust < -0.30)) or (rel_fm and (rel_fm.hostility > 0.60 or rel_fm.trust < -0.30)):
                                    continue
                                kin = genealogy.calculate_kinship(cand_m.id, cand_f.id)
                                score = (
                                    (cand_m.energy + cand_f.energy) * 0.2
                                    + (getattr(cand_m.personality, "sociabilidade", 0.5) + getattr(cand_f.personality, "sociabilidade", 0.5)) * 15.0
                                    - kin * 40.0
                                )
                                if score > best_score:
                                    best_score = score
                                    best_pair = (cand_m, cand_f)

                        if best_pair:
                            male, female = best_pair
                        else:
                            male = sorted(candidates_m, key=lambda o: o.id)[0]
                            female = sorted(candidates_f, key=lambda o: o.id)[0]

                        new_fam_id = next_family_id_fn()
                        clan_name = get_clan_name(new_fam_id, target_species)

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

                        if target_species == Organism.SPECIES_PREDATOR:
                            male.partner_id = female.id
                            female.partner_id = male.id
                            male.partner_bond_tick = tick
                            female.partner_bond_tick = tick
                            genealogy.register_pair_bond(male.id, female.id, tick)
                            male.update_social_interaction(female.id, "COOPERATION", intensity=0.9, tick=tick, target_name=female.name, target_species=female.species)
                            female.update_social_interaction(male.id, "COOPERATION", intensity=0.9, tick=tick, target_name=male.name, target_species=male.species)
                        else:
                            # Vrancos cooperam comunitariamente sem formar casal fixo ou monogamia
                            male.partner_id = None
                            female.partner_id = None
                            male.update_social_interaction(female.id, "COOPERATION", intensity=0.6, tick=tick, target_name=female.name, target_species=female.species)
                            female.update_social_interaction(male.id, "COOPERATION", intensity=0.6, tick=tick, target_name=male.name, target_species=male.species)

                        male.reproduction_cooldown = 25
                        female.reproduction_cooldown = 25

                        if getattr(male, "memory", None):
                            male.memory.safe_haven = (cx, cy)
                        if getattr(female, "memory", None):
                            female.memory.safe_haven = (cx, cy)

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
                        break

    def _food_conditioned_reproduction(
        self,
        all_organisms: Dict[int, Organism],
        prng: PRNG,
        next_entity_id_fn,
        genealogy: GenealogyRegistry,
        pop_averages: Dict[str, float],
        events: List[Dict[str, Any]],
        tick: int,
        season_reproduction_factor: float = 1.0,
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

            # Exclusividade da reprodução por casal e ninho para Predadores
            if getattr(male, "species", Organism.SPECIES_PREDATOR) != Organism.SPECIES_PREDATOR or getattr(female, "species", Organism.SPECIES_PREDATOR) != Organism.SPECIES_PREDATOR:
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

            # Avaliação de Recursos Reais e Custo Sazonal:
            req_energy = self.energy_reproduce * season_reproduction_factor
            if male.energy < req_energy or female.energy < req_energy:
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

            # Bloqueia reprodução caso haja hostilidade extrema acumulada entre o casal
            rel_mf = male.relationships.get(female.id) if hasattr(male, "relationships") else None
            rel_fm = female.relationships.get(male.id) if hasattr(female, "relationships") else None
            if (rel_mf and rel_mf.hostility > 0.70) or (rel_fm and rel_fm.hostility > 0.70):
                continue

            dist_partners = math.hypot(female.x - male.x, female.y - male.y)
            if dist_partners <= 85.0:
                child_id = next_entity_id_fn()
                child_gen = max(female.generation, male.generation) + 1
                is_vranco_child = (female.species == Organism.SPECIES_VRANCO)

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

                child_name = GeneticsEngine.generate_name(child_id, child_gen, child_id, is_vranco=is_vranco_child)

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
                    saude=child_genotype.max_saude * (0.60 if is_vranco_child else 1.0),
                    age=0,
                    species=female.species,
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
                male.update_social_interaction(female.id, "COOPERATION", intensity=0.85, tick=tick, target_name=female.name, target_species=female.species)
                female.update_social_interaction(male.id, "COOPERATION", intensity=0.85, tick=tick, target_name=male.name, target_species=male.species)
                child.update_social_interaction(female.id, "HELP_RECEIVED", intensity=0.9, tick=tick, target_name=female.name, target_species=female.species)
                child.update_social_interaction(male.id, "HELP_RECEIVED", intensity=0.9, tick=tick, target_name=male.name, target_species=male.species)
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

    def _reproduce_vrancos_flexible(
        self,
        all_organisms: Dict[int, Organism],
        prng: PRNG,
        next_entity_id_fn,
        genealogy: GenealogyRegistry,
        pop_averages: Dict[str, float],
        events: List[Dict[str, Any]],
        tick: int,
        season_reproduction_factor: float = 1.0,
    ) -> List[Organism]:
        """Reprodução sem parceiro fixo para Vrancos: machos e fêmeas adultos elegíveis reproduzem oportunisticamente."""
        newborns: List[Organism] = []

        # Contagem total de Vrancos vivos para controle de capacidade de suporte global
        live_vrancos = [o for o in all_organisms.values() if o.alive and o.species == Organism.SPECIES_VRANCO]
        total_vrancos = len(live_vrancos)

        if total_vrancos >= self.vranco_carrying_capacity:
            return newborns

        # Fêmeas adultas elegíveis: maturidade, energia, saúde e recursos alimentares comprovados
        required_vranco_energy = self.vranco_energy_reproduce * season_reproduction_factor
        eligible_females = [
            o for o in live_vrancos
            if o.role == Organism.ROLE_FEMALE
            and o.life_stage == Organism.STAGE_ADULT
            and o.reproduction_cooldown <= 0
            and o.energy >= required_vranco_energy
            and o.saude >= o.max_saude * 0.40
            and (o.food_eaten >= 1 or o.carried_food > 0.0)
        ]

        # Machos adultos elegíveis: maturidade, energia, saúde e recursos alimentares comprovados
        eligible_males = [
            o for o in live_vrancos
            if o.role == Organism.ROLE_MALE
            and o.life_stage == Organism.STAGE_ADULT
            and o.reproduction_cooldown <= 0
            and o.energy >= required_vranco_energy
            and o.saude >= o.max_saude * 0.40
            and (o.food_eaten >= 1 or o.carried_food > 0.0)
        ]

        if not eligible_females or not eligible_males:
            return newborns

        # Dicionário de machos disponíveis neste tick para evitar cópulas simultâneas infinitas
        available_males = {m.id: m for m in eligible_males}

        # Embaralha ordem das fêmeas com o PRNG determinístico para alternância justa
        females_order = list(sorted(eligible_females, key=lambda f: f.id))
        for i in range(len(females_order) - 1, 0, -1):
            j = prng.randint(0, i)
            females_order[i], females_order[j] = females_order[j], females_order[i]

        for female in females_order:
            if not available_males:
                break

            # 1. Verificação de capacidade de suporte global
            if total_vrancos + len(newborns) >= self.vranco_carrying_capacity:
                break
            if total_vrancos >= int(self.vranco_carrying_capacity * 0.75):
                throttle_prob = 1.0 - ((total_vrancos - self.vranco_carrying_capacity * 0.75) / (self.vranco_carrying_capacity * 0.25)) * 0.75
                if prng.random() > throttle_prob:
                    continue

            # 2. Verificação de densidade local (superpopulação local inibe reprodução)
            nearby_vrancos_count = sum(
                1 for v in live_vrancos
                if math.hypot(v.x - female.x, v.y - female.y) <= 80.0
            )
            if nearby_vrancos_count >= 8:
                continue

            # 3. Verificação de filhotes dependentes próximos à fêmea
            nearby_dependent_pups = sum(
                1 for v in live_vrancos
                if v.role == Organism.ROLE_CHILD
                and v.life_stage in [Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING]
                and math.hypot(v.x - female.x, v.y - female.y) <= 45.0
            )
            if nearby_dependent_pups >= 2 and female.energy < (self.vranco_energy_reproduce + 12.0):
                continue

            # 4. Machos próximos elegíveis
            males_in_range = [
                m for m in available_males.values()
                if math.hypot(m.x - female.x, m.y - female.y) <= 80.0
            ]
            if not males_in_range:
                continue

            # Seleciona parceiro: prioriza menor parentesco (evitar endogamia), afinidade social e proximidade
            def partner_score(m: Organism) -> Tuple[float, float]:
                kin = genealogy.calculate_kinship(m.id, female.id)
                d = math.hypot(m.x - female.x, m.y - female.y)
                rel = female.relationships.get(m.id) if hasattr(female, "relationships") else None
                hostility_pen = (rel.hostility * 2.0 - rel.trust) if rel else 0.0
                return (kin + hostility_pen, d)

            eligible_vranco_males = [
                m for m in males_in_range
                if not (female.relationships.get(m.id) and female.relationships[m.id].hostility > 0.65)
            ]
            if eligible_vranco_males:
                eligible_vranco_males.sort(key=partner_score)
                male = eligible_vranco_males[0]
            else:
                males_in_range.sort(key=partner_score)
                male = males_in_range[0]

            # 5. Execução da fecundação e herança genética
            child_id = next_entity_id_fn()
            child_gen = max(female.generation, male.generation) + 1

            kinship = genealogy.calculate_kinship(male.id, female.id)
            inbreeding_coef = kinship / 2.0

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
            child_name = GeneticsEngine.generate_name(child_id, child_gen, child_id, is_vranco=True)

            birth_x = max(35.0, min(1165.0, female.x + prng.uniform(-3.0, 3.0)))
            birth_y = max(35.0, min(765.0, female.y + prng.uniform(-3.0, 3.0)))

            child_fam_id = female.family_id or male.family_id
            child_home_id = female.home_cluster_id or male.home_cluster_id
            child_nest_id = female.nest_id or male.nest_id

            child = Organism(
                id=child_id,
                x=birth_x,
                y=birth_y,
                name=child_name,
                vx=0.0,
                vy=0.0,
                energy=50.0,
                saude=child_genotype.max_saude * 0.60,
                age=0,
                species=Organism.SPECIES_VRANCO,
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
                family_id=child_fam_id,
                home_cluster_id=child_home_id,
                nest_id=child_nest_id,
                maturity_ticks=0,
                reproduction_cooldown=self.vranco_cooldown_ticks,
                children_ids=[],
                mutations=all_mutations,
                genetic_history=genetic_history,
                current_state=Organism.STATE_RESTING,
            )

            # Atualiza descendência dos pais SEM impor vínculo de casal ou alterar parceiro
            male.children_ids.append(child_id)
            female.children_ids.append(child_id)
            if child_fam_id and child_fam_id in self.families:
                self.families[child_fam_id].children_ids.append(child_id)

            # Registro permanente e não-destrutivo na árvore genealógica
            genealogy.register_birth(
                organism_id=child_id,
                name=child_name,
                role=Organism.ROLE_CHILD,
                generation=child_gen,
                birth_tick=tick,
                father_id=male.id,
                mother_id=female.id,
                family_id=child_fam_id,
                genome=child_genotype,
                personality=child_personality,
                sex=child.sex,
                life_stage=child.life_stage,
                species=Organism.SPECIES_VRANCO,
                mutations=all_mutations,
                genetic_history=genetic_history,
                inbreeding_coefficient=inbreeding_coef,
                lineage_id=child_genotype.lineage_id,
                lineage_name=child_genotype.lineage_name,
            )

            # Custos metabólicos moderados e tempo de recuperação
            fert_f = getattr(female.phenotype, "fertilidade", 1.0)
            fert_m = getattr(male.phenotype, "fertilidade", 1.0)
            female.energy -= 12.0 * (0.8 + 0.4 * fert_f)
            male.energy -= 8.0 * (0.8 + 0.4 * fert_m)

            female.reproduction_cooldown = int(self.vranco_cooldown_ticks / max(0.5, fert_f))
            male.reproduction_cooldown = int(self.vranco_cooldown_ticks / max(0.5, fert_m))

            # Remove o macho da lista de disponíveis neste tick
            del available_males[male.id]

            newborns.append(child)
            female.update_social_interaction(male.id, "COOPERATION", intensity=0.75, tick=tick, target_name=male.name, target_species=male.species)
            male.update_social_interaction(female.id, "COOPERATION", intensity=0.75, tick=tick, target_name=female.name, target_species=female.species)
            child.update_social_interaction(female.id, "HELP_RECEIVED", intensity=0.9, tick=tick, target_name=female.name, target_species=female.species)
            child.update_social_interaction(male.id, "HELP_RECEIVED", intensity=0.9, tick=tick, target_name=male.name, target_species=male.species)

            events.append({
                "type": "vranco_birth",
                "child_id": child_id,
                "child_name": child_name,
                "father_id": male.id,
                "father_name": male.name,
                "mother_id": female.id,
                "mother_name": female.name,
                "gen": child_gen,
                "x": round(birth_x, 1),
                "y": round(birth_y, 1),
                "tick": tick,
            })
            events.append({
                "type": "birth",
                "child_id": child_id,
                "child_name": child_name,
                "clan_name": "Comunidade Vranco",
                "family_id": child_fam_id,
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
                            # Relações sociais: filhote recebe alimento materno
                            child.update_social_interaction(matriarch.id, "HELP_RECEIVED", intensity=0.8, tick=tick, target_name=matriarch.name, target_species=matriarch.species)
                            matriarch.update_social_interaction(child.id, "HELP_GIVEN", intensity=0.7, tick=tick, target_name=child.name, target_species=child.species)
                            if getattr(child, "memory", None):
                                child.memory.add_episode(
                                    event_type="RECEIVED_HELP",
                                    description=f"Recebeu alimento de {matriarch.name}",
                                    tick=tick,
                                    x=child.x,
                                    y=child.y,
                                    intensity=0.8,
                                    relevance=0.85,
                                    involved_id=matriarch.id,
                                    involved_name=matriarch.name,
                                )
                            if getattr(matriarch, "memory", None):
                                matriarch.memory.add_episode(
                                    event_type="GAVE_HELP",
                                    description=f"Alimentou o filhote {child.name}",
                                    tick=tick,
                                    x=child.x,
                                    y=child.y,
                                    intensity=0.6,
                                    relevance=0.7,
                                    involved_id=child.id,
                                    involved_name=child.name,
                                )

                elif child.life_stage == Organism.STAGE_JUVENILE:
                    target_parent = matriarch if (matriarch and matriarch.alive) else patriarch
                    if target_parent and target_parent.alive:
                        dist_p = math.hypot(target_parent.x - child.x, target_parent.y - child.y)
                        if dist_p > 22.0:
                            pull = 0.16
                            child.vx += ((target_parent.x - child.x) / dist_p) * pull
                            child.vy += ((target_parent.y - child.y) / dist_p) * pull

    def _vranco_cooperative_pup_care(
        self,
        organisms: Dict[int, Organism],
        genealogy: GenealogyRegistry,
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Cuidado aloparental e proteção comunitária de filhotes Vrancos por adultos próximos."""
        vrancos = [o for o in organisms.values() if o.alive and o.species == Organism.SPECIES_VRANCO]
        adults = [
            o for o in vrancos
            if o.role != Organism.ROLE_CHILD and o.life_stage == Organism.STAGE_ADULT and o.energy >= 45.0
        ]
        children = [
            o for o in vrancos
            if o.role == Organism.ROLE_CHILD
        ]

        if not adults or not children:
            return

        for child in children:
            if child.life_stage in [Organism.STAGE_NEWBORN, Organism.STAGE_DEVELOPING]:
                # Filhote necessita de cuidados se estiver com pouca energia ou machucado
                needs_care = (child.energy < 55.0) or (child.saude < child.genome.max_saude * 0.85)
                if not needs_care:
                    continue

                # Encontra adultos próximos capazes de prestar auxílio
                candidates: List[Tuple[Organism, float]] = []
                for adult in adults:
                    dist = math.hypot(adult.x - child.x, adult.y - child.y)
                    if dist <= 50.0:
                        # Cálculo da predisposição social baseada em parentesco, proximidade, energia e personalidade
                        prox_factor = max(0.0, 1.0 - (dist / 50.0))
                        energy_factor = min(1.0, max(0.0, (adult.energy - 40.0) / 60.0))

                        # Parentesco
                        if adult.id == child.mother_id:
                            kin_score = 1.0
                        elif adult.id == child.father_id:
                            kin_score = 0.85
                        else:
                            kin_score = max(0.20, genealogy.calculate_kinship(adult.id, child.id))

                        # Características individuais (sociabilidade / cooperação)
                        sociability = getattr(adult.personality, "sociabilidade", 0.5)
                        cooperativeness = getattr(adult.personality, "cooperacao", 0.5) if hasattr(adult.personality, "cooperacao") else sociability
                        trait_score = 0.4 + 0.6 * cooperativeness

                        # Pontuação ponderada
                        total_score = (
                            0.35 * kin_score +
                            0.35 * prox_factor +
                            0.15 * energy_factor +
                            0.15 * trait_score
                        )
                        candidates.append((adult, total_score))

                if candidates:
                    candidates.sort(key=lambda c: -c[1])
                    best_adult, score = candidates[0]
                    if score >= 0.38:
                        transfer = min(6.0, (best_adult.energy - 35.0) * 0.4)
                        if transfer > 1.0:
                            best_adult.energy -= transfer
                            child.energy = min(100.0, child.energy + transfer * 1.35)
                            child.saude = min(child.genome.max_saude, child.saude + 3.0)
                            best_adult.current_state = Organism.STATE_NURTURING
                            is_parent = (best_adult.id in [child.mother_id, child.father_id])
                            # Relações sociais: cuidado comunitário fortalece confiança e afinidade do filhote
                            child.update_social_interaction(best_adult.id, "HELP_RECEIVED", intensity=0.75, tick=tick, target_name=best_adult.name, target_species=best_adult.species)
                            best_adult.update_social_interaction(child.id, "HELP_GIVEN", intensity=0.6, tick=tick, target_name=child.name, target_species=child.species)
                            events.append({
                                "type": "vranco_alloparental_care",
                                "helper_id": best_adult.id,
                                "helper_name": best_adult.name,
                                "pup_id": child.id,
                                "pup_name": child.name,
                                "is_parent": is_parent,
                                "care_score": round(score, 2),
                                "x": round(child.x, 1),
                                "y": round(child.y, 1),
                                "tick": tick,
                            })
                            events.append({
                                "type": "care",
                                "parent_name": best_adult.name,
                                "child_name": child.name,
                                "x": round(child.x, 1),
                                "y": round(child.y, 1),
                                "tick": tick,
                            })
                            if getattr(child, "memory", None):
                                child.memory.add_episode(
                                    event_type="RECEIVED_HELP",
                                    description=f"Recebeu cuidados de {best_adult.name}",
                                    tick=tick,
                                    x=child.x,
                                    y=child.y,
                                    intensity=0.75,
                                    relevance=0.85,
                                    involved_id=best_adult.id,
                                    involved_name=best_adult.name,
                                )
                            if getattr(best_adult, "memory", None):
                                best_adult.memory.add_episode(
                                    event_type="GAVE_HELP",
                                    description=f"Cuidou do filhote {child.name}",
                                    tick=tick,
                                    x=child.x,
                                    y=child.y,
                                    intensity=0.55,
                                    relevance=0.7,
                                    involved_id=child.id,
                                    involved_name=child.name,
                                )

            elif child.life_stage == Organism.STAGE_JUVENILE:
                # Jovens Vrancos seguem o adulto mais próximo do grupo para aprendizado coletivo
                nearby_adults = [
                    a for a in adults
                    if math.hypot(a.x - child.x, a.y - child.y) <= 75.0
                ]
                if nearby_adults:
                    closest_adult = min(nearby_adults, key=lambda a: math.hypot(a.x - child.x, a.y - child.y))
                    dist_to_adult = math.hypot(closest_adult.x - child.x, closest_adult.y - child.y)
                    if dist_to_adult > 22.0:
                        pull = 0.15
                        child.vx += ((closest_adult.x - child.x) / dist_to_adult) * pull
                        child.vy += ((closest_adult.y - child.y) / dist_to_adult) * pull

    def _record_witness_death(
        self,
        organisms: Dict[int, Organism],
        victim: Organism,
        killer_name: Optional[str],
        tick: int,
    ) -> None:
        """Registra memórias de perda de parente e testemunho de morte para organismos próximos."""
        for other in organisms.values():
            if other.id == victim.id or not other.alive:
                continue
            if not getattr(other, "memory", None):
                continue
            dist = math.hypot(other.x - victim.x, other.y - victim.y)

            is_relative = (
                (other.family_id is not None and other.family_id == victim.family_id) or
                other.partner_id == victim.id or
                other.id in (victim.father_id, victim.mother_id) or
                victim.id in (other.father_id, other.mother_id)
            )
            if is_relative:
                other.memory.add_episode(
                    event_type="LOST_RELATIVE",
                    description=f"Perdeu {victim.name} (abatido por {killer_name or 'inimigo'})",
                    tick=tick,
                    x=victim.x,
                    y=victim.y,
                    intensity=0.95,
                    relevance=1.0,
                    involved_id=victim.id,
                    involved_name=victim.name,
                )
            elif dist <= 90.0:
                other.memory.add_episode(
                    event_type="WITNESSED_DEATH",
                    description=f"Presenciou a morte de {victim.name}",
                    tick=tick,
                    x=victim.x,
                    y=victim.y,
                    intensity=0.75,
                    relevance=0.85,
                    involved_id=victim.id,
                    involved_name=victim.name,
                )
                if getattr(other, "knowledge", None):
                    other.knowledge.record_danger(victim.x, victim.y, "KILL_SITE", danger_level=0.75, tick=tick)
                    other.knowledge.tactical_skills.improve("evasion_proficiency", 0.05)
                    other.knowledge.add_xp(1.5)

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

            fam_species = macho.species if macho else (matriarch.species if matriarch else Organism.SPECIES_PREDATOR)

            territory_limit = self.cluster_radius * (1.30 if has_vulnerable_pups else 1.10)

            threats: List[Tuple[Organism, float]] = []
            for other in organisms.values():
                if not other.alive or other.family_id == family.id:
                    continue

                # REGRA FUNDAMENTAL: Ausência de conflitos internos entre Vrancos!
                # Os Vrancos não brigam entre si por território, parceiros, força ou liderança.
                if fam_species == Organism.SPECIES_VRANCO and other.species == Organism.SPECIES_VRANCO:
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

            # -------------------------------------------------------------
            # SE A FAMÍLIA FOR DE VRANCOS: DEFESA COLETIVA (MOBBING)
            # -------------------------------------------------------------
            if fam_species == Organism.SPECIES_VRANCO:
                # O invasor é um predador ameaçando o ninho dos Vrancos
                nearby_defenders = [
                    v for v in organisms.values()
                    if v.alive and v.species == Organism.SPECIES_VRANCO
                    and getattr(v, "life_stage", None) == Organism.STAGE_ADULT
                    and math.hypot(v.x - closest_enemy.x, v.y - closest_enemy.y) <= 110.0
                ]

                # Cálculo de Força Coletiva com Retornos Decrescentes e Coordenação Tática Aprendida
                collective_power = 0.0
                for idx, v_def in enumerate(nearby_defenders, start=1):
                    dim_ret = 1.0 / math.sqrt(idx)
                    power_v = v_def.genome.forca * (v_def.energy / 100.0) * (v_def.saude / v_def.max_saude)
                    mob_skill = v_def.knowledge.tactical_skills.mobbing_coordination if getattr(v_def, "knowledge", None) else 0.15
                    collective_power += power_v * (1.0 + mob_skill * 0.45) * dim_ret

                pred_power = closest_enemy.genome.forca * (closest_enemy.energy / 100.0) * (closest_enemy.saude / closest_enemy.max_saude)

                # Se houver força coletiva expressiva (>= 4 defensores e poder > 1.15 * predador):
                if len(nearby_defenders) >= 4 and collective_power >= (pred_power * 1.15):
                    mob_damage = max(3.0, (collective_power - pred_power * 0.40) * 0.28)
                    closest_enemy.saude = max(0.0, closest_enemy.saude - mob_damage)
                    closest_enemy.energy = max(0.0, closest_enemy.energy - 10.0)

                    # Repele o predador
                    pdx = closest_enemy.x - ref_x
                    pdy = closest_enemy.y - ref_y
                    plen = math.hypot(pdx, pdy)
                    pdir_x = pdx / max(1e-4, plen)
                    pdir_y = pdy / max(1e-4, plen)
                    closest_enemy.vx = pdir_x * 4.2
                    closest_enemy.vy = pdir_y * 4.2
                    closest_enemy.current_state = Organism.STATE_FLEEING

                    # Memória e conhecimento de perigo para o predador repelido
                    if getattr(closest_enemy, "memory", None):
                        closest_enemy.memory.add_episode(
                            event_type="ATTACKED_BY",
                            description="Repelido por bando de Vrancos em defesa coletiva",
                            tick=tick,
                            x=closest_enemy.x,
                            y=closest_enemy.y,
                            intensity=0.8,
                            relevance=0.85,
                        )
                        closest_enemy.memory.add_danger_zone(ref_x, ref_y, tick)
                    if getattr(closest_enemy, "knowledge", None):
                        closest_enemy.knowledge.record_danger(ref_x, ref_y, "VRANCO_MOBBING", danger_level=0.65, tick=tick)
                        closest_enemy.knowledge.add_xp(2.0)

                    # Custos energéticos, escoriações leves e consolidação de conhecimento de defesa nos defensores
                    for v_def in nearby_defenders:
                        v_def.energy = max(5.0, v_def.energy - 2.0)
                        v_def.saude = max(1.0, v_def.saude - 0.5)
                        v_def.current_state = Organism.STATE_DEFENDING
                        # Relações sociais: hostilidade contra invasor e cooperação mútua entre defensores
                        v_def.update_social_interaction(closest_enemy.id, "ATTACK_DEALT", intensity=0.75, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                        closest_enemy.update_social_interaction(v_def.id, "ATTACK_RECEIVED", intensity=0.75, tick=tick, target_name=v_def.name, target_species=v_def.species)
                        for other_def in nearby_defenders:
                            if other_def.id != v_def.id:
                                v_def.update_social_interaction(other_def.id, "COOPERATION", intensity=0.65, tick=tick, target_name=other_def.name, target_species=other_def.species)
                        if getattr(v_def, "memory", None):
                            v_def.memory.add_episode(
                                event_type="SURVIVED_COMBAT",
                                description=f"Participou da defesa coletiva contra {closest_enemy.name}",
                                tick=tick,
                                x=v_def.x,
                                y=v_def.y,
                                intensity=0.7,
                                relevance=0.8,
                                involved_id=closest_enemy.id,
                                involved_name=closest_enemy.name,
                            )
                        if getattr(v_def, "knowledge", None):
                            v_def.knowledge.record_danger(closest_enemy.x, closest_enemy.y, "MOB_DEFENSE", danger_level=0.35, tick=tick)
                            v_def.knowledge.record_threat(closest_enemy.id, closest_enemy.name, 0.50)
                            v_def.knowledge.tactical_skills.improve("mobbing_coordination", 0.08)
                            v_def.knowledge.add_xp(3.0)

                    events.append({
                        "type": "vranco_collective_defense",
                        "clan_name": family.clan_name,
                        "predator_name": closest_enemy.name,
                        "participants_count": len(nearby_defenders),
                        "collective_power": round(collective_power, 1),
                        "damage": round(mob_damage, 1),
                        "x": round(closest_enemy.x, 1),
                        "y": round(closest_enemy.y, 1),
                        "tick": tick,
                    })

                    if closest_enemy.saude <= 0.0:
                        closest_enemy.alive = False
                        closest_enemy.cause_of_death = "Defesa Coletiva dos Vrancos"
                        self._record_witness_death(organisms, closest_enemy, "Defesa dos Vrancos", tick)
                        events.append({
                            "type": "predator_defeated",
                            "predator_name": closest_enemy.name,
                            "clan_name": family.clan_name,
                            "tick": tick,
                        })
                    continue
                else:
                    # Desvantagem para os Vrancos: Grupo recua e predador pode ferir o macho ou filhote
                    for v_def in nearby_defenders:
                        v_def.current_state = Organism.STATE_FLEEING

                    dist_m = math.hypot(closest_enemy.x - macho.x, closest_enemy.y - macho.y) if macho and macho.alive else 999.0
                    hit_range = closest_enemy.traits.size + (macho.traits.size if macho else 4.0) + 4.5
                    if dist_m <= hit_range and macho and macho.alive:
                        pred_dmg = max(4.0, (closest_enemy.genome.forca * 0.35) - (macho.genome.resistencia * 0.08))
                        macho.saude = max(0.0, macho.saude - pred_dmg)
                        macho.energy = max(0.0, macho.energy - pred_dmg * 0.6)
                        # Relações sociais: agressão sofrida gera medo e hostilidade
                        macho.update_social_interaction(closest_enemy.id, "ATTACK_RECEIVED", intensity=0.85, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                        closest_enemy.update_social_interaction(macho.id, "ATTACK_DEALT", intensity=0.85, tick=tick, target_name=macho.name, target_species=macho.species)
                        if getattr(macho, "memory", None):
                            macho.memory.add_episode(
                                event_type="ATTACKED_BY",
                                description=f"Atacado pelo predador {closest_enemy.name}",
                                tick=tick,
                                x=macho.x,
                                y=macho.y,
                                intensity=0.9,
                                relevance=0.95,
                                involved_id=closest_enemy.id,
                                involved_name=closest_enemy.name,
                            )
                        if getattr(closest_enemy, "memory", None):
                            closest_enemy.memory.add_episode(
                                event_type="SURVIVED_COMBAT",
                                description=f"Confrontou {macho.name}",
                                tick=tick,
                                x=closest_enemy.x,
                                y=closest_enemy.y,
                                intensity=0.6,
                                relevance=0.7,
                                involved_id=macho.id,
                                involved_name=macho.name,
                            )
                        events.append({
                            "type": "combat",
                            "macho_name": closest_enemy.name,
                            "target_name": macho.name,
                            "damage": round(pred_dmg, 1),
                            "x": round(macho.x, 1),
                            "y": round(macho.y, 1),
                            "tick": tick,
                        })
                        if macho.saude <= 0.0:
                            macho.alive = False
                            macho.cause_of_death = "Predação"
                            closest_enemy.energy = min(120.0, closest_enemy.energy + 35.0)
                            self._record_witness_death(organisms, macho, closest_enemy.name, tick)
                            if getattr(closest_enemy, "knowledge", None):
                                closest_enemy.knowledge.record_food(macho.x, macho.y, tick)
                                closest_enemy.knowledge.tactical_skills.improve("hunting_proficiency", 0.10)
                                closest_enemy.knowledge.add_xp(5.0)
                            events.append({
                                "type": "predation_kill",
                                "predator_name": closest_enemy.name,
                                "pup_name": macho.name,
                                "clan_name": family.clan_name,
                                "tick": tick,
                            })

            # -------------------------------------------------------------
            # SE A FAMÍLIA FOR DE PREDADORES: DEFESA TERRITORIAL TRADICIONAL
            # -------------------------------------------------------------
            elif macho and macho.alive:
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

                    # Relações sociais: combate territorial gera hostilidade e rivalidade entre predadores
                    closest_enemy.update_social_interaction(macho.id, "ATTACK_RECEIVED", intensity=0.85, tick=tick, target_name=macho.name, target_species=macho.species)
                    macho.update_social_interaction(closest_enemy.id, "ATTACK_DEALT", intensity=0.85, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                    closest_enemy.update_social_interaction(macho.id, "COMPETITION", intensity=0.80, tick=tick, target_name=macho.name, target_species=macho.species)
                    macho.update_social_interaction(closest_enemy.id, "COMPETITION", intensity=0.80, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)

                    if getattr(closest_enemy, "memory", None):
                        closest_enemy.memory.add_danger_zone(macho.x, macho.y, tick)
                        closest_enemy.memory.add_episode(
                            event_type="ATTACKED_BY",
                            description=f"Atacado por {macho.name} em disputa territorial",
                            tick=tick,
                            x=closest_enemy.x,
                            y=closest_enemy.y,
                            intensity=0.85,
                            relevance=0.9,
                            involved_id=macho.id,
                            involved_name=macho.name,
                        )
                    if getattr(macho, "memory", None):
                        macho.memory.add_episode(
                            event_type="SURVIVED_COMBAT",
                            description=f"Defendeu território contra {closest_enemy.name}",
                            tick=tick,
                            x=macho.x,
                            y=macho.y,
                            intensity=0.7,
                            relevance=0.75,
                            involved_id=closest_enemy.id,
                            involved_name=closest_enemy.name,
                        )
                    if getattr(closest_enemy, "knowledge", None):
                        closest_enemy.knowledge.record_danger(macho.x, macho.y, "TERRITORIAL_COMBAT", danger_level=0.60, tick=tick)
                        closest_enemy.knowledge.record_threat(macho.id, macho.name, 0.70)
                        closest_enemy.knowledge.add_xp(1.5)
                    if getattr(macho, "knowledge", None):
                        macho.knowledge.record_threat(closest_enemy.id, closest_enemy.name, 0.50)
                        macho.knowledge.tactical_skills.improve("mobbing_coordination", 0.05)
                        macho.knowledge.add_xp(2.5)
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

                    if closest_enemy.saude <= 0.0:
                        closest_enemy.alive = False
                        closest_enemy.cause_of_death = f"Combate com {macho.name}"
                        macho.energy = min(120.0, macho.energy + 20.0)
                        self._record_witness_death(organisms, closest_enemy, macho.name, tick)
                        events.append({
                            "type": "predation_kill",
                            "predator_name": macho.name,
                            "pup_name": closest_enemy.name,
                            "clan_name": family.clan_name,
                            "tick": tick,
                        })
                    elif closest_enemy.saude < (closest_enemy.max_saude * 0.40) and closest_enemy.alive:
                        closest_enemy.current_state = Organism.STATE_FLEEING
                        closest_enemy.vx = pdir_x * (closest_enemy.genome.velocidade * 1.4)
                        closest_enemy.vy = pdir_y * (closest_enemy.genome.velocidade * 1.4)
                        if getattr(closest_enemy, "memory", None):
                            closest_enemy.memory.add_episode(
                                event_type="SURVIVED_COMBAT",
                                description=f"Sobreviveu a confronto com {macho.name}",
                                tick=tick,
                                x=closest_enemy.x,
                                y=closest_enemy.y,
                                intensity=0.75,
                                relevance=0.85,
                                involved_id=macho.id,
                                involved_name=macho.name,
                            )
                        events.append({
                            "type": "flee",
                            "organism_name": closest_enemy.name,
                            "macho_name": macho.name,
                            "tick": tick,
                        })

            # 3. Predação de Filhotes Vulneráveis se o Macho estiver distante
            # NOTA: Vrancos NUNCA predam filhotes
            if has_vulnerable_pups and closest_enemy.species == Organism.SPECIES_PREDATOR and (macho is None or math.hypot(macho.x - closest_enemy.x, macho.y - closest_enemy.y) > 65.0):
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
                        # Para Vrancos: Indivíduos próximos (mãe ou vizinhos da mesma espécie) ajudam a proteger filhote
                        helpers = [
                            v for v in organisms.values()
                            if v.alive and v.species == Organism.SPECIES_VRANCO and v.id != target_pup.id
                            and math.hypot(v.x - target_pup.x, v.y - target_pup.y) <= 45.0
                        ]
                        if helpers:
                            for h in helpers:
                                h.current_state = Organism.STATE_DEFENDING
                                h.update_social_interaction(closest_enemy.id, "ATTACK_DEALT", intensity=0.7, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                                closest_enemy.update_social_interaction(h.id, "ATTACK_RECEIVED", intensity=0.7, tick=tick, target_name=h.name, target_species=h.species)
                                target_pup.update_social_interaction(h.id, "HELP_RECEIVED", intensity=0.85, tick=tick, target_name=h.name, target_species=h.species)
                                h.update_social_interaction(target_pup.id, "HELP_GIVEN", intensity=0.65, tick=tick, target_name=target_pup.name, target_species=target_pup.species)
                                if getattr(h, "memory", None):
                                    h.memory.add_episode(
                                        event_type="SURVIVED_COMBAT",
                                        description=f"Defendeu o filhote {target_pup.name} de {closest_enemy.name}",
                                        tick=tick,
                                        x=h.x,
                                        y=h.y,
                                        intensity=0.7,
                                        relevance=0.8,
                                        involved_id=closest_enemy.id,
                                        involved_name=closest_enemy.name,
                                    )
                            if getattr(closest_enemy, "memory", None):
                                closest_enemy.memory.add_episode(
                                    event_type="ATTACKED_BY",
                                    description=f"Repelido por protetores do filhote {target_pup.name}",
                                    tick=tick,
                                    x=closest_enemy.x,
                                    y=closest_enemy.y,
                                    intensity=0.75,
                                    relevance=0.8,
                                )
                            helper_dmg = sum(h.genome.forca * 0.15 for h in helpers[:3])
                            closest_enemy.saude = max(0.0, closest_enemy.saude - helper_dmg)
                            events.append({
                                "type": "mother_defense",
                                "mother_name": helpers[0].name,
                                "predator_name": closest_enemy.name,
                                "pup_name": target_pup.name,
                                "tick": tick,
                            })
                        elif matriarch and matriarch.alive and math.hypot(matriarch.x - target_pup.x, matriarch.y - target_pup.y) <= 40.0:
                            matriarch.current_state = Organism.STATE_DEFENDING
                            matriarch_dmg = max(2.0, matriarch.genome.forca * 0.22)
                            closest_enemy.saude = max(0.0, closest_enemy.saude - matriarch_dmg)
                            matriarch.saude = max(0.0, matriarch.saude - 2.0)
                            matriarch.update_social_interaction(closest_enemy.id, "ATTACK_DEALT", intensity=0.85, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                            closest_enemy.update_social_interaction(matriarch.id, "ATTACK_RECEIVED", intensity=0.85, tick=tick, target_name=matriarch.name, target_species=matriarch.species)
                            target_pup.update_social_interaction(matriarch.id, "HELP_RECEIVED", intensity=0.9, tick=tick, target_name=matriarch.name, target_species=matriarch.species)
                            if getattr(matriarch, "memory", None):
                                matriarch.memory.add_episode(
                                    event_type="SURVIVED_COMBAT",
                                    description=f"Defendeu o filhote {target_pup.name} de {closest_enemy.name}",
                                    tick=tick,
                                    x=matriarch.x,
                                    y=matriarch.y,
                                    intensity=0.85,
                                    relevance=0.9,
                                    involved_id=closest_enemy.id,
                                    involved_name=closest_enemy.name,
                                )
                            if getattr(closest_enemy, "memory", None):
                                closest_enemy.memory.add_episode(
                                    event_type="ATTACKED_BY",
                                    description=f"Atacado pela mãe {matriarch.name}",
                                    tick=tick,
                                    x=closest_enemy.x,
                                    y=closest_enemy.y,
                                    intensity=0.8,
                                    relevance=0.85,
                                    involved_id=matriarch.id,
                                    involved_name=matriarch.name,
                                )
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
                                target_pup.update_social_interaction(closest_enemy.id, "ATTACK_RECEIVED", intensity=0.95, tick=tick, target_name=closest_enemy.name, target_species=closest_enemy.species)
                                closest_enemy.update_social_interaction(target_pup.id, "ATTACK_DEALT", intensity=0.95, tick=tick, target_name=target_pup.name, target_species=target_pup.species)
                                if getattr(target_pup, "memory", None):
                                    target_pup.memory.add_episode(
                                        event_type="ATTACKED_BY",
                                        description=f"Atacado pelo predador {closest_enemy.name}",
                                        tick=tick,
                                        x=target_pup.x,
                                        y=target_pup.y,
                                        intensity=0.95,
                                        relevance=1.0,
                                        involved_id=closest_enemy.id,
                                        involved_name=closest_enemy.name,
                                    )
                                if getattr(target_pup, "knowledge", None):
                                    target_pup.knowledge.record_danger(closest_enemy.x, closest_enemy.y, "AMBUSH", danger_level=0.85, tick=tick)
                                    target_pup.knowledge.record_threat(closest_enemy.id, closest_enemy.name, 0.85)
                                    target_pup.knowledge.tactical_skills.improve("evasion_proficiency", 0.08)
                                    target_pup.knowledge.add_xp(2.0)
                                if target_pup.saude <= 0.0:
                                    target_pup.alive = False
                                    target_pup.cause_of_death = "Predação"
                                    closest_enemy.energy = min(100.0, closest_enemy.energy + 35.0)
                                    self._record_witness_death(organisms, target_pup, closest_enemy.name, tick)
                                    if getattr(closest_enemy, "knowledge", None):
                                        closest_enemy.knowledge.record_food(target_pup.x, target_pup.y, tick)
                                        closest_enemy.knowledge.tactical_skills.improve("hunting_proficiency", 0.10)
                                        closest_enemy.knowledge.add_xp(4.0)
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

    def can_mate(self, org_a: Organism, org_b: Organism) -> bool:
        """Verifica se dois organismos podem cruzar, respeitando isolamento reprodutivo entre espécies."""
        if getattr(org_a, "species", Organism.SPECIES_PREDATOR) != getattr(org_b, "species", Organism.SPECIES_PREDATOR):
            return False
        if org_a.role == org_b.role:
            return False
        return True

    def evaluate_male_contest(self, macho_a: Organism, macho_b: Organism) -> bool:
        """Avalia se dois machos disputam liderança ou território. Vrancos NUNCA lutam entre si."""
        sp_a = getattr(macho_a, "species", Organism.SPECIES_PREDATOR)
        sp_b = getattr(macho_b, "species", Organism.SPECIES_PREDATOR)
        if sp_a == Organism.SPECIES_VRANCO or sp_b == Organism.SPECIES_VRANCO:
            return False
        # Predadores podem disputar
        return True

    def evaluate_and_execute_mobbing(self, vranco: Organism, world: Any) -> bool:
        """Avalia e executa defesa coletiva (mobbing) de Vrancos contra predadores próximos."""
        predators = [
            o for o in world.organisms.values()
            if o.alive and getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_PREDATOR
            and math.hypot(o.x - vranco.x, o.y - vranco.y) <= 120.0
        ]
        if not predators:
            return False
        closest_pred = min(predators, key=lambda p: math.hypot(p.x - vranco.x, p.y - vranco.y))

        nearby_defenders = [
            v for v in world.organisms.values()
            if v.alive and getattr(v, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO
            and getattr(v, "life_stage", None) == Organism.STAGE_ADULT
            and math.hypot(v.x - closest_pred.x, v.y - closest_pred.y) <= 110.0
        ]
        if len(nearby_defenders) < 4:
            return False

        collective_power = 0.0
        for idx, v_def in enumerate(nearby_defenders, start=1):
            dim_ret = 1.0 / math.sqrt(idx)
            power_v = v_def.genome.forca * (v_def.energy / 100.0) * (v_def.saude / v_def.max_saude)
            collective_power += power_v * dim_ret

        pred_power = closest_pred.genome.forca * (closest_pred.energy / 100.0) * (closest_pred.saude / closest_pred.max_saude)
        if collective_power >= (pred_power * 1.15):
            mob_damage = max(3.0, (collective_power - pred_power * 0.40) * 0.28)
            closest_pred.saude = max(0.0, closest_pred.saude - mob_damage)
            closest_pred.energy = max(0.0, closest_pred.energy - 10.0)

            for v_def in nearby_defenders:
                v_def.energy = max(5.0, v_def.energy - 2.0)
                v_def.saude = max(1.0, v_def.saude - 0.5)
                v_def.current_state = Organism.STATE_DEFENDING

            world.recent_events.append({
                "type": "vranco_collective_defense",
                "predator_name": closest_pred.name,
                "participants_count": len(nearby_defenders),
                "collective_power": round(collective_power, 1),
                "damage": round(mob_damage, 1),
                "tick": world.tick,
            })
            return True
        return False
