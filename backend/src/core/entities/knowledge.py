"""Entidades e modelos para o Sistema de Aprendizado Individual, Conhecimento Cognitivo e Sabedoria Coletiva."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class FoodHotspot:
    """Sítio fértil de alimentação consolidado através de evidências acumuladas."""

    x: float
    y: float
    confidence: float = 0.40          # Grau de certeza na fertilidade do sítio [0.0 - 1.0]
    success_count: int = 1            # Vezes em que encontrou alimento nesta região
    failure_count: int = 0            # Vezes em que visitou e encontrou o sítio esgotado
    last_visited_tick: int = 0        # Último ciclo em que o sítio foi visitado ou observado
    discovered_via: str = "EXPERIENCIA"  # 'EXPERIENCIA', 'TRANSMISSAO_SOCIAL', 'IMITACAO_PARENTEAL'

    def reinforce(self, tick: int, learning_rate: float = 0.25) -> None:
        """Reforça a confiança no sítio após novo consumo bem-sucedido."""
        self.success_count += 1
        self.last_visited_tick = tick
        # Aumento assintótico com retornos decrescentes
        self.confidence = min(1.0, self.confidence + learning_rate * (1.0 - self.confidence))

    def penalize(self, tick: int, penalty_rate: float = 0.30) -> None:
        """Penaliza a confiança ao encontrar o sítio esgotado (desaprendizado / extinção de crença)."""
        self.failure_count += 1
        self.last_visited_tick = tick
        self.confidence = max(0.0, self.confidence * (1.0 - penalty_rate))

    def decay(self, current_tick: int, decay_rate: float = 0.0004) -> None:
        """Decaimento temporal de crenças não revisitadas."""
        elapsed = max(0, current_tick - self.last_visited_tick)
        if elapsed > 100:
            self.confidence = max(0.05, self.confidence * math.exp(-decay_rate * (elapsed - 100)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "confidence": round(self.confidence, 2),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_visited_tick": self.last_visited_tick,
            "discovered_via": self.discovered_via,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FoodHotspot:
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            confidence=float(data.get("confidence", 0.4)),
            success_count=int(data.get("success_count", 1)),
            failure_count=int(data.get("failure_count", 0)),
            last_visited_tick=int(data.get("last_visited_tick", 0)),
            discovered_via=data.get("discovered_via", "EXPERIENCIA"),
        )


@dataclass
class DangerHotspot:
    """Zona de perigo reconhecida através de embates violentos ou presenciamento de mortes."""

    x: float
    y: float
    danger_level: float = 0.50        # Gravidade percebida da ameaça [0.0 - 1.0]
    radius: float = 55.0              # Raio de influência espacial da ameaça
    incident_count: int = 1           # Quantidade de ataques sofridos ou mortes testemunhadas aqui
    threat_type: str = "PREDACAO"     # 'PREDACAO', 'MORTE_TESTEMUNHADA', 'COMBATE_RIVAL'
    last_incident_tick: int = 0
    discovered_via: str = "EXPERIENCIA"  # 'EXPERIENCIA', 'ALERTA_SOCIAL', 'IMITACAO_PARENTEAL'

    def reinforce(self, tick: int, intensity: float = 0.5) -> None:
        """Intensifica a gravidade da zona após novo ataque ou susto."""
        self.incident_count += 1
        self.last_incident_tick = tick
        self.danger_level = min(1.0, self.danger_level + intensity * 0.35 * (1.0 - self.danger_level * 0.5))

    def decay(self, current_tick: int, decay_rate: float = 0.0003) -> None:
        """Atenuação temporal gradual do medo caso a área permaneça calma."""
        elapsed = max(0, current_tick - self.last_incident_tick)
        if elapsed > 150:
            self.danger_level = max(0.05, self.danger_level * math.exp(-decay_rate * (elapsed - 150)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "danger_level": round(self.danger_level, 2),
            "radius": round(self.radius, 1),
            "incident_count": self.incident_count,
            "threat_type": self.threat_type,
            "last_incident_tick": self.last_incident_tick,
            "discovered_via": self.discovered_via,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DangerHotspot:
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            danger_level=float(data.get("danger_level", 0.5)),
            radius=float(data.get("radius", 55.0)),
            incident_count=int(data.get("incident_count", 1)),
            threat_type=data.get("threat_type", "PREDACAO"),
            last_incident_tick=int(data.get("last_incident_tick", 0)),
            discovered_via=data.get("discovered_via", "EXPERIENCIA"),
        )


@dataclass
class ThreatProfile:
    """Perfil cognitivo de um predador ou rival individualmente reconhecido."""

    target_id: int
    target_name: str
    threat_score: float = 0.50        # Grau de letalidade percebida do indivíduo [0.0 - 1.0]
    encounters: int = 1
    last_seen_tick: int = 0

    def reinforce(self, tick: int, delta: float = 0.25) -> None:
        self.encounters += 1
        self.last_seen_tick = tick
        self.threat_score = min(1.0, self.threat_score + delta * (1.0 - self.threat_score))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_name": self.target_name,
            "threat_score": round(self.threat_score, 2),
            "encounters": self.encounters,
            "last_seen_tick": self.last_seen_tick,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThreatProfile:
        return cls(
            target_id=int(data["target_id"]),
            target_name=data.get("target_name", ""),
            threat_score=float(data.get("threat_score", 0.5)),
            encounters=int(data.get("encounters", 1)),
            last_seen_tick=int(data.get("last_seen_tick", 0)),
        )


@dataclass
class TacticalSkills:
    """Habilidades táticas processuais desenvolvidas por experiência e prática direta."""

    evasion_proficiency: float = 0.15     # Agilidade e escolha de vetores de fuga
    mobbing_coordination: float = 0.15    # Capacidade de sincronizar defesa coletiva (Vrancos)
    hunting_proficiency: float = 0.15     # Astúcia na seleção de presas vulneráveis e perseguição (Predadores)
    foraging_efficiency: float = 0.15     # Discernimento e persistência na localização de alimento

    def improve(self, skill: str, delta: float) -> None:
        """Aprimora uma habilidade tática com retornos decrescentes."""
        current = getattr(self, skill, 0.15)
        new_val = min(0.95, current + delta * (1.0 - current))
        setattr(self, skill, new_val)

    def to_dict(self) -> Dict[str, float]:
        return {
            "evasion_proficiency": round(self.evasion_proficiency, 2),
            "mobbing_coordination": round(self.mobbing_coordination, 2),
            "hunting_proficiency": round(self.hunting_proficiency, 2),
            "foraging_efficiency": round(self.foraging_efficiency, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TacticalSkills:
        return cls(
            evasion_proficiency=float(data.get("evasion_proficiency", 0.15)),
            mobbing_coordination=float(data.get("mobbing_coordination", 0.15)),
            hunting_proficiency=float(data.get("hunting_proficiency", 0.15)),
            foraging_efficiency=float(data.get("foraging_efficiency", 0.15)),
        )


@dataclass
class AnimalKnowledge:
    """
    Estrutura de Conhecimento Cognitivo Individual.
    Distingue-se explicitamente de:
      1. Memória Episódica (registros de acontecimentos históricos pontuais)
      2. Genética (código bialélico hereditário, estritamente inalterado por aprendizado).
    """

    food_hotspots: List[FoodHotspot] = field(default_factory=list)
    danger_hotspots: List[DangerHotspot] = field(default_factory=list)
    known_threats: Dict[int, ThreatProfile] = field(default_factory=dict)
    tactical_skills: TacticalSkills = field(default_factory=TacticalSkills)
    experience_points: float = 0.0
    social_transmissions_received: int = 0
    social_transmissions_given: int = 0
    mentor_id: Optional[int] = None
    max_food_hotspots: int = 4
    max_danger_hotspots: int = 4
    max_threats: int = 6

    def reinforce_food_spot(
        self,
        x: float,
        y: float,
        tick: int,
        learning_rate: float = 0.25,
        discovered_via: str = "EXPERIENCIA",
    ) -> FoodHotspot:
        """Consolida conhecimento sobre um sítio de alimentação."""
        self.experience_points += 2.5
        for spot in self.food_hotspots:
            if math.hypot(spot.x - x, spot.y - y) <= 45.0:
                spot.reinforce(tick, learning_rate)
                self.tactical_skills.improve("foraging_efficiency", 0.04)
                return spot

        # Novo sítio descoberto
        init_conf = 0.40 if discovered_via == "EXPERIENCIA" else 0.25
        new_spot = FoodHotspot(
            x=round(x, 1),
            y=round(y, 1),
            confidence=init_conf,
            success_count=1,
            failure_count=0,
            last_visited_tick=tick,
            discovered_via=discovered_via,
        )
        self.food_hotspots.append(new_spot)
        self.tactical_skills.improve("foraging_efficiency", 0.05)

        # Compactação mantendo os sítios com maior confiança
        if len(self.food_hotspots) > self.max_food_hotspots:
            self.food_hotspots.sort(key=lambda s: s.confidence, reverse=True)
            self.food_hotspots = self.food_hotspots[:self.max_food_hotspots]

        return new_spot

    def penalize_food_spot(self, x: float, y: float, tick: int, penalty_rate: float = 0.30) -> None:
        """Penaliza sítio visitado que se encontra esgotado (extinção de crença desatualizada)."""
        for spot in self.food_hotspots:
            if math.hypot(spot.x - x, spot.y - y) <= 40.0:
                spot.penalize(tick, penalty_rate)
                break

        # Remove sítios cuja confiança caiu abaixo do limiar crítico de relevância
        self.food_hotspots = [s for s in self.food_hotspots if s.confidence >= 0.12]

    def reinforce_danger_spot(
        self,
        x: float,
        y: float,
        tick: int,
        intensity: float = 0.50,
        threat_type: str = "PREDACAO",
        discovered_via: str = "EXPERIENCIA",
    ) -> DangerHotspot:
        """Consolida percepção de perigo em uma área perigosa."""
        self.experience_points += 3.0
        for spot in self.danger_hotspots:
            if math.hypot(spot.x - x, spot.y - y) <= 50.0:
                spot.reinforce(tick, intensity)
                return spot

        init_danger = min(0.85, 0.40 + intensity * 0.30)
        new_spot = DangerHotspot(
            x=round(x, 1),
            y=round(y, 1),
            danger_level=init_danger,
            incident_count=1,
            threat_type=threat_type,
            last_incident_tick=tick,
            discovered_via=discovered_via,
        )
        self.danger_hotspots.append(new_spot)

        if len(self.danger_hotspots) > self.max_danger_hotspots:
            self.danger_hotspots.sort(key=lambda s: s.danger_level, reverse=True)
            self.danger_hotspots = self.danger_hotspots[:self.max_danger_hotspots]

        return new_spot

    def register_threat(self, target_id: int, target_name: str, tick: int, delta: float = 0.30) -> None:
        """Reconhece e memoriza um indivíduo ameaçador específico."""
        self.experience_points += 1.5
        if target_id in self.known_threats:
            self.known_threats[target_id].reinforce(tick, delta)
        else:
            self.known_threats[target_id] = ThreatProfile(
                target_id=target_id,
                target_name=target_name,
                threat_score=min(1.0, 0.40 + delta),
                encounters=1,
                last_seen_tick=tick,
            )

        if len(self.known_threats) > self.max_threats:
            # Mantém os de maior periculosidade
            sorted_items = sorted(self.known_threats.items(), key=lambda item: item[1].threat_score, reverse=True)
            self.known_threats = dict(sorted_items[:self.max_threats])

    def get_threat(self, target_id: int) -> Optional[ThreatProfile]:
        """Recupera o perfil cognitivo de uma ameaça conhecida."""
        return self.known_threats.get(target_id)

    def get_threat_score(self, target_id: int) -> float:
        """Retorna o nível de ameaça cognitiva atribuído a um indivíduo."""
        if target_id in self.known_threats:
            return self.known_threats[target_id].threat_score
        return 0.0

    def record_threat(self, target_id: int, target_name: str, delta: float = 0.30, tick: int = 0) -> None:
        """Alias para registrar ameaça específica."""
        self.register_threat(target_id, target_name, tick, delta)

    def record_danger(
        self,
        x: float,
        y: float,
        threat_type: str = "PREDACAO",
        danger_level: float = 0.50,
        tick: int = 0,
    ) -> DangerHotspot:
        """Alias para registrar hotspot de perigo."""
        return self.reinforce_danger_spot(x, y, tick, intensity=danger_level, threat_type=threat_type)

    def record_food(self, x: float, y: float, tick: int = 0, learning_rate: float = 0.25) -> FoodHotspot:
        """Alias para registrar hotspot de alimentação."""
        return self.reinforce_food_spot(x, y, tick, learning_rate=learning_rate)

    def add_xp(self, amount: float) -> None:
        """Acrescenta pontos de experiência empírica ao animal."""
        self.experience_points += amount

    def decay_all(self, current_tick: int) -> None:
        """Aplica decaimento temporal suave em sítios não reforçados."""
        for spot in self.food_hotspots:
            spot.decay(current_tick)
        self.food_hotspots = [s for s in self.food_hotspots if s.confidence >= 0.10]

        for danger in self.danger_hotspots:
            danger.decay(current_tick)
        self.danger_hotspots = [d for d in self.danger_hotspots if d.danger_level >= 0.10]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "food_hotspots": [s.to_dict() for s in self.food_hotspots],
            "danger_hotspots": [d.to_dict() for d in self.danger_hotspots],
            "known_threats": [t.to_dict() for t in self.known_threats.values()],
            "tactical_skills": self.tactical_skills.to_dict(),
            "experience_points": round(self.experience_points, 1),
            "social_transmissions_received": self.social_transmissions_received,
            "social_transmissions_given": self.social_transmissions_given,
            "mentor_id": self.mentor_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnimalKnowledge:
        k = cls()
        k.food_hotspots = [FoodHotspot.from_dict(s) for s in data.get("food_hotspots", [])]
        k.danger_hotspots = [DangerHotspot.from_dict(d) for d in data.get("danger_hotspots", [])]
        k.known_threats = {
            int(t["target_id"]): ThreatProfile.from_dict(t)
            for t in data.get("known_threats", [])
        }
        k.tactical_skills = TacticalSkills.from_dict(data.get("tactical_skills", {}))
        k.experience_points = float(data.get("experience_points", 0.0))
        k.social_transmissions_received = int(data.get("social_transmissions_received", 0))
        k.social_transmissions_given = int(data.get("social_transmissions_given", 0))
        k.mentor_id = data.get("mentor_id")
        return k
