"""Módulo de Relações Sociais Individuais, Reputação, Confiança e Dinâmica de Liderança."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple


@dataclass
class SocialRelationship:
    """
    Relação social individual entre um animal e outro indivíduo específico.
    Estrutura esparsa e compacta contendo as dimensões afetivas e comportamentais fundamentais.
    """

    target_id: int
    target_name: str = ""
    target_species: str = "PREDATOR"

    # Dimensões afetivas / comportamentais fundamentais [-1.0 a +1.0] ou [0.0 a 1.0]
    trust: float = 0.50          # Confiança [-1.0 a +1.0] (negativo = desconfiança/traição, positivo = lealdade)
    affinity: float = 0.50       # Afinidade social [-1.0 a +1.0] (atração gregária vs repulsa)
    fear: float = 0.0            # Medo / Intimidação [0.0 a 1.0] (tendência à fuga e submissão)
    rivalry: float = 0.0         # Rivalidade [0.0 a 1.0] (disputa de recursos, território ou liderança)
    hostility: float = 0.0       # Hostilidade [0.0 a 1.0] (probabilidade de agressão física)
    cooperation_count: int = 0   # Histórico acumulado de interações cooperativas bem-sucedidas
    last_interaction_tick: int = 0 # Ciclo da última interação relevante

    def decay(self, elapsed_ticks: int, rate: float = 0.0003) -> None:
        """
        Decai suavemente emoções extremas em direção a estados neutros basais com o passar do tempo.
        """
        if elapsed_ticks <= 0:
            return

        factor = max(0.0, 1.0 - (elapsed_ticks * rate))

        # Medo, rivalidade e hostilidade se dissipam gradualmente sem reforço
        self.fear = round(max(0.0, self.fear * factor), 3)
        self.rivalry = round(max(0.0, self.rivalry * factor), 3)
        self.hostility = round(max(0.0, self.hostility * factor), 3)

        # Confiança e afinidade convergem lentamente para o ponto neutro (0.50)
        if self.trust > 0.50:
            self.trust = round(max(0.50, 0.50 + (self.trust - 0.50) * factor), 3)
        elif self.trust < 0.50:
            self.trust = round(min(0.50, 0.50 - (0.50 - self.trust) * factor), 3)

        if self.affinity > 0.50:
            self.affinity = round(max(0.50, 0.50 + (self.affinity - 0.50) * factor), 3)
        elif self.affinity < 0.50:
            self.affinity = round(min(0.50, 0.50 - (0.50 - self.affinity) * factor), 3)

    def significance(self) -> float:
        """
        Calcula o grau de relevância desta relação para política de descarte/poda seletiva.
        Relações neutras e antigas pontuam baixo; relações intensas pontuam alto.
        """
        trust_dev = abs(self.trust - 0.50)
        affinity_dev = abs(self.affinity - 0.50)
        coop_bonus = min(1.0, self.cooperation_count * 0.15)
        return (
            trust_dev * 1.5
            + affinity_dev * 1.5
            + self.fear * 1.8
            + self.rivalry * 1.2
            + self.hostility * 2.0
            + coop_bonus
        )

    def get_status_label(self) -> str:
        """Retorna uma classificação semântica do relacionamento para exibição."""
        if self.hostility >= 0.55:
            return "Inimigo Hostil"
        if self.fear >= 0.55:
            return "Ameaça Temida"
        if self.rivalry >= 0.55:
            return "Rival Declarado"
        if self.trust >= 0.75 and self.affinity >= 0.70:
            return "Aliado Leal"
        if self.trust >= 0.60:
            return "Confiável"
        if self.trust <= 0.20:
            return "Desconfiança"
        if self.affinity >= 0.65:
            return "Afinidade Amigável"
        return "Neutro / Conhecido"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_name": self.target_name,
            "target_species": self.target_species,
            "trust": round(self.trust, 2),
            "affinity": round(self.affinity, 2),
            "fear": round(self.fear, 2),
            "rivalry": round(self.rivalry, 2),
            "hostility": round(self.hostility, 2),
            "cooperation_count": self.cooperation_count,
            "last_interaction_tick": self.last_interaction_tick,
            "status_label": self.get_status_label(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SocialRelationship:
        return cls(
            target_id=int(data.get("target_id", 0)),
            target_name=str(data.get("target_name", "")),
            target_species=str(data.get("target_species", "PREDATOR")),
            trust=float(data.get("trust", 0.50)),
            affinity=float(data.get("affinity", 0.50)),
            fear=float(data.get("fear", 0.0)),
            rivalry=float(data.get("rivalry", 0.0)),
            hostility=float(data.get("hostility", 0.0)),
            cooperation_count=int(data.get("cooperation_count", 0)),
            last_interaction_tick=int(data.get("last_interaction_tick", 0)),
        )


# Pesos configuráveis para eleição e legitimidade de liderança de clã
DEFAULT_CLAN_ELECTION_WEIGHTS = {
    "physical_strength": 0.45,   # Força individual e aptidão biológica [0.0 - 100.0]
    "collective_trust": 0.30,    # Confiança média dos membros do clã no candidato [0.0 - 100.0]
    "cooperation_history": 0.15, # Histórico médio de cooperações realizadas com membros [0.0 - 100.0]
    "hostility_penalty": 0.10,   # Penalidade por hostilidade interna contra o candidato [0.0 - 100.0]
}


def calculate_candidate_support(
    candidate: Any,
    clan_members: List[Any],
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, float]:
    """
    Calcula a pontuação de liderança integrada de um candidato no clã.

    Fórmula:
    S_total = W_fis * S_fisico + W_trust * S_trust + W_coop * S_coop - W_host * S_host

    Retorna:
    - total_score: Pontuação ponderada final [0.0 - 100.0]
    - avg_trust: Confiança média dos membros no candidato [-1.0 a +1.0]
    - approval_rating: Percentual de membros que apoiam o candidato [0.0 - 100.0%]
    """
    from .clan import calculate_leadership_score

    if weights is None:
        weights = DEFAULT_CLAN_ELECTION_WEIGHTS

    phys_score = calculate_leadership_score(candidate)

    other_members = [m for m in clan_members if m.id != candidate.id and getattr(m, "is_alive", True)]
    if not other_members:
        # Se não há outros membros vivos, baseia-se unicamente na força física
        return round(phys_score, 1), 0.70, 100.0

    trust_scores: List[float] = []
    coop_scores: List[float] = []
    hostility_scores: List[float] = []
    supporters_count = 0

    for member in other_members:
        rel: Optional[SocialRelationship] = getattr(member, "relationships", {}).get(candidate.id)
        if rel is not None:
            t = rel.trust
            c = float(rel.cooperation_count)
            h = rel.hostility
        else:
            # Baseline de confiança entre membros do mesmo clã
            is_vranco = (getattr(member, "species", "PREDATOR") == "VRANCO")
            t = 0.65 if is_vranco else 0.50
            c = 0.0
            h = 0.0

        trust_scores.append(t)
        coop_scores.append(c)
        hostility_scores.append(h)

        # Membro apoia o líder se confiar (t >= 0.35) e não for hostil (h < 0.40)
        if t >= 0.35 and h < 0.40:
            supporters_count += 1

    avg_trust = sum(trust_scores) / len(trust_scores)
    avg_coop = sum(coop_scores) / len(coop_scores)
    avg_host = sum(hostility_scores) / len(hostility_scores)
    approval_rating = round((supporters_count / len(other_members)) * 100.0, 1)

    # Normalizações para [0.0 - 100.0]
    norm_trust_100 = min(100.0, max(0.0, ((avg_trust + 1.0) / 2.0) * 100.0))
    norm_coop_100 = min(100.0, max(0.0, (avg_coop / 8.0) * 100.0))
    norm_host_100 = min(100.0, max(0.0, avg_host * 100.0))

    w_phys = weights.get("physical_strength", 0.45)
    w_trust = weights.get("collective_trust", 0.30)
    w_coop = weights.get("cooperation_history", 0.15)
    w_host = weights.get("hostility_penalty", 0.10)

    total_score = (
        w_phys * phys_score
        + w_trust * norm_trust_100
        + w_coop * norm_coop_100
        - w_host * norm_host_100
    )

    total_score = round(max(0.0, min(100.0, total_score)), 1)
    return total_score, round(avg_trust, 2), approval_rating
