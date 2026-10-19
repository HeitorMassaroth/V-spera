"""Sistema Avançado de Clãs, Liderança Alpha/Beta, Reserva Coletiva e Estratégia."""

from __future__ import annotations
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from ..entities.clan import (
    Clan,
    ClanSocialStage,
    ClanRelation,
    ClanPriorityType,
    ClanPriority,
    ClanObjective,
    calculate_leadership_score,
)
from ..entities.organism import Organism
from ..entities.nest import Nest
from ..entities.genealogy import GenealogyRegistry
from ..prng import PRNG

CLAN_NAMES = [
    "Clã Solaris", "Clã Apex", "Clã Ignis", "Clã Sylva", "Clã Terra",
    "Clã Umbra", "Clã Astra", "Clã Zephyr", "Clã Boreas", "Clã Titan",
    "Clã Vulcan", "Clã Orion", "Clã Chronos", "Clã Fenrir", "Clã Chimera"
]


class ClanSystem:
    """
    Gerencia a emergência espontânea de clãs, eleição de Alpha e Beta,
    economia comunal, prioridades estratégicas, diplomacia, guerras e expulsões.
    """

    def __init__(
        self,
        cooperation_threshold_occasional: float = 10.0,
        cooperation_threshold_recurrent: float = 25.0,
        cooperation_threshold_established: float = 40.0,
        cooperation_radius: float = 280.0,
        election_interval_ticks: int = 30,
    ) -> None:
        self.coop_thresh_occasional = cooperation_threshold_occasional
        self.coop_thresh_recurrent = cooperation_threshold_recurrent
        self.coop_thresh_established = cooperation_threshold_established
        self.cooperation_radius = cooperation_radius
        self.election_interval = election_interval_ticks

        self.clans: Dict[int, Clan] = {}
        # Matriz de cooperação par a par entre famílias: (min_fam_id, max_fam_id) -> coop_score
        self.family_coop: Dict[Tuple[int, int], float] = {}
        self._next_clan_id_counter: int = 1

    def _next_clan_id(self) -> int:
        cid = self._next_clan_id_counter
        self._next_clan_id_counter += 1
        return cid

    def _pair_key(self, id1: int, id2: int) -> Tuple[int, int]:
        return (min(id1, id2), max(id1, id2))

    def get_family_coop(self, id1: int, id2: int) -> float:
        return self.family_coop.get(self._pair_key(id1, id2), 0.0)

    def add_family_coop(self, id1: int, id2: int, amount: float) -> float:
        key = self._pair_key(id1, id2)
        new_val = max(0.0, self.family_coop.get(key, 0.0) + amount)
        self.family_coop[key] = new_val
        return new_val

    def update(
        self,
        organisms: Dict[int, Organism],
        families: Dict[int, Any],
        nests: Dict[int, Nest],
        prng: PRNG,
        genealogy: GenealogyRegistry,
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Executa a dinâmica completa dos clãs a cada ciclo de simulação."""

        # 1. Atualiza cooperação espontânea e transição de estágios sociais
        self._evaluate_spontaneous_clan_formation(organisms, families, nests, events, tick)

        # 2. Atualiza eleição, estabilidade e sucessão de liderança (Alpha & Beta)
        self._update_clan_leadership(organisms, events, tick)

        # 3. Economia Coletiva: Coleta para reserva e redistribuição para ninhos/membros necessitados
        self._update_communal_economy(organisms, families, nests, events, tick)

        # 4. Avaliação dinâmica da fila de prioridades estratégicas pelo Alpha & Beta
        self._evaluate_strategic_priorities(organisms, nests, events, tick)

        # 5. Avaliação de conflitos internos e expulsão de famílias antissociais/parasitárias
        self._evaluate_expulsions(organisms, families, events, tick)

        # 6. Expansão territorial dos clãs consolidados
        self._evaluate_territorial_expansion(nests, events, tick)

        # 7. Diplomacia entre clãs, conflitos territoriais, guerras e tréguas
        self._update_inter_clan_diplomacy(organisms, nests, events, tick)

    # -------------------------------------------------------------------------
    # 1. FORMAÇÃO ESPONTÂNEA DE CLÃS & ESTÁGIOS SOCIAIS
    # -------------------------------------------------------------------------
    def _evaluate_spontaneous_clan_formation(
        self,
        organisms: Dict[int, Organism],
        families: Dict[int, Any],
        nests: Dict[int, Nest],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        Avalia a proximidade dos ninhos e ações cooperativas entre famílias independentes.
        Um clã surge quando pelo menos 3 famílias próximas cooperam regularmente.
        """
        active_fam_ids = [fid for fid, f in families.items() if getattr(f, "is_active", True)]
        if len(active_fam_ids) < 3:
            return

        # Incrementa cooperação suave quando famílias estão próximas, bem alimentadas e sem conflitos
        for i in range(len(active_fam_ids)):
            fid1 = active_fam_ids[i]
            nest1 = nests.get(getattr(families[fid1], "nest_id", -1))
            if not nest1:
                continue

            for j in range(i + 1, len(active_fam_ids)):
                fid2 = active_fam_ids[j]
                nest2 = nests.get(getattr(families[fid2], "nest_id", -1))
                if not nest2:
                    continue

                dist = math.hypot(nest1.x - nest2.x, nest1.y - nest2.y)
                if dist <= self.cooperation_radius:
                    # Ambas as famílias têm pais vivos e sem hostilidade ativa
                    p1 = organisms.get(getattr(families[fid1], "patriarch_id", -1))
                    p2 = organisms.get(getattr(families[fid2], "patriarch_id", -1))
                    if p1 and p2 and getattr(p1, "alive", True) and getattr(p2, "alive", True):
                        # Se ambos têm boa sociabilidade e não estão em combate, cooperam
                        soc = (p1.personality.sociabilidade + p2.personality.sociabilidade) / 2.0
                        if soc >= 0.40 and p1.current_state != Organism.STATE_FLEEING and p2.current_state != Organism.STATE_FLEEING:
                            self.add_family_coop(fid1, fid2, 0.15)

        # Agrupa famílias com base na cooperação mútua
        # Famílias que já pertencem a um clã mantêm o clã
        assigned_families: Set[int] = set()
        for clan in self.clans.values():
            if clan.is_active:
                assigned_families.update(clan.family_ids)

        unassigned_fams = [fid for fid in active_fam_ids if fid not in assigned_families]

        # Busca clusters de 3+ famílias que cooperam
        for i in range(len(unassigned_fams)):
            f_seed = unassigned_fams[i]
            coop_group = {f_seed}

            for j in range(len(unassigned_fams)):
                if i == j:
                    continue
                f_other = unassigned_fams[j]
                if self.get_family_coop(f_seed, f_other) >= self.coop_thresh_occasional:
                    coop_group.add(f_other)

            if len(coop_group) >= 3:
                # Calcula cooperação média do grupo
                pair_scores: List[float] = []
                group_list = list(coop_group)
                for a in range(len(group_list)):
                    for b in range(a + 1, len(group_list)):
                        pair_scores.append(self.get_family_coop(group_list[a], group_list[b]))

                avg_coop = sum(pair_scores) / max(1, len(pair_scores))

                # Determina estágio social
                if avg_coop >= self.coop_thresh_established:
                    new_stage = ClanSocialStage.ESTABLISHED_CLAN
                elif avg_coop >= self.coop_thresh_recurrent:
                    new_stage = ClanSocialStage.RECURRENT_COOP
                else:
                    new_stage = ClanSocialStage.OCCASIONAL_COOP

                # Cria a comunidade / clã
                clan_id = self._next_clan_id()
                clan_name = CLAN_NAMES[(clan_id - 1) % len(CLAN_NAMES)]

                # Calcula centro territorial a partir dos ninhos
                nest_coords = []
                for fid in coop_group:
                    n = nests.get(getattr(families[fid], "nest_id", -1))
                    if n:
                        nest_coords.append((n.x, n.y))
                tx = sum(c[0] for c in nest_coords) / max(1, len(nest_coords)) if nest_coords else 400.0
                ty = sum(c[1] for c in nest_coords) / max(1, len(nest_coords)) if nest_coords else 400.0

                new_clan = Clan(
                    id=clan_id,
                    name=clan_name,
                    stage=new_stage,
                    family_ids=set(coop_group),
                    territory_x=tx,
                    territory_y=ty,
                    territory_radius=180.0,
                    communal_food=20.0,
                    founded_tick=tick,
                )

                # Vincula organismos ao novo clã
                for fid in coop_group:
                    for org in organisms.values():
                        if org.family_id == fid:
                            org.clan_id = clan_id
                            org.clan_role = "MEMBRO"

                # Se já atingiu ESTABLISHED_CLAN, elege Alpha e Beta
                if new_stage == ClanSocialStage.ESTABLISHED_CLAN:
                    new_clan.elect_leaders(organisms, tick, force=True)

                new_clan.log_event("clan_formed", f"{clan_name} emergiu com {len(coop_group)} famílias cooperantes no estágio {new_stage.value}!", tick)
                self.clans[clan_id] = new_clan

                events.append({
                    "type": "clan_formed",
                    "clan_id": clan_id,
                    "clan_name": clan_name,
                    "stage": new_stage.value,
                    "families_count": len(coop_group),
                    "tick": tick,
                })
                break

        # Atualiza transição de estágio para clãs existentes
        for clan in self.clans.values():
            if not clan.is_active or clan.stage == ClanSocialStage.ESTABLISHED_CLAN:
                continue

            # Avalia se a cooperação aumentou para evoluir o estágio
            f_list = list(clan.family_ids)
            scores = []
            for a in range(len(f_list)):
                for b in range(a + 1, len(f_list)):
                    scores.append(self.get_family_coop(f_list[a], f_list[b]))
            avg_coop = sum(scores) / max(1, len(scores)) if scores else 0.0

            old_stage = clan.stage
            if avg_coop >= self.coop_thresh_established and len(clan.family_ids) >= 3:
                clan.stage = ClanSocialStage.ESTABLISHED_CLAN
                clan.elect_leaders(organisms, tick, force=True)
                clan.log_event("clan_stage_changed", f"{clan.name} evoluiu para Clã Estabelecido com liderança Alpha e Beta!", tick)
                events.append({
                    "type": "clan_stage_changed",
                    "clan_id": clan.id,
                    "clan_name": clan.name,
                    "stage": clan.stage.value,
                    "tick": tick,
                })
            elif avg_coop >= self.coop_thresh_recurrent and clan.stage == ClanSocialStage.OCCASIONAL_COOP:
                clan.stage = ClanSocialStage.RECURRENT_COOP
                clan.log_event("clan_stage_changed", f"{clan.name} intensificou cooperação e atingiu Cooperação Recorrente!", tick)

    # -------------------------------------------------------------------------
    # 2. LIDERANÇA: ALPHA E BETA (ELEIÇÃO, ESTABILIDADE E SUCESSÃO)
    # -------------------------------------------------------------------------
    def _update_clan_leadership(
        self,
        organisms: Dict[int, Organism],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        Recalcula líderes periodicamente ou sob contingência (morte/incapacitação/parceria).
        Garante que Alpha e Beta não possuam parceiros ativos e não possam acasalar enquanto em liderança.
        """
        for clan in self.clans.values():
            if not clan.is_active or clan.stage != ClanSocialStage.ESTABLISHED_CLAN:
                continue

            # Verifica se os titulares continuam válidos ou se há crise de legitimidade
            alpha_valid = clan.alpha_id is not None and clan.alpha_id in organisms and clan.is_eligible_for_leadership(organisms[clan.alpha_id])
            beta_valid = clan.beta_id is not None and clan.beta_id in organisms and clan.is_eligible_for_leadership(organisms[clan.beta_id])

            needs_election = (
                not alpha_valid or
                not beta_valid or
                clan.has_legitimacy_crisis or
                ((tick - clan.last_election_tick) >= self.election_interval)
            )

            if needs_election:
                old_alpha = clan.alpha_id
                old_beta = clan.beta_id

                clan.elect_leaders(organisms, tick, force=False)

                # Atualiza papéis clan_role nos organismos
                for org in organisms.values():
                    if org.clan_id == clan.id:
                        if org.id == clan.alpha_id:
                            org.clan_role = "ALPHA"
                        elif org.id == clan.beta_id:
                            org.clan_role = "BETA"
                        else:
                            org.clan_role = "MEMBRO"

                # Emite eventos se houve troca de liderança
                if clan.alpha_id != old_alpha and clan.alpha_id is not None:
                    leader_org = organisms.get(clan.alpha_id)
                    events.append({
                        "type": "alpha_elected",
                        "clan_id": clan.id,
                        "clan_name": clan.name,
                        "leader_id": clan.alpha_id,
                        "leader_name": leader_org.name if leader_org else f"Animal#{clan.alpha_id}",
                        "score": clan.alpha_score,
                        "approval_rating": clan.alpha_approval_rating,
                        "has_crisis": clan.has_legitimacy_crisis,
                        "tick": tick,
                    })

                if clan.beta_id != old_beta and clan.beta_id is not None:
                    beta_org = organisms.get(clan.beta_id)
                    events.append({
                        "type": "beta_elected",
                        "clan_id": clan.id,
                        "clan_name": clan.name,
                        "beta_id": clan.beta_id,
                        "beta_name": beta_org.name if beta_org else f"Animal#{clan.beta_id}",
                        "score": clan.beta_score,
                        "tick": tick,
                    })

            # Avalia deserção voluntária de predadores descontentes que rejeitam a liderança Alpha
            if clan.alpha_id is not None and len(clan.family_ids) > 2:
                for org in list(organisms.values()):
                    if (
                        org.alive
                        and org.clan_id == clan.id
                        and org.clan_role == "MEMBRO"
                        and getattr(org, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_PREDATOR
                    ):
                        rel_alpha = org.relationships.get(clan.alpha_id)
                        if rel_alpha and rel_alpha.trust < -0.40 and rel_alpha.hostility > 0.40:
                            org.clan_id = None
                            org.clan_role = None
                            org.update_social_interaction(clan.alpha_id, "DESERTION", intensity=0.75, tick=tick, target_name=f"Ex-Líder#{clan.alpha_id}")
                            clan.log_event("clan_desertion", f"{org.name} desertou do {clan.name} por profunda desconfiança e rejeição à liderança do Alpha!", tick)
                            events.append({
                                "type": "clan_desertion",
                                "clan_id": clan.id,
                                "clan_name": clan.name,
                                "organism_id": org.id,
                                "organism_name": org.name,
                                "reason": "Rejeição e desconfiança extrema em relação ao líder Alpha",
                                "tick": tick,
                            })

    # -------------------------------------------------------------------------
    # 3. ECONOMIA COLETIVA & RESERVA DE ALIMENTOS
    # -------------------------------------------------------------------------
    def _update_communal_economy(
        self,
        organisms: Dict[int, Organism],
        families: Dict[int, Any],
        nests: Dict[int, Nest],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        Coleta fracionária de excedentes de biomassa para a reserva comunal e
        redistribuição para famílias com filhotes ou indivíduos famintos.
        """
        for clan in self.clans.values():
            if not clan.is_active:
                continue

            # Membros do clã com carried_food > 15 contribuem 20% para a reserva do clã ao passar pelo território
            for org in organisms.values():
                if org.clan_id == clan.id and org.carried_food >= 12.0:
                    dist_to_center = math.hypot(org.x - clan.territory_x, org.y - clan.territory_y)
                    if dist_to_center <= clan.territory_radius:
                        donation = round(org.carried_food * 0.20, 1)
                        if donation > 1.0:
                            org.carried_food -= donation
                            clan.add_communal_food(donation, org.family_id or 0)
                            if clan.alpha_id is not None and clan.alpha_id in organisms:
                                org.update_social_interaction(clan.alpha_id, "RESOURCE_SHARING", intensity=0.5, tick=tick, target_name=organisms[clan.alpha_id].name)
                                organisms[clan.alpha_id].update_social_interaction(org.id, "RESOURCE_SHARING", intensity=0.4, tick=tick, target_name=org.name)

            # Se a reserva tem comida suficiente (> 25 kcal), socorre ninhos famintos do clã
            if clan.communal_food >= 25.0:
                for fid in clan.family_ids:
                    fam = families.get(fid)
                    if not fam or not fam.nest_id:
                        continue
                    nest = nests.get(fam.nest_id)
                    if nest and nest.is_active and nest.food_storage < 10.0:
                        # Repassa 12 kcal da reserva comunal diretamente para o ninho faminto
                        aid = clan.consume_communal_food(12.0, fid)
                        if aid > 0.0:
                            nest.add_food(aid)
                            clan.log_event("communal_aid", f"Reserva do clã repassou {aid:.1f} kcal ao ninho faminto da Família #{fid}", tick)
                            if clan.alpha_id is not None:
                                p_id = getattr(fam, "patriarch_id", None) or getattr(fam, "matriarch_id", None)
                                if p_id and p_id in organisms:
                                    organisms[p_id].update_social_interaction(clan.alpha_id, "HELP_RECEIVED", intensity=0.7, tick=tick, target_name="Líder Alpha")

    # -------------------------------------------------------------------------
    # 4. PRIORIDADES ESTRATÉGICAS DEFINIDAS POR ALPHA & BETA
    # -------------------------------------------------------------------------
    def _evaluate_strategic_priorities(
        self,
        organisms: Dict[int, Organism],
        nests: Dict[int, Nest],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        O Alpha (com suporte do Beta) ajusta a fila de prioridades estratégicas
        conforme o contexto ecológico real do clã.
        """
        for clan in self.clans.values():
            if not clan.is_active or clan.stage != ClanSocialStage.ESTABLISHED_CLAN:
                continue

            clan_orgs = [o for o in organisms.values() if o.clan_id == clan.id and o.is_alive]
            if not clan_orgs:
                continue

            avg_hunger = sum(o.hunger for o in clan_orgs) / max(1, len(clan_orgs))
            avg_health = sum(o.saude for o in clan_orgs) / max(1, len(clan_orgs))

            new_priorities: List[ClanPriority] = []

            # 1. Crise Alimentar Emergencial
            if avg_hunger > 45.0 or clan.communal_food < 10.0:
                new_priorities.append(ClanPriority(
                    type=ClanPriorityType.SURVIVAL_FOOD,
                    title="Forrageamento Emergencial Coletivo",
                    urgency=1,
                    description="Coleta intensiva de alimento para evitar mortes por inanição.",
                    created_tick=tick,
                ))

            # 2. Guerra ou Ameaça Hostil Ativa
            has_war = any(rel == ClanRelation.WAR for rel in clan.diplomacy.values())
            if has_war:
                new_priorities.append(ClanPriority(
                    type=ClanPriorityType.DEFEND_NEST,
                    title="Mobilização Defensiva Territorial",
                    urgency=1 if not new_priorities else 2,
                    description="Guardiões patrulham os ninhos e interceptam incursões rivais.",
                    created_tick=tick,
                ))

            # 3. Distribuição de Recursos para Filhotes
            total_pups = sum(1 for o in clan_orgs if o.role == Organism.ROLE_CHILD)
            if total_pups > 0 and clan.communal_food >= 30.0:
                new_priorities.append(ClanPriority(
                    type=ClanPriorityType.DISTRIBUTE_FOOD,
                    title="Suprimento da Prole",
                    urgency=3,
                    description="Alimentação prioritária dos filhotes dependentes nos ninhos.",
                    created_tick=tick,
                ))

            # 4. Expansão Territorial (se houver abundância)
            if clan.communal_food > 60.0 and avg_health > 70.0 and not has_war:
                new_priorities.append(ClanPriority(
                    type=ClanPriorityType.EXPAND_TERRITORY,
                    title="Expansão Territorial",
                    urgency=4,
                    description="Exploração de novos oásis e ampliação da fronteira do clã.",
                    created_tick=tick,
                ))

            # Se a prioridade principal mudou, registra no histórico
            if not clan.priorities or (new_priorities and clan.priorities[0].type != new_priorities[0].type):
                clan.priorities = new_priorities
                if new_priorities:
                    clan.log_event("clan_priority_changed", f"Alpha definiu nova prioridade: {new_priorities[0].title}", tick)
                    events.append({
                        "type": "clan_priority_changed",
                        "clan_id": clan.id,
                        "clan_name": clan.name,
                        "priority": new_priorities[0].title,
                        "urgency": new_priorities[0].urgency,
                        "tick": tick,
                    })

    # -------------------------------------------------------------------------
    # 5. EXPULSÃO DE FAMÍLIAS & CONFLITOS INTERNOS
    # -------------------------------------------------------------------------
    def _evaluate_expulsions(
        self,
        organisms: Dict[int, Organism],
        families: Dict[int, Any],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        O Alpha/Beta pode decretar a expulsão de uma família que consuma excessivamente
        sem contribuir ou que apresente agressões reincidentes contra o clã.
        """
        for clan in self.clans.values():
            if not clan.is_active or len(clan.family_ids) <= 3:
                continue

            # Clãs de Vrancos são puramente altruístas e solidários: não expulsam famílias
            clan_orgs = [o for o in organisms.values() if o.clan_id == clan.id]
            if any(getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO for o in clan_orgs):
                continue

            for fid in list(clan.family_ids):
                contrib = clan.family_contributions.get(fid, 0.0)
                consump = clan.family_consumptions.get(fid, 0.0)

                # Parasitismo grave: consumiu mais de 50 kcal e contribuiu menos de 5%
                if consump > 50.0 and contrib < (consump * 0.05):
                    # Expulsão decretada pelo Alpha
                    clan.family_ids.remove(fid)
                    clan.log_event("family_expelled", f"Família #{fid} foi expulsa do clã por parasitismo crônico de recursos!", tick)

                    # Desvincula organismos da família expulsa e registra memória episódica e relações sociais
                    for org in organisms.values():
                        if org.family_id == fid:
                            org.clan_id = None
                            org.clan_role = None
                            if clan.alpha_id is not None:
                                org.update_social_interaction(clan.alpha_id, "EXPULSION", intensity=0.85, tick=tick, target_name=f"Líder Alpha#{clan.alpha_id}")
                            if getattr(org, "memory", None):
                                org.memory.add_episode(
                                    event_type="EXPELLED",
                                    description=f"Expulso do {clan.name}",
                                    tick=tick,
                                    x=org.x,
                                    y=org.y,
                                    intensity=0.85,
                                    relevance=0.9,
                                    involved_id=clan.alpha_id or 0,
                                    involved_name=clan.name,
                                )

                    events.append({
                        "type": "family_expelled",
                        "clan_id": clan.id,
                        "clan_name": clan.name,
                        "family_id": fid,
                        "reason": "Parasitismo crônico de alimentos",
                        "tick": tick,
                    })

    # -------------------------------------------------------------------------
    # 6. EXPANSÃO TERRITORIAL
    # -------------------------------------------------------------------------
    def _evaluate_territorial_expansion(
        self,
        nests: Dict[int, Nest],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """Clãs prósperos expandem gradualmente o raio do seu território protegido."""
        for clan in self.clans.values():
            if not clan.is_active or clan.stage != ClanSocialStage.ESTABLISHED_CLAN:
                continue

            if clan.communal_food > 70.0 and clan.territory_radius < 320.0:
                clan.territory_radius += 10.0
                clan.communal_food -= 15.0 # Custo de manter e patrulhar novo perímetro
                clan.log_event("clan_expanded", f"{clan.name} expandiu seu território para raio {clan.territory_radius:.0f}px!", tick)

    # -------------------------------------------------------------------------
    # 7. DIPLOMACIA, GUERRAS E TRÉGUAS ENTRE CLÃS
    # -------------------------------------------------------------------------
    def _update_inter_clan_diplomacy(
        self,
        organisms: Dict[int, Organism],
        nests: Dict[int, Nest],
        events: List[Dict[str, Any]],
        tick: int,
    ) -> None:
        """
        Gerencia relações diplomáticas (Neutralidade, Competição, Hostilidade, Guerra e Trégua)
        entre comunidades distintas.
        """
        active_clans = [c for c in self.clans.values() if c.is_active and c.stage == ClanSocialStage.ESTABLISHED_CLAN]
        if len(active_clans) < 2:
            return

        for i in range(len(active_clans)):
            c1 = active_clans[i]
            for j in range(i + 1, len(active_clans)):
                c2 = active_clans[j]

                # Distância territorial entre os centros dos clãs
                dist = math.hypot(c1.territory_x - c2.territory_x, c1.territory_y - c2.territory_y)

                # Atualiza contagem de trégua se ativa
                t1 = c1.truce_ticks.get(c2.id, 0)
                if t1 > 0:
                    c1.truce_ticks[c2.id] = t1 - 1
                    c2.truce_ticks[c1.id] = t1 - 1
                    if t1 - 1 == 0:
                        c1.diplomacy[c2.id] = ClanRelation.NEUTRAL
                        c2.diplomacy[c1.id] = ClanRelation.NEUTRAL
                        c1.log_event("clan_truce_ended", f"Trégua com {c2.name} expirou. Relações normalizadas.", tick)
                    continue

                # Verifica se ambos os clãs pertencem à raça Vrancos
                c1_orgs = [o for o in organisms.values() if o.clan_id == c1.id]
                c2_orgs = [o for o in organisms.values() if o.clan_id == c2.id]
                c1_is_vranco = any(getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO for o in c1_orgs)
                c2_is_vranco = any(getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO for o in c2_orgs)

                if c1_is_vranco and c2_is_vranco:
                    # Entre clãs Vrancos vigora solidariedade permanente e cooperação mútua
                    c1.diplomacy[c2.id] = ClanRelation.COOPERATION
                    c2.diplomacy[c1.id] = ClanRelation.COOPERATION
                    continue

                # Se territórios se sobrepõem e há disputa por recursos
                if dist <= (c1.territory_radius + c2.territory_radius):
                    curr_rel = c1.diplomacy.get(c2.id, ClanRelation.NEUTRAL)

                    # Se escassez ou proximidade excessiva, escala para COMPETITION -> HOSTILE -> WAR
                    if curr_rel == ClanRelation.NEUTRAL:
                        c1.diplomacy[c2.id] = ClanRelation.COMPETITION
                        c2.diplomacy[c1.id] = ClanRelation.COMPETITION
                    elif curr_rel == ClanRelation.COMPETITION:
                        # Alpha agressivo ou baixa comida desencadeia hostilidade
                        c1_alpha = organisms.get(c1.alpha_id or -1)
                        c2_alpha = organisms.get(c2.alpha_id or -1)
                        if c1_alpha and c2_alpha:
                            agr = (c1_alpha.personality.agressividade + c2_alpha.personality.agressividade) / 2.0
                            if agr >= 0.55:
                                c1.diplomacy[c2.id] = ClanRelation.WAR
                                c2.diplomacy[c1.id] = ClanRelation.WAR
                                c1.log_event("clan_war_declared", f"GUERRA DECLARADA contra {c2.name} por disputa territorial!", tick)
                                c2.log_event("clan_war_declared", f"GUERRA DECLARADA contra {c1.name} por disputa territorial!", tick)
                                events.append({
                                    "type": "clan_war_declared",
                                    "clan1_name": c1.name,
                                    "clan2_name": c2.name,
                                    "tick": tick,
                                })

                # Se em GUERRA, avalia trégua por exaustão ou baixas
                if c1.diplomacy.get(c2.id) == ClanRelation.WAR:
                    # Se um dos clãs ficou sem comida ou perdeu membros significativos
                    if c1.communal_food < 5.0 or c2.communal_food < 5.0:
                        c1.diplomacy[c2.id] = ClanRelation.TRUCE
                        c2.diplomacy[c1.id] = ClanRelation.TRUCE
                        c1.truce_ticks[c2.id] = 120
                        c2.truce_ticks[c1.id] = 120
                        c1.log_event("clan_truce_agreed", f"TRÉGUA firmada com {c2.name} devido à exaustão de guerra.", tick)
                        c2.log_event("clan_truce_agreed", f"TRÉGUA firmada com {c1.name} devido à exaustão de guerra.", tick)
                        events.append({
                            "type": "clan_truce_agreed",
                            "clan1_name": c1.name,
                            "clan2_name": c2.name,
                            "tick": tick,
                        })
