"""Entidade de primeira classe representando Clãs, Liderança (Alpha/Beta), Reserva Coletiva e Estratégia."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum


class ClanSocialStage(str, Enum):
    """Estágios de organização social de comunidades de famílias."""
    INDEPENDENT = "INDEPENDENT"           # Famílias independentes
    OCCASIONAL_COOP = "OCCASIONAL_COOP"   # Cooperação ocasional (compartilham recursos esporadicamente)
    RECURRENT_COOP = "RECURRENT_COOP"     # Cooperação recorrente (divisão frequente de alimento e defesa)
    ESTABLISHED_CLAN = "ESTABLISHED_CLAN" # Clã estabelecido com identidade coletiva, Alpha e Beta


class ClanRelation(str, Enum):
    """Relações diplomáticas entre clãs vizinhos."""
    NEUTRAL = "NEUTRAL"
    COOPERATION = "COOPERATION"
    ALLIANCE = "ALLIANCE"
    COMPETITION = "COMPETITION"
    HOSTILE = "HOSTILE"
    WAR = "WAR"
    TRUCE = "TRUCE"


class ClanPriorityType(str, Enum):
    """Tipos de prioridades coletivas estratégicas definidas pelo Alpha."""
    SURVIVAL_FOOD = "SURVIVAL_FOOD"           # Coleta emergencial de alimentos
    DEFEND_NEST = "DEFEND_NEST"               # Defesa de ninhos e filhotes sob ataque
    DISTRIBUTE_FOOD = "DISTRIBUTE_FOOD"       # Distribuição de alimentos da reserva para famílias críticas
    BUILD_SHELTER = "BUILD_SHELTER"           # Construção e melhoria de abrigos/ninhos
    EXPAND_TERRITORY = "EXPAND_TERRITORY"     # Exploração e expansão de território
    TERRITORIAL_WAR = "TERRITORIAL_WAR"       # Conflito e guerra territorial contra rival
    TRUCE_RECOVERY = "TRUCE_RECOVERY"         # Recuperação e trégua após guerra


@dataclass
class ClanPriority:
    """Prioridade estratégica ativa na fila do clã."""
    type: ClanPriorityType
    title: str
    urgency: int                             # 1 (mais urgente) a 5 (menos urgente)
    description: str
    target_cluster_id: Optional[int] = None
    target_clan_id: Optional[int] = None
    created_tick: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "title": self.title,
            "urgency": self.urgency,
            "description": self.description,
            "target_cluster_id": self.target_cluster_id,
            "target_clan_id": self.target_clan_id,
            "created_tick": self.created_tick,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClanPriority:
        raw_type = data["type"]
        p_type = ClanPriorityType(raw_type) if isinstance(raw_type, str) else raw_type
        return cls(
            type=p_type,
            title=str(data.get("title", "")),
            urgency=int(data.get("urgency", 3)),
            description=str(data.get("description", "")),
            target_cluster_id=int(data["target_cluster_id"]) if data.get("target_cluster_id") is not None else None,
            target_clan_id=int(data["target_clan_id"]) if data.get("target_clan_id") is not None else None,
            created_tick=int(data.get("created_tick", 0)),
        )


@dataclass
class ClanObjective:
    """Objetivo tático em andamento atribuído a membros do clã."""
    id: str
    type: ClanPriorityType
    assigned_organism_ids: List[int] = field(default_factory=list)
    progress: float = 0.0                    # 0.0 a 100.0%
    target_amount: float = 50.0
    current_amount: float = 0.0
    is_completed: bool = False
    is_failed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "assigned_count": len(self.assigned_organism_ids),
            "assigned_organism_ids": list(self.assigned_organism_ids),
            "progress": round(self.progress, 1),
            "target_amount": round(self.target_amount, 1),
            "current_amount": round(self.current_amount, 1),
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClanObjective:
        raw_type = data["type"]
        p_type = ClanPriorityType(raw_type) if isinstance(raw_type, str) else raw_type
        return cls(
            id=str(data["id"]),
            type=p_type,
            assigned_organism_ids=list(data.get("assigned_organism_ids", [])),
            progress=float(data.get("progress", 0.0)),
            target_amount=float(data.get("target_amount", 50.0)),
            current_amount=float(data.get("current_amount", 0.0)),
            is_completed=bool(data.get("is_completed", False)),
            is_failed=bool(data.get("is_failed", False)),
        )


# Pesos configuráveis para o cálculo do Índice de Força de Liderança
DEFAULT_LEADERSHIP_WEIGHTS = {
    "forca": 0.25,
    "resistencia": 0.20,
    "saude": 0.15,
    "velocidade": 0.15,
    "eficiencia_coleta": 0.10,
    "protecao": 0.10,
    "inteligencia": 0.05,
}


def calculate_leadership_score(organism: Any, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calcula o índice de força de liderança individual [0.0 - 100.0].
    Critério puramente individual, normalizado com pesos configuráveis.
    """
    if weights is None:
        weights = DEFAULT_LEADERSHIP_WEIGHTS

    genome = organism.genome
    personality = organism.personality

    # Normalizações para [0.0 - 1.0]
    norm_forca = min(1.0, max(0.0, genome.forca / 100.0))
    norm_resistencia = min(1.0, max(0.0, genome.resistencia / 100.0))
    norm_velocidade = min(1.0, max(0.0, genome.velocidade / 100.0))
    norm_inteligencia = min(1.0, max(0.0, genome.inteligencia / 100.0))

    # Saúde atual relativa à saúde máxima
    max_s = getattr(genome, "max_saude", 100.0) or 100.0
    norm_saude = min(1.0, max(0.0, organism.saude / max_s))

    # Personalidade [0.0 - 2.0]
    norm_eficiencia = min(1.0, max(0.0, getattr(personality, "eficiencia_coleta", 1.0) / 2.0))
    norm_protecao = min(1.0, max(0.0, getattr(personality, "instinto_protecao", 1.0) / 2.0))

    raw_score = (
        weights.get("forca", 0.25) * norm_forca
        + weights.get("resistencia", 0.20) * norm_resistencia
        + weights.get("saude", 0.15) * norm_saude
        + weights.get("velocidade", 0.15) * norm_velocidade
        + weights.get("eficiencia_coleta", 0.10) * norm_eficiencia
        + weights.get("protecao", 0.10) * norm_protecao
        + weights.get("inteligencia", 0.05) * norm_inteligencia
    )

    return round(raw_score * 100.0, 2)


@dataclass
class Clan:
    """Comunidade emergente de famílias com liderança Alpha/Beta, reserva de recursos e estratégia."""

    id: int
    name: str
    stage: ClanSocialStage = ClanSocialStage.INDEPENDENT
    family_ids: Set[int] = field(default_factory=set)

    # Liderança (Alpha e Beta) e Legitimidade
    alpha_id: Optional[int] = None
    beta_id: Optional[int] = None
    alpha_score: float = 0.0
    beta_score: float = 0.0
    alpha_approval_rating: float = 100.0  # Taxa de aprovação coletiva dos membros [0.0 - 100.0%]
    has_legitimacy_crisis: bool = False   # Indica crise de legitimidade (baixa confiança popular)
    crisis_ticks: int = 0
    last_election_tick: int = 0

    # Reserva de Alimentos Coletiva (Economia do Clã)
    communal_food: float = 0.0
    total_food_contributed: float = 0.0
    total_food_consumed: float = 0.0
    family_contributions: Dict[int, float] = field(default_factory=dict)
    family_consumptions: Dict[int, float] = field(default_factory=dict)

    # Território e Ninhos
    territory_x: float = 0.0
    territory_y: float = 0.0
    territory_radius: float = 180.0
    nest_ids: Set[int] = field(default_factory=set)

    # Estratégia e Prioridades
    priorities: List[ClanPriority] = field(default_factory=list)
    active_objectives: List[ClanObjective] = field(default_factory=list)

    # Diplomacia e Relações com outros Clãs (target_clan_id -> ClanRelation)
    diplomacy: Dict[int, ClanRelation] = field(default_factory=dict)
    diplomacy_scores: Dict[int, float] = field(default_factory=dict) # Positivo = amigável, Negativo = hostil
    truce_ticks: Dict[int, int] = field(default_factory=dict)

    # Histórico de Eventos do Clã
    history_log: List[Dict[str, Any]] = field(default_factory=list)
    founded_tick: int = 0
    is_active: bool = True

    def log_event(self, event_type: str, desc: str, tick: int, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra um acontecimento marcante na memória histórica do clã."""
        entry: Dict[str, Any] = {
            "type": event_type,
            "desc": desc,
            "tick": tick,
        }
        if extra:
            entry.update(extra)
        self.history_log.append(entry)
        if len(self.history_log) > 50:
            self.history_log.pop(0)

    def is_eligible_for_leadership(self, organism: Any) -> bool:
        """
        Verifica critérios estritos de elegibilidade para Alpha ou Beta:
        1. Adulto.
        2. Vivo e ativo (saúde > 15.0).
        3. Sem vínculo de parceiro ativo (partner_id is None).
        4. Pertence ao clã (sua família pertence ao clã ou é membro registrado).
        """
        if not getattr(organism, "is_alive", True):
            return False
        if organism.saude <= 15.0:
            return False
        # Idade adulta
        stage = getattr(organism, "life_stage", "ADULT")
        if stage != "ADULT":
            return False
        # Não possuir parceiro ativo!
        if organism.partner_id is not None:
            return False
        # Pertence ao clã (por clã registrado ou família participante)
        in_clan = (getattr(organism, "clan_id", None) == self.id) or (organism.family_id in self.family_ids)
        if not in_clan:
            return False
        return True

    def elect_leaders(
        self,
        organisms: Dict[int, Any],
        current_tick: int,
        force: bool = False,
        election_weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Elege Alpha e Beta baseando-se no índice de força biológica, confiança coletiva
        dos membros e histórico de cooperação, aplicando critérios de legitimidade.
        """
        from .social import calculate_candidate_support

        clan_members = [
            org for org in organisms.values()
            if (getattr(org, "clan_id", None) == self.id or getattr(org, "family_id", None) in self.family_ids)
            and getattr(org, "is_alive", True)
        ]

        # Avalia aprovação do titular atual se ele estiver vivo e no clã
        if self.alpha_id is not None and self.alpha_id in organisms:
            current_alpha_org = organisms[self.alpha_id]
            if self.is_eligible_for_leadership(current_alpha_org):
                _, cur_alpha_trust, cur_alpha_approval = calculate_candidate_support(
                    current_alpha_org, clan_members, weights=election_weights
                )
                self.alpha_approval_rating = cur_alpha_approval
                if cur_alpha_approval < 38.0 or cur_alpha_trust < 0.15:
                    self.has_legitimacy_crisis = True
                    self.crisis_ticks += 1
                else:
                    self.has_legitimacy_crisis = False
                    self.crisis_ticks = 0

        # Coleta e pontua todos os candidatos elegíveis com fórmula integrada
        candidates: List[Tuple[int, float, float]] = []
        for org_id, org in organisms.items():
            if self.is_eligible_for_leadership(org):
                score, avg_t, approval = calculate_candidate_support(
                    org, clan_members, weights=election_weights
                )
                candidates.append((org_id, score, approval))

        # Ordena por índice de liderança integrada decrescente
        candidates.sort(key=lambda x: x[1], reverse=True)

        new_alpha: Optional[int] = None
        new_beta: Optional[int] = None
        score_a: float = 0.0
        score_b: float = 0.0
        approval_a: float = 100.0

        if len(candidates) >= 1:
            new_alpha = candidates[0][0]
            score_a = candidates[0][1]
            approval_a = candidates[0][2]
        if len(candidates) >= 2:
            new_beta = candidates[1][0]
            score_b = candidates[1][1]

        alpha_valid = self.alpha_id is not None and self.alpha_id in organisms and self.is_eligible_for_leadership(organisms[self.alpha_id])
        beta_valid = self.beta_id is not None and self.beta_id in organisms and self.is_eligible_for_leadership(organisms[self.beta_id])

        # Sucessão de emergência quando Alpha se torna inválido
        if not alpha_valid:
            if beta_valid:
                old_beta = self.beta_id
                self.alpha_id = old_beta
                b_score, _, b_appr = calculate_candidate_support(organisms[old_beta], clan_members, weights=election_weights)
                self.alpha_score = b_score
                self.alpha_approval_rating = b_appr
                self.has_legitimacy_crisis = False
                self.crisis_ticks = 0
                self.log_event("alpha_succession", f"Beta #{old_beta} assumiu a liderança principal como novo Alpha!", current_tick)
                remaining = [c for c in candidates if c[0] != old_beta]
                if remaining:
                    self.beta_id = remaining[0][0]
                    self.beta_score = remaining[0][1]
                    self.log_event("beta_elected", f"Novo Beta #{self.beta_id} eleito após sucessão!", current_tick)
                else:
                    self.beta_id = None
                    self.beta_score = 0.0
                self.last_election_tick = current_tick
                return self.alpha_id, self.beta_id
            else:
                self.alpha_id = new_alpha
                self.alpha_score = score_a
                self.alpha_approval_rating = approval_a
                self.has_legitimacy_crisis = False
                self.crisis_ticks = 0
                self.beta_id = new_beta
                self.beta_score = score_b
                self.last_election_tick = current_tick
                if new_alpha:
                    self.log_event("alpha_elected", f"Novo Alpha #{new_alpha} eleito com score {score_a:.1f}", current_tick)
                if new_beta:
                    self.log_event("beta_elected", f"Novo Beta #{new_beta} eleito com score {score_b:.1f}", current_tick)
                return self.alpha_id, self.beta_id

        # Se Alpha continua válido
        # Se houver crise de legitimidade, a margem de proteção é zerada!
        required_margin = 0.5 if self.has_legitimacy_crisis else 3.0
        if force or (new_alpha and new_alpha != self.alpha_id and score_a > (self.alpha_score + required_margin)):
            old_alpha_id = self.alpha_id
            self.alpha_id = new_alpha
            self.alpha_score = score_a
            self.alpha_approval_rating = approval_a
            if self.has_legitimacy_crisis:
                self.log_event(
                    "alpha_deposed",
                    f"Alpha #{old_alpha_id} perdeu o apoio dos membros (Aprovação < 40%) e foi destituído por #{new_alpha} (Score {score_a:.1f})!",
                    current_tick,
                )
                self.has_legitimacy_crisis = False
                self.crisis_ticks = 0
            else:
                self.log_event("alpha_elected", f"Alpha #{new_alpha} superou o titular e assumiu a liderança (Score {score_a:.1f})", current_tick)

        # Atualização do Beta
        if not beta_valid or force or (new_beta and new_beta != self.beta_id and score_b > (self.beta_score + 3.0) and new_beta != self.alpha_id):
            valid_betas = [c for c in candidates if c[0] != self.alpha_id]
            if valid_betas:
                self.beta_id = valid_betas[0][0]
                self.beta_score = valid_betas[0][1]
                self.log_event("beta_elected", f"Novo Beta #{self.beta_id} eleito com score {self.beta_score:.1f}", current_tick)
            else:
                self.beta_id = None
                self.beta_score = 0.0

        self.last_election_tick = current_tick
        return self.alpha_id, self.beta_id

    def add_communal_food(self, amount: float, family_id: int) -> float:
        """Adiciona alimento à reserva coletiva do clã sem dupla contagem."""
        if amount <= 0.0:
            return 0.0
        self.communal_food += amount
        self.total_food_contributed += amount
        self.family_contributions[family_id] = self.family_contributions.get(family_id, 0.0) + amount
        return amount

    def consume_communal_food(self, amount: float, family_id: int) -> float:
        """Consome alimento da reserva coletiva do clã (ex: auxílio a famílias famintas)."""
        available = min(self.communal_food, amount)
        if available <= 0.0:
            return 0.0
        self.communal_food -= available
        self.total_food_consumed += available
        self.family_consumptions[family_id] = self.family_consumptions.get(family_id, 0.0) + available
        return available

    def to_dict(self) -> Dict[str, Any]:
        """Serialização para WebSocket e API REST."""
        return {
            "id": self.id,
            "name": self.name,
            "stage": self.stage.value,
            "family_ids": list(self.family_ids),
            "families_count": len(self.family_ids),
            "alpha_id": self.alpha_id,
            "beta_id": self.beta_id,
            "alpha_score": self.alpha_score,
            "beta_score": self.beta_score,
            "alpha_approval_rating": round(self.alpha_approval_rating, 1),
            "has_legitimacy_crisis": self.has_legitimacy_crisis,
            "crisis_ticks": self.crisis_ticks,
            "last_election_tick": self.last_election_tick,
            "communal_food": round(self.communal_food, 1),
            "total_food_contributed": round(self.total_food_contributed, 1),
            "total_food_consumed": round(self.total_food_consumed, 1),
            "family_contributions": {str(k): v for k, v in self.family_contributions.items()},
            "family_consumptions": {str(k): v for k, v in self.family_consumptions.items()},
            "territory": {
                "x": round(self.territory_x, 1),
                "y": round(self.territory_y, 1),
                "radius": round(self.territory_radius, 1),
            },
            "nest_ids": list(self.nest_ids),
            "priorities": [p.to_dict() for p in self.priorities],
            "active_objectives": [o.to_dict() for o in self.active_objectives],
            "diplomacy": {str(k): v.value for k, v in self.diplomacy.items()},
            "diplomacy_scores": {str(k): v for k, v in self.diplomacy_scores.items()},
            "truce_ticks": {str(k): v for k, v in self.truce_ticks.items()},
            "history_log": self.history_log[-15:], # Últimos 15 acontecimentos
            "founded_tick": self.founded_tick,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Clan:
        priorities = [
            ClanPriority.from_dict(p) if isinstance(p, dict) else p
            for p in data.get("priorities", [])
        ]
        objectives = [
            ClanObjective.from_dict(o) if isinstance(o, dict) else o
            for o in data.get("active_objectives", [])
        ]
        raw_diplomacy = data.get("diplomacy", {})
        diplomacy = {
            int(k): ClanRelation(v) if isinstance(v, str) else v
            for k, v in raw_diplomacy.items()
        }
        diplomacy_scores = {
            int(k): float(v)
            for k, v in data.get("diplomacy_scores", {}).items()
        }
        truce_ticks = {
            int(k): int(v)
            for k, v in data.get("truce_ticks", {}).items()
        }
        family_contributions = {
            int(k): float(v)
            for k, v in data.get("family_contributions", {}).items()
        }
        family_consumptions = {
            int(k): float(v)
            for k, v in data.get("family_consumptions", {}).items()
        }
        terr = data.get("territory", {})
        tx = float(terr.get("x", 0.0))
        ty = float(terr.get("y", 0.0))
        tr = float(terr.get("radius", 180.0))

        raw_stage = data.get("stage", ClanSocialStage.INDEPENDENT.value)
        try:
            stage = ClanSocialStage(raw_stage)
        except Exception:
            stage = ClanSocialStage.INDEPENDENT

        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            stage=stage,
            family_ids=set(data.get("family_ids", [])),
            alpha_id=int(data["alpha_id"]) if data.get("alpha_id") is not None else None,
            beta_id=int(data["beta_id"]) if data.get("beta_id") is not None else None,
            alpha_score=float(data.get("alpha_score", 0.0)),
            beta_score=float(data.get("beta_score", 0.0)),
            alpha_approval_rating=float(data.get("alpha_approval_rating", 100.0)),
            has_legitimacy_crisis=bool(data.get("has_legitimacy_crisis", False)),
            crisis_ticks=int(data.get("crisis_ticks", 0)),
            last_election_tick=int(data.get("last_election_tick", 0)),
            communal_food=float(data.get("communal_food", 0.0)),
            total_food_contributed=float(data.get("total_food_contributed", 0.0)),
            total_food_consumed=float(data.get("total_food_consumed", 0.0)),
            family_contributions=family_contributions,
            family_consumptions=family_consumptions,
            territory_x=tx,
            territory_y=ty,
            territory_radius=tr,
            nest_ids=set(data.get("nest_ids", [])),
            priorities=priorities,
            active_objectives=objectives,
            diplomacy=diplomacy,
            diplomacy_scores=diplomacy_scores,
            truce_ticks=truce_ticks,
            history_log=list(data.get("history_log", [])),
            founded_tick=int(data.get("founded_tick", 0)),
            is_active=bool(data.get("is_active", True)),
        )
