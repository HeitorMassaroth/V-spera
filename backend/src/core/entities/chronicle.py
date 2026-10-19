"""Modelo centralizado da Crônica Histórica do Ecossistema (Ecosystem Chronicle).

Transforma acontecimentos reais e verificados da simulação em um registro histórico
consultável, causalmente articulado e integrado à árvore genealógica, clãs e territórios.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple


class ChronicleEventType(str, Enum):
    """Categorias factuais de acontecimentos marcantes da simulação."""
    BIRTH = "BIRTH"                                 # Nascimento com herança e filiação
    DEATH = "DEATH"                                 # Morte com causa apurada e registros de combate
    CLAN_FOUNDED = "CLAN_FOUNDED"                   # Fundação espontânea de clã
    CLAN_STAGE_CHANGE = "CLAN_STAGE_CHANGE"         # Evolução social (Ocasional -> Recorrente -> Estabelecido)
    CLAN_DISBANDED = "CLAN_DISBANDED"               # Dissolução de clã por extinção de famílias ou dispersão
    CLAN_SPLIT = "CLAN_SPLIT"                       # Divisão do grupo ou expulsão de membros dissidentes
    LEADERSHIP_ELECTED = "LEADERSHIP_ELECTED"       # Eleição de Alfa / Beta por mérito e aprovação
    LEADERSHIP_DEPOSED = "LEADERSHIP_DEPOSED"       # Queda de líder por crise de legitimidade
    LEADERSHIP_SUCCESSION = "LEADERSHIP_SUCCESSION" # Sucessão ordenada após morte de Alfa/Beta anterior
    TERRITORY_CLAIMED = "TERRITORY_CLAIMED"         # Ocupação ou assentamento de território
    TERRITORY_CONTESTED = "TERRITORY_CONTESTED"     # Disputa por recursos com bando rival
    TERRITORY_LOST = "TERRITORY_LOST"               # Perda de território após escassez ou derrotas
    MIGRATION = "MIGRATION"                         # Migração motivada por escassez de biomassa ou perigo
    COMBAT_ENGAGEMENT = "COMBAT_ENGAGEMENT"         # Confronto violento ou defesa territorial
    MOBBING_DEFENSE = "MOBBING_DEFENSE"             # Defesa coletiva bem-sucedida de Vrancos contra predadores
    WAR_DECLARED = "WAR_DECLARED"                   # Eclosão de guerra diplomática entre clãs
    TRUCE_SIGNED = "TRUCE_SIGNED"                   # Acordo de cessar-fogo ou trégua
    ENVIRONMENTAL_SEASON = "ENVIRONMENTAL_SEASON"   # Mudança climática de estação do ano
    SPECIES_CRISIS = "SPECIES_CRISIS"               # Alerta de perigo de extinção de espécie
    SPECIES_EXTINCTION = "SPECIES_EXTINCTION"       # Extinção biológica confirmada
    LINEAGE_PROMINENCE = "LINEAGE_PROMINENCE"       # Linhagem atinge marco dinástico marcante
    CULTURAL_LOSS = "CULTURAL_LOSS"                 # Perda cultural pela morte de sábio sem herdeiros do saber


@dataclass
class ChronicleEvent:
    """Registro histórico imutável de um evento real ocorrido no mundo."""

    id: int
    tick: int
    year: int
    event_type: str
    title: str
    description: str
    cause: str
    result: str
    importance: int = 3                                 # 1 (menor) a 5 (cataclísmico/histórico maior)
    location: Optional[Tuple[float, float]] = None
    zone_id: Optional[int] = None
    zone_name: Optional[str] = None
    primary_organism_id: Optional[int] = None
    primary_organism_name: Optional[str] = None
    secondary_organism_id: Optional[int] = None
    secondary_organism_name: Optional[str] = None
    involved_organism_ids: List[int] = field(default_factory=list)
    clan_id: Optional[int] = None
    clan_name: Optional[str] = None
    secondary_clan_id: Optional[int] = None
    secondary_clan_name: Optional[str] = None
    species: Optional[str] = None                       # 'VRANCO', 'PREDATOR', 'MISTA'
    related_event_ids: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialização estruturada do evento histórico."""
        return {
            "id": self.id,
            "tick": self.tick,
            "year": self.year,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "cause": self.cause,
            "result": self.result,
            "importance": self.importance,
            "location": [round(self.location[0], 1), round(self.location[1], 1)] if self.location else None,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "primary_organism_id": self.primary_organism_id,
            "primary_organism_name": self.primary_organism_name,
            "secondary_organism_id": self.secondary_organism_id,
            "secondary_organism_name": self.secondary_organism_name,
            "involved_organism_ids": self.involved_organism_ids,
            "clan_id": self.clan_id,
            "clan_name": self.clan_name,
            "secondary_clan_id": self.secondary_clan_id,
            "secondary_clan_name": self.secondary_clan_name,
            "species": self.species,
            "related_event_ids": self.related_event_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChronicleEvent:
        """Desserializa registro histórico."""
        loc = None
        if data.get("location") and len(data["location"]) >= 2:
            loc = (float(data["location"][0]), float(data["location"][1]))

        return cls(
            id=int(data["id"]),
            tick=int(data["tick"]),
            year=int(data.get("year", data["tick"] // 500 + 1)),
            event_type=str(data["event_type"]),
            title=str(data["title"]),
            description=str(data["description"]),
            cause=str(data.get("cause", "Causa desconhecida")),
            result=str(data.get("result", "")),
            importance=int(data.get("importance", 3)),
            location=loc,
            zone_id=data.get("zone_id"),
            zone_name=data.get("zone_name"),
            primary_organism_id=data.get("primary_organism_id"),
            primary_organism_name=data.get("primary_organism_name"),
            secondary_organism_id=data.get("secondary_organism_id"),
            secondary_organism_name=data.get("secondary_organism_name"),
            involved_organism_ids=data.get("involved_organism_ids", []),
            clan_id=data.get("clan_id"),
            clan_name=data.get("clan_name"),
            secondary_clan_id=data.get("secondary_clan_id"),
            secondary_clan_name=data.get("secondary_clan_name"),
            species=data.get("species"),
            related_event_ids=data.get("related_event_ids", []),
            metadata=data.get("metadata", {}),
        )


class EcosystemChronicle:
    """
    Gerenciador e índice central da Crônica Histórica do Ecossistema.
    
    Mantém o histórico causal e ordenado, provendo busca eficiente O(1) e O(log N),
    navegação de causa e efeito, e limites de armazenamento para evitar vazamento de memória.
    """

    def __init__(self, max_events: int = 1500, ticks_per_year: int = 500) -> None:
        self.max_events = max_events
        self.ticks_per_year = ticks_per_year
        self._next_event_id: int = 1

        # Repositório primário ordenado por ID/Tick
        self._events: List[ChronicleEvent] = []
        self._event_map: Dict[int, ChronicleEvent] = {}

        # Índices espaciais e relacionais para consultas velozes
        self._by_organism: Dict[int, List[int]] = {}
        self._by_clan: Dict[int, List[int]] = {}
        self._by_zone: Dict[int, List[int]] = {}
        self._by_type: Dict[str, List[int]] = {}

    def tick_to_year(self, tick: int) -> int:
        """Converte ciclo da simulação em contagem anual do ecossistema."""
        return max(1, (tick // self.ticks_per_year) + 1)

    def record_event(
        self,
        event_type: str,
        title: str,
        description: str,
        tick: int,
        cause: str = "Causa desconhecida",
        result: str = "",
        importance: int = 3,
        location: Optional[Tuple[float, float]] = None,
        zone_id: Optional[int] = None,
        zone_name: Optional[str] = None,
        primary_organism_id: Optional[int] = None,
        primary_organism_name: Optional[str] = None,
        secondary_organism_id: Optional[int] = None,
        secondary_organism_name: Optional[str] = None,
        involved_organism_ids: Optional[List[int]] = None,
        clan_id: Optional[int] = None,
        clan_name: Optional[str] = None,
        secondary_clan_id: Optional[int] = None,
        secondary_clan_name: Optional[str] = None,
        species: Optional[str] = None,
        related_event_ids: Optional[List[int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChronicleEvent:
        """Registra um acontecimento concreto e verificado na crônica."""
        event_id = self._next_event_id
        self._next_event_id += 1

        all_involved = list(involved_organism_ids or [])
        if primary_organism_id is not None and primary_organism_id not in all_involved:
            all_involved.append(primary_organism_id)
        if secondary_organism_id is not None and secondary_organism_id not in all_involved:
            all_involved.append(secondary_organism_id)

        event = ChronicleEvent(
            id=event_id,
            tick=tick,
            year=self.tick_to_year(tick),
            event_type=event_type,
            title=title,
            description=description,
            cause=cause,
            result=result,
            importance=importance,
            location=location,
            zone_id=zone_id,
            zone_name=zone_name,
            primary_organism_id=primary_organism_id,
            primary_organism_name=primary_organism_name,
            secondary_organism_id=secondary_organism_id,
            secondary_organism_name=secondary_organism_name,
            involved_organism_ids=all_involved,
            clan_id=clan_id,
            clan_name=clan_name,
            secondary_clan_id=secondary_clan_id,
            secondary_clan_name=secondary_clan_name,
            species=species,
            related_event_ids=list(related_event_ids or []),
            metadata=metadata or {},
        )

        self._events.append(event)
        self._event_map[event_id] = event

        # Atualiza índices
        for org_id in all_involved:
            if org_id not in self._by_organism:
                self._by_organism[org_id] = []
            self._by_organism[org_id].append(event_id)

        if clan_id is not None:
            if clan_id not in self._by_clan:
                self._by_clan[clan_id] = []
            self._by_clan[clan_id].append(event_id)

        if secondary_clan_id is not None:
            if secondary_clan_id not in self._by_clan:
                self._by_clan[secondary_clan_id] = []
            self._by_clan[secondary_clan_id].append(event_id)

        if zone_id is not None:
            if zone_id not in self._by_zone:
                self._by_zone[zone_id] = []
            self._by_zone[zone_id].append(event_id)

        if event_type not in self._by_type:
            self._by_type[event_type] = []
        self._by_type[event_type].append(event_id)

        # Compactação controlada se o limite for ultrapassado
        if len(self._events) > self.max_events:
            self._compact_history()

        return event

    def _compact_history(self) -> None:
        """
        Compacta eventos arquiváveis mantendo a fidelidade histórica:
        - Preserva TODOS os eventos de importância >= 3 (mudanças de clã, guerras, mortes notáveis, extinções).
        - Descarte de eventos rotineiros mais antigos (nascimentos comuns antigos ou combates menores).
        """
        target_size = self.max_events
        critical_events: List[ChronicleEvent] = []
        routine_events: List[ChronicleEvent] = []

        for ev in self._events:
            if ev.importance >= 3:
                critical_events.append(ev)
            else:
                routine_events.append(ev)

        # Mantém os rotineiros mais recentes
        allowed_routine = max(0, target_size - len(critical_events))
        if len(routine_events) > allowed_routine:
            routine_events = routine_events[-allowed_routine:] if allowed_routine > 0 else []

        new_events = sorted(critical_events + routine_events, key=lambda e: e.id)
        if len(new_events) > target_size:
            new_events = new_events[-target_size:]

        self._events = new_events
        self._event_map = {e.id: e for e in self._events}

        # Reconstrói índices com os eventos mantidos
        self._rebuild_indices()

    def _rebuild_indices(self) -> None:
        """Reconstrói os índices relacionais a partir da lista ativa de eventos."""
        self._by_organism.clear()
        self._by_clan.clear()
        self._by_zone.clear()
        self._by_type.clear()

        for ev in self._events:
            for org_id in ev.involved_organism_ids:
                if org_id not in self._by_organism:
                    self._by_organism[org_id] = []
                self._by_organism[org_id].append(ev.id)

            if ev.clan_id is not None:
                if ev.clan_id not in self._by_clan:
                    self._by_clan[ev.clan_id] = []
                self._by_clan[ev.clan_id].append(ev.id)

            if ev.secondary_clan_id is not None:
                if ev.secondary_clan_id not in self._by_clan:
                    self._by_clan[ev.secondary_clan_id] = []
                self._by_clan[ev.secondary_clan_id].append(ev.id)

            if ev.zone_id is not None:
                if ev.zone_id not in self._by_zone:
                    self._by_zone[ev.zone_id] = []
                self._by_zone[ev.zone_id].append(ev.id)

            if ev.event_type not in self._by_type:
                self._by_type[ev.event_type] = []
            self._by_type[ev.event_type].append(ev.id)

    def get_event(self, event_id: int) -> Optional[ChronicleEvent]:
        """Obtém um evento específico por ID."""
        return self._event_map.get(event_id)

    def get_event_by_id(self, event_id: int) -> Optional[ChronicleEvent]:
        """Alias para get_event."""
        return self.get_event(event_id)

    def get_related_events(self, event_id: int) -> List[ChronicleEvent]:
        """Recupera a árvore causal de eventos relacionados a um acontecimento."""
        event = self.get_event(event_id)
        if not event or not event.related_event_ids:
            return []

        resolved: List[ChronicleEvent] = []
        for rel_id in event.related_event_ids:
            rel_ev = self.get_event(rel_id)
            if rel_ev:
                resolved.append(rel_ev)
        return resolved

    def find_recent_events_in_zone(self, zone_id: int, since_tick: int) -> List[ChronicleEvent]:
        """Busca eventos recentes em uma zona territorial para dedução causal."""
        event_ids = self._by_zone.get(zone_id, [])
        matches = []
        for eid in reversed(event_ids):
            ev = self._event_map.get(eid)
            if ev and ev.tick >= since_tick:
                matches.append(ev)
            elif ev and ev.tick < since_tick:
                break
        return matches

    def find_recent_clan_conflicts(self, clan_id: int, since_tick: int) -> List[ChronicleEvent]:
        """Busca confrontos recentes envolvendo um clã para nexo causal."""
        event_ids = self._by_clan.get(clan_id, [])
        matches = []
        for eid in reversed(event_ids):
            ev = self._event_map.get(eid)
            if ev and ev.tick >= since_tick and ev.event_type in (
                ChronicleEventType.COMBAT_ENGAGEMENT,
                ChronicleEventType.MOBBING_DEFENSE,
                ChronicleEventType.WAR_DECLARED,
                ChronicleEventType.TERRITORY_CONTESTED,
            ):
                matches.append(ev)
        return matches

    def get_organism_history(self, organism_id: int) -> List[Dict[str, Any]]:
        """Gera a biografia cronológica completa de um indivíduo específico."""
        event_ids = self._by_organism.get(organism_id, [])
        history = []
        for eid in event_ids:
            ev = self._event_map.get(eid)
            if ev:
                history.append(ev.to_dict())
        return history

    def get_clan_history(self, clan_id: int) -> List[Dict[str, Any]]:
        """Gera os anais históricos completos de um clã específico."""
        event_ids = self._by_clan.get(clan_id, [])
        history = []
        for eid in event_ids:
            ev = self._event_map.get(eid)
            if ev:
                history.append(ev.to_dict())
        return history

    def query_timeline(
        self,
        species: Optional[str] = None,
        organism_id: Optional[int] = None,
        clan_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        event_type: Optional[str] = None,
        min_importance: int = 1,
        search: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Consulta filtrada e paginada da linha do tempo histórica com ordenação cronológica reversa.
        """
        # Candidatos iniciais
        if organism_id is not None:
            candidate_ids = self._by_organism.get(organism_id, [])
        elif clan_id is not None:
            candidate_ids = self._by_clan.get(clan_id, [])
        elif zone_id is not None:
            candidate_ids = self._by_zone.get(zone_id, [])
        elif event_type is not None:
            candidate_ids = self._by_type.get(event_type, [])
        else:
            candidate_ids = [e.id for e in self._events]

        term = search or search_query
        search_lower = term.lower().strip() if term else None

        filtered: List[ChronicleEvent] = []
        # Itera em ordem reversa (mais recentes primeiro)
        for eid in reversed(candidate_ids):
            ev = self._event_map.get(eid)
            if not ev:
                continue

            if ev.importance < min_importance:
                continue

            if species is not None:
                if ev.species is None or (ev.species != species and ev.species != "MISTA"):
                    continue

            if event_type is not None and ev.event_type != event_type:
                continue

            if clan_id is not None and ev.clan_id != clan_id and ev.secondary_clan_id != clan_id:
                continue

            if zone_id is not None and ev.zone_id != zone_id:
                continue

            if search_lower:
                text_corpus = f"{ev.title} {ev.description} {ev.cause} {ev.result} {ev.primary_organism_name or ''} {ev.secondary_organism_name or ''} {ev.clan_name or ''} {ev.zone_name or ''}".lower()
                if search_lower not in text_corpus:
                    continue

            filtered.append(ev)

        total_count = len(filtered)
        paginated = filtered[offset : offset + limit]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "events": [e.to_dict() for e in paginated],
        }

    def get_recent_summary(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retorna os eventos mais recentes para transmissão compacta no WebSocket."""
        return [e.to_dict() for e in self._events[-limit:]]

    def to_snapshot(self) -> Dict[str, Any]:
        """Serializa o estado integral da crônica para checkpoint."""
        return {
            "next_event_id": self._next_event_id,
            "ticks_per_year": self.ticks_per_year,
            "max_events": self.max_events,
            "event_count": len(self._events),
            "events": [e.to_dict() for e in self._events],
        }

    def load_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Carrega e reconstrói o estado histórico a partir de um dicionário snapshot."""
        self.max_events = snapshot.get("max_events", self.max_events)
        self.ticks_per_year = snapshot.get("ticks_per_year", self.ticks_per_year)
        self._next_event_id = snapshot.get("next_event_id", 1)
        self._events = [ChronicleEvent.from_dict(d) for d in snapshot.get("events", [])]
        self._event_map = {e.id: e for e in self._events}
        self._rebuild_indices()

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> EcosystemChronicle:
        """Restaura a crônica a partir de um checkpoint salvo."""
        chronicle = cls(
            max_events=snapshot.get("max_events", 1500),
            ticks_per_year=snapshot.get("ticks_per_year", 500),
        )
        chronicle.load_from_snapshot(snapshot)
        return chronicle
