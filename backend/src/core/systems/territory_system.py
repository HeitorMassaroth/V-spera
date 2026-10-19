"""Sistema dinâmico de Territórios, Qualidade Regional, Disputas e Decisões de Migração."""

from __future__ import annotations
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from ..entities.territory import TerritoryZone
from ..entities.organism import Organism
from ..entities.food import Food
from ..entities.clan import Clan, ClanRelation, ClanSocialStage
from ..entities.nest import Nest
from ..prng import PRNG


ZONE_NAMES_CENTRAL = [
    "Oásis Centralis",
    "Platô Apex",
    "Vale Solaris",
    "Bosque Sylva",
]

ZONE_NAMES_PERIPHERAL = [
    "Periferia Setentrional",
    "Refúgio Meridional",
    "Costa Ocidental",
    "Estepes Orientais",
]


class TerritorySystem:
    """Gerencia zonas territoriais, cálculo de qualidade ecológica, migrações fundamentadas e disputas por recursos."""

    def __init__(
        self,
        world_width: float,
        world_height: float,
        food_clusters: List[Tuple[float, float]],
        prng: PRNG,
    ) -> None:
        self.width = float(world_width)
        self.height = float(world_height)
        self.prng = prng
        self.zones: Dict[int, TerritoryZone] = {}
        self._initialize_zones(food_clusters)

    def _initialize_zones(self, food_clusters: List[Tuple[float, float]]) -> None:
        """Inicializa as 8 regiões territoriais estratégicas do ecossistema."""
        zone_id = 1

        # 1. Zonas Centrais / Oásis de Recursos (baseadas nos food clusters)
        for idx, (cx, cy) in enumerate(food_clusters):
            name = ZONE_NAMES_CENTRAL[idx % len(ZONE_NAMES_CENTRAL)]
            zone = TerritoryZone(
                id=zone_id,
                name=name,
                x=cx,
                y=cy,
                radius=100.0,
                is_peripheral=False,
                base_fertility=1.20,
                current_fertility=1.20,
                carrying_capacity=22,
                safety_score=0.85,
            )
            self.zones[zone_id] = zone
            zone_id += 1

        # 2. Zonas Periféricas / Santuários nas bordas do mapa (ideais para Vrancos e nômades)
        margin = 85.0
        cx_mid = self.width / 2.0
        cy_mid = self.height / 2.0

        peripheral_coords = [
            (cx_mid, margin, ZONE_NAMES_PERIPHERAL[0]),                      # Norte
            (cx_mid, self.height - margin, ZONE_NAMES_PERIPHERAL[1]),        # Sul
            (margin, cy_mid, ZONE_NAMES_PERIPHERAL[2]),                      # Oeste
            (self.width - margin, cy_mid, ZONE_NAMES_PERIPHERAL[3]),         # Leste
        ]

        for px, py, pname in peripheral_coords:
            zone = TerritoryZone(
                id=zone_id,
                name=pname,
                x=px,
                y=py,
                radius=115.0,
                is_peripheral=True,
                base_fertility=0.85,
                current_fertility=0.85,
                carrying_capacity=18,
                safety_score=0.95,
            )
            self.zones[zone_id] = zone
            zone_id += 1

    def get_zone_at(self, x: float, y: float) -> Optional[TerritoryZone]:
        """Retorna a zona territorial que contém o ponto especificado, se houver."""
        for zone in self.zones.values():
            if zone.contains_point(x, y):
                return zone
        return None

    def get_nearest_zone(self, x: float, y: float) -> TerritoryZone:
        """Retorna a zona territorial cujo centro está mais próximo das coordenadas."""
        return min(self.zones.values(), key=lambda z: z.distance_to_point(x, y))

    def update(
        self,
        organisms: Dict[int, Organism],
        foods: Dict[int, Food],
        families: Dict[int, Any],
        nests: Dict[int, Nest],
        clans: Dict[int, Clan],
        tick: int,
        events: List[Dict[str, Any]],
    ) -> None:
        """Executa a atualização ecológica, avaliação de permanência, migrações e disputas territoriais."""

        # 1. Mapeamento espacial das entidades para as zonas e contagem ecológica
        self._map_spatial_entities_and_ecology(organisms, foods, nests, clans, tick)

        # 2. Avaliação de Permanência, Abandono de Regiões Degradadas e Migração
        self._evaluate_occupancy_and_migrations(organisms, families, clans, tick, events)

        # 3. Resolução Inteligente de Disputas Territoriais e Competição por Recursos
        self._resolve_territory_disputes(organisms, clans, tick, events)

    def _map_spatial_entities_and_ecology(
        self,
        organisms: Dict[int, Organism],
        foods: Dict[int, Food],
        nests: Dict[int, Nest],
        clans: Dict[int, Clan],
        tick: int,
    ) -> None:
        """Atualiza a presença biológica, recursos disponíveis e cálculo de qualidade de cada zona."""
        for zone in self.zones.values():
            zone.occupant_ids.clear()
            zone.food_count = 0
            zone.biomass = 0.0
            zone.predator_count = 0
            zone.vranco_count = 0
            zone.shelter_count = 0

        # Mapeia alimentos para as zonas correspondentes
        for food in foods.values():
            zone = self.get_zone_at(food.x, food.y)
            if zone:
                zone.food_count += 1
                zone.biomass += getattr(food, "energy_value", 25.0)

        # Mapeia ninhos ativos
        for nest in nests.values():
            if nest.is_active:
                zone = self.get_zone_at(nest.x, nest.y)
                if zone:
                    zone.shelter_count += 1

        # Mapeia organismos vivos
        for org in organisms.values():
            if not org.alive:
                continue

            zone = self.get_zone_at(org.x, org.y)
            if zone:
                zone.occupant_ids.add(org.id)
                if getattr(org, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO:
                    zone.vranco_count += 1
                else:
                    zone.predator_count += 1

                # Se o organismo não possuía território e permaneceu na zona: associa provisoriamente
                if org.territory_id is None and org.family_id is not None:
                    org.territory_id = zone.id

        # Mapeia controle dos Clãs estabelecidos
        for clan in clans.values():
            if clan.is_active and clan.stage == ClanSocialStage.ESTABLISHED_CLAN:
                zone = self.get_zone_at(clan.territory_x, clan.territory_y)
                if zone and (zone.controlling_clan_id is None or zone.controlling_clan_id == clan.id):
                    zone.controlling_clan_id = clan.id
                    zone.controller_type = "CLAN"
                    if zone.status != "CONTESTED":
                        zone.status = "SETTLED"

        # Atualiza qualidade ecológica e finitude dos recursos
        for zone in self.zones.values():
            zone.calculate_quality()
            zone.update_resource_ecology(tick)

    def _evaluate_occupancy_and_migrations(
        self,
        organisms: Dict[int, Organism],
        families: Dict[int, Any],
        clans: Dict[int, Clan],
        tick: int,
        events: List[Dict[str, Any]],
    ) -> None:
        """
        Avalia se clãs, famílias ou grupos devem permanecer, forragear ou abandonar uma região.
        Migrações exigem causas reais identificáveis (escassez crônica, infestação de predadores, superpopulação).
        """
        # Avaliação de abandono e migração para Clãs e Famílias a cada 35 ticks
        if tick % 35 != 0:
            return

        for zone in self.zones.values():
            if len(zone.occupant_ids) == 0:
                continue

            # Identifica as famílias e clãs presentes na zona
            present_families: Set[int] = set()
            present_clans: Set[int] = set()
            vrancos_in_zone: List[Organism] = []
            predators_in_zone: List[Organism] = []

            for oid in zone.occupant_ids:
                org = organisms.get(oid)
                if not org or not org.alive:
                    continue
                if org.family_id:
                    present_families.add(org.family_id)
                if org.clan_id:
                    present_clans.add(org.clan_id)
                if getattr(org, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO:
                    vrancos_in_zone.append(org)
                else:
                    predators_in_zone.append(org)

            # -------------------------------------------------------------
            # A. REGRAS DE MIGRAÇÃO DOS VRANCOS (Fuga da Degradação ou Predação)
            # -------------------------------------------------------------
            if vrancos_in_zone:
                # Vrancos avaliam se a zona atual tornou-se insustentável
                high_danger = (zone.predator_count >= 3 and zone.safety_score < 0.35)
                starvation = (zone.food_count <= 1 and any(v.energy < 40.0 for v in vrancos_in_zone))
                severe_overcrowding = (zone.population_density > 1.8)

                should_vrancos_migrate = (high_danger or starvation or severe_overcrowding) and (zone.quality_score < 28.0)

                if should_vrancos_migrate:
                    reason = (
                        "Infestação crítica de predadores" if high_danger
                        else ("Escassez severa de alimentos" if starvation else "Superpopulação insustentável")
                    )

                    # Busca a melhor zona de refúgio alternativa
                    candidate_zones = [
                        z for z in self.zones.values()
                        if z.id != zone.id and z.abandoned_cooldown == 0
                    ]

                    # Vrancos preferem periferia se viável; caso contrário, consideram zonas centrais
                    best_dest = None
                    best_score = -1.0
                    for c_zone in candidate_zones:
                        pref_bonus = 20.0 if c_zone.is_peripheral else 0.0
                        dist = zone.distance_to_point(c_zone.x, c_zone.y)
                        dist_penalty = min(25.0, dist * 0.03)
                        eval_score = c_zone.quality_score + pref_bonus - dist_penalty
                        if eval_score > best_score:
                            best_score = eval_score
                            best_dest = c_zone

                    if best_dest and best_dest.quality_score >= 32.0:
                        zone.status = "ABANDONED"
                        zone.abandoned_cooldown = 70
                        zone.abandoned_tick = tick
                        zone.log_event("zone_abandoned", f"Bando Vranco abandonou {zone.name} rumo a {best_dest.name} ({reason})", tick)

                        for v in vrancos_in_zone:
                            v.target_migration_zone = (best_dest.x, best_dest.y)
                            v.territory_cooldown = 90
                            v.territory_id = best_dest.id
                            if getattr(v, "memory", None):
                                v.memory.safe_haven = (best_dest.x, best_dest.y)
                                v.memory.add_danger_zone(zone.x, zone.y, tick)

                        events.append({
                            "type": "territory_migration",
                            "species": Organism.SPECIES_VRANCO,
                            "origin_zone": zone.name,
                            "dest_zone": best_dest.name,
                            "count": len(vrancos_in_zone),
                            "reason": reason,
                            "tick": tick,
                        })

            # -------------------------------------------------------------
            # B. REGRAS DE MIGRAÇÃO DOS PREDADORES E CLÃS ESTABELECIDOS
            # -------------------------------------------------------------
            if zone.controlling_clan_id and zone.controlling_clan_id in clans:
                clan = clans[zone.controlling_clan_id]
                clan_members = [
                    o for o in organisms.values()
                    if o.clan_id == clan.id and o.alive
                ]

                if clan_members:
                    avg_energy = sum(o.energy for o in clan_members) / len(clan_members)
                    clan_starvation = (clan.communal_food < 5.0 and zone.food_count <= 2 and avg_energy < 48.0)
                    depleted_territory = (zone.quality_score < 24.0 and zone.current_fertility < 0.40)

                    # Clã só abandona território com motivo grave comprovado
                    if (clan_starvation or depleted_territory) and zone.abandoned_cooldown == 0:
                        reason = "Esgotamento crônico da biomassa local" if depleted_territory else "Crise de inanição do clã"

                        # Busca novo território fértil não controlado por rivais em guerra
                        candidate_zones = [
                            z for z in self.zones.values()
                            if z.id != zone.id and z.controlling_clan_id is None
                            and z.abandoned_cooldown == 0
                        ]
                        if candidate_zones:
                            best_dest = max(candidate_zones, key=lambda z: z.quality_score - (zone.distance_to_point(z.x, z.y) * 0.02))
                            if best_dest.quality_score > (zone.quality_score + 15.0):
                                zone.status = "ABANDONED"
                                zone.abandoned_cooldown = 100
                                zone.controlling_clan_id = None
                                zone.controller_type = "NONE"
                                zone.log_event("clan_migrated", f"{clan.name} abandonou {zone.name} e migrou para {best_dest.name} ({reason})", tick)

                                clan.territory_x = best_dest.x
                                clan.territory_y = best_dest.y
                                best_dest.controlling_clan_id = clan.id
                                best_dest.controller_type = "CLAN"
                                best_dest.status = "SETTLED"

                                for member in clan_members:
                                    member.target_migration_zone = (best_dest.x, best_dest.y)
                                    member.territory_cooldown = 100
                                    member.territory_id = best_dest.id
                                    if getattr(member, "memory", None):
                                        member.memory.safe_haven = (best_dest.x, best_dest.y)

                                events.append({
                                    "type": "clan_territory_migrated",
                                    "clan_name": clan.name,
                                    "origin_zone": zone.name,
                                    "dest_zone": best_dest.name,
                                    "members_count": len(clan_members),
                                    "reason": reason,
                                    "tick": tick,
                                })

            # -------------------------------------------------------------
            # C. PREDADORES SOLITÁRIOS: ABANDONO DE ZONAS SEM PRESAS/COMIDA
            # -------------------------------------------------------------
            # Predadores sem presas nem alimento abandonam a zona vazia (sem telepatia mágica)
            solitary_predators = [
                p for p in predators_in_zone
                if p.clan_id is None and p.family_id is None and p.energy < 60.0 and p.territory_cooldown == 0
            ]
            if solitary_predators and zone.food_count == 0 and zone.vranco_count == 0:
                for p in solitary_predators:
                    # Rastreia por memória ou segue gradiente em direção à zona vizinha mais fértil
                    other_zones = [z for z in self.zones.values() if z.id != zone.id]
                    if other_zones:
                        dest = max(other_zones, key=lambda z: z.quality_score - (p.distance_to(z.x, z.y) * 0.04))
                        p.target_migration_zone = (dest.x, dest.y)
                        p.territory_cooldown = 60
                        p.territory_id = dest.id
                        zone.log_event("predator_forage_migration", f"{p.name} abandonou {zone.name} e migrou para {dest.name} em busca de presas", tick)
                        events.append({
                            "type": "predator_forage_migration",
                            "predator_id": p.id,
                            "origin_zone": zone.name,
                            "dest_zone": dest.name,
                            "tick": tick,
                        })

    def _resolve_territory_disputes(
        self,
        organisms: Dict[int, Organism],
        clans: Dict[int, Clan],
        tick: int,
        events: List[Dict[str, Any]],
    ) -> None:
        """
        Gerencia conflitos e disputas por regiões:
        1. Compara correlação de forças (número, saúde, energia, relações sociais).
        2. Permite recuo pacífico sem combate desnecessário.
        3. Fissão social por superpopulação em clãs estabelecidos.
        """
        for zone in self.zones.values():
            # Identifica clãs concorrentes com membros presentes na mesma região
            present_clan_ids: Set[int] = set()
            for oid in zone.occupant_ids:
                org = organisms.get(oid)
                if org and org.alive and org.clan_id and org.clan_id in clans:
                    present_clan_ids.add(org.clan_id)

            if len(present_clan_ids) < 2:
                if zone.status == "CONTESTED" and zone.dispute_ticks > 0:
                    zone.dispute_ticks = max(0, zone.dispute_ticks - 1)
                    if zone.dispute_ticks == 0:
                        zone.status = "SETTLED" if (zone.controlling_clan_id or zone.controlling_family_id) else "UNCLAIMED"
                continue

            # Há múltiplos clãs presentes na mesma zona: avalia diplomacia e forças
            clan_list = [clans[cid] for cid in present_clan_ids if clans[cid].is_active]
            if len(clan_list) < 2:
                continue

            c1, c2 = clan_list[0], clan_list[1]
            rel = c1.diplomacy.get(c2.id, ClanRelation.NEUTRAL)

            # Entre clãs aliados ou cooperantes: partilham pacificamente a zona
            if rel in (ClanRelation.ALLIANCE, ClanRelation.COOPERATION, ClanRelation.TRUCE):
                zone.status = "SETTLED"
                continue

            # Calcula força combativa efetiva de cada grupo na zona
            c1_members = [organisms[oid] for oid in zone.occupant_ids if organisms.get(oid) and organisms[oid].clan_id == c1.id and organisms[oid].alive]
            c2_members = [organisms[oid] for oid in zone.occupant_ids if organisms.get(oid) and organisms[oid].clan_id == c2.id and organisms[oid].alive]

            power_c1 = sum(m.genome.forca * (m.energy / 100.0) * (m.saude / m.max_saude) for m in c1_members)
            power_c2 = sum(m.genome.forca * (m.energy / 100.0) * (m.saude / m.max_saude) for m in c2_members)

            # Se um grupo está em desvantagem clara (< 60% do rival) ou possui alta cautela:
            # Opção de RECUO PACÍFICO inteligente (evita suicídio biológico)
            c1_cautela = sum(getattr(m.personality, "cautela", 0.5) for m in c1_members) / max(1, len(c1_members))
            c2_cautela = sum(getattr(m.personality, "cautela", 0.5) for m in c2_members) / max(1, len(c2_members))

            if power_c1 < (power_c2 * 0.60) or (c1_cautela > 0.65 and power_c1 < power_c2):
                # Clã 1 recua pacificamente para zona vizinha livre
                self._execute_peaceful_retreat(c1, c1_members, zone, tick, events, reason=f"Superioridade de {c2.name}")
                zone.controlling_clan_id = c2.id
                zone.status = "SETTLED"
            elif power_c2 < (power_c1 * 0.60) or (c2_cautela > 0.65 and power_c2 < power_c1):
                # Clã 2 recua pacificamente para zona vizinha livre
                self._execute_peaceful_retreat(c2, c2_members, zone, tick, events, reason=f"Superioridade de {c1.name}")
                zone.controlling_clan_id = c1.id
                zone.status = "SETTLED"
            else:
                # Forças equilibradas e competição ativa por recursos escassos: Zona CONTESTED
                zone.status = "CONTESTED"
                zone.dispute_ticks += 1
                if zone.dispute_ticks == 1 or zone.dispute_ticks % 40 == 0:
                    zone.log_event("territory_dispute", f"Disputa territorial ativa entre {c1.name} e {c2.name} em {zone.name}", tick)
                    events.append({
                        "type": "territory_contested",
                        "zone_name": zone.name,
                        "clan1": c1.name,
                        "clan2": c2.name,
                        "tick": tick,
                    })

    def _execute_peaceful_retreat(
        self,
        clan: Clan,
        retreating_members: List[Organism],
        contested_zone: TerritoryZone,
        tick: int,
        events: List[Dict[str, Any]],
        reason: str,
    ) -> None:
        """Executa o recuo pacífico e estratégico de um clã para evitar confronto mortal em desvantagem."""
        candidate_zones = [
            z for z in self.zones.values()
            if z.id != contested_zone.id and z.controlling_clan_id is None
            and z.status != "DEGRADED" and z.abandoned_cooldown == 0
        ]
        if not candidate_zones:
            candidate_zones = [z for z in self.zones.values() if z.id != contested_zone.id]

        target_zone = min(candidate_zones, key=lambda z: contested_zone.distance_to_point(z.x, z.y))

        contested_zone.log_event("clan_peaceful_retreat", f"{clan.name} recuou pacificamente de {contested_zone.name} para {target_zone.name} ({reason})", tick)

        for member in retreating_members:
            member.target_migration_zone = (target_zone.x, target_zone.y)
            member.territory_cooldown = 80
            member.territory_id = target_zone.id
            if getattr(member, "memory", None):
                member.memory.safe_haven = (target_zone.x, target_zone.y)

        events.append({
            "type": "clan_peaceful_retreat",
            "clan_name": clan.name,
            "origin_zone": contested_zone.name,
            "dest_zone": target_zone.name,
            "retreat_count": len(retreating_members),
            "reason": reason,
            "tick": tick,
        })
