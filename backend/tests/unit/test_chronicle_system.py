"""Testes unitários e de integração da Crônica Histórica do Ecossistema."""

import pytest
from core.world import World
from core.entities.chronicle import EcosystemChronicle, ChronicleEvent, ChronicleEventType
from core.entities.organism import Organism


def test_chronicle_initialization_and_genesis():
    """Garante que a inicialização do mundo cria registros factuais pioneiros e não inventa eventos."""
    world = World(seed=123, initial_organisms=20, initial_food=30)
    
    assert world.chronicle is not None
    assert len(world.chronicle._events) == 20
    
    # Todos os eventos iniciais são de nascimento/gênese pioneira
    for ev in world.chronicle._events:
        assert ev.event_type == ChronicleEventType.BIRTH.value
        assert "Gênese Ancestral" in ev.title
        assert ev.tick == 0
        assert ev.primary_organism_id in world.organisms
        assert ev.species in (Organism.SPECIES_PREDATOR, Organism.SPECIES_VRANCO)
        assert ev.importance == 2


def test_no_fictitious_events_recorded():
    """Garante que eventos fictícios não são inseridos."""
    chronicle = EcosystemChronicle()
    ev = chronicle.record_event(
        event_type=ChronicleEventType.BIRTH.value,
        title="Nascimento Real",
        description="Animal #1 nasceu na Geração 1",
        tick=10,
        cause="Reprodução biológica",
        result="Aumento populacional",
        primary_organism_id=1,
    )
    assert ev.id == 1
    assert ev.title == "Nascimento Real"
    assert ev.cause == "Reprodução biológica"
    
    # Eventos de outros tipos não ocorridos não devem existir
    wars = chronicle.query_timeline(event_type=ChronicleEventType.WAR_DECLARED.value)
    assert wars["total"] == 0
    assert len(wars["events"]) == 0


def test_chronological_ordering_and_filtering():
    """Verifica que a cronologia permanece rigorosamente ordenada e suporta filtros."""
    chronicle = EcosystemChronicle()
    
    # Registra eventos em ordem cronológica
    chronicle.record_event(
        event_type=ChronicleEventType.BIRTH.value,
        title="Nascimento de Alfa",
        description="Predador Alfa nasceu",
        tick=10,
        cause="Reprodução",
        result="Vida iniciada",
        species=Organism.SPECIES_PREDATOR,
        primary_organism_id=101,
        importance=2,
    )
    chronicle.record_event(
        event_type=ChronicleEventType.LEADERSHIP_ELECTED.value,
        title="Eleição de Alfa",
        description="Alfa eleito",
        tick=50,
        cause="Eleição",
        result="Liderança assumida",
        clan_id=1,
        clan_name="Clã das Sombras",
        primary_organism_id=101,
        importance=4,
    )
    chronicle.record_event(
        event_type=ChronicleEventType.DEATH.value,
        title="Morte de Alfa",
        description="Alfa faleceu aos 200 ciclos",
        tick=200,
        cause="Senescência",
        result="Morte",
        clan_id=1,
        clan_name="Clã das Sombras",
        primary_organism_id=101,
        importance=4,
    )

    # 1. Consulta geral ordenada decrescente por padrão (mais recentes primeiro)
    res_desc = chronicle.query_timeline(limit=10)
    assert res_desc["total"] == 3
    assert [e["tick"] for e in res_desc["events"]] == [200, 50, 10]

    # 2. Filtro por espécie
    res_pred = chronicle.query_timeline(species=Organism.SPECIES_PREDATOR)
    assert res_pred["total"] == 1
    assert res_pred["events"][0]["primary_organism_id"] == 101

    # 3. Filtro por clã
    res_clan = chronicle.query_timeline(clan_id=1)
    assert res_clan["total"] == 2

    # 4. Filtro por importância mínima
    res_imp = chronicle.query_timeline(min_importance=3)
    assert res_imp["total"] == 2

    # 5. Busca textual
    res_search = chronicle.query_timeline(search="Eleição")
    assert res_search["total"] == 1
    assert res_search["events"][0]["event_type"] == ChronicleEventType.LEADERSHIP_ELECTED.value


def test_causal_linking_between_events():
    """Verifica encadeamento de causalidade factual entre eventos correlatos."""
    chronicle = EcosystemChronicle()
    
    # Evento precursor: declaração de guerra
    war_ev = chronicle.record_event(
        event_type=ChronicleEventType.WAR_DECLARED.value,
        title="Guerra de Fronteira",
        description="Clã A declarou guerra contra Clã B",
        tick=100,
        cause="Disputa territorial",
        result="Hostilidade aberta",
        importance=4,
        metadata={"clan1": "Clã A", "clan2": "Clã B"},
    )

    # Evento resultante: trégua com vínculo causal
    truce_ev = chronicle.record_event(
        event_type=ChronicleEventType.TRUCE_SIGNED.value,
        title="Trégua Firmada",
        description="Clã A e Clã B assinaram armistício",
        tick=180,
        cause="Exaustão de suprimentos e baixas",
        result="Cessar-fogo",
        importance=4,
        related_event_ids=[war_ev.id],
        metadata={"clan1": "Clã A", "clan2": "Clã B"},
    )

    # Verifica resolução de referências causais
    related = chronicle.get_related_events(truce_ev.id)
    assert len(related) == 1
    assert related[0].id == war_ev.id
    assert related[0].event_type == ChronicleEventType.WAR_DECLARED.value


def test_organism_and_clan_history_queries():
    """Valida consulta de biografia individual e crônica do clã."""
    chronicle = EcosystemChronicle()
    
    chronicle.record_event(
        event_type=ChronicleEventType.BIRTH.value,
        title="Nascimento de V-1",
        description="Filhote de Vranco nasceu",
        tick=5,
        cause="Reprodução",
        result="Vida iniciada",
        primary_organism_id=42,
        primary_organism_name="V-1",
        clan_id=5,
    )
    chronicle.record_event(
        event_type=ChronicleEventType.MOBBING_DEFENSE.value,
        title="Defesa de Bando",
        description="V-1 participou da defesa contra predador",
        tick=40,
        cause="Ataque de predador",
        result="Predador repelido",
        involved_organism_ids=[42, 43],
        clan_id=5,
    )
    chronicle.record_event(
        event_type=ChronicleEventType.DEATH.value,
        title="Morte de V-1",
        description="V-1 faleceu em confronto",
        tick=120,
        cause="Predação",
        result="Falecimento",
        primary_organism_id=42,
        primary_organism_name="V-1",
        clan_id=5,
    )

    # Biografia do organismo 42
    bio = chronicle.get_organism_history(42)
    assert len(bio) == 3
    assert bio[0]["event_type"] == ChronicleEventType.BIRTH.value
    assert bio[2]["event_type"] == ChronicleEventType.DEATH.value

    # Anais do clã 5
    clan_hist = chronicle.get_clan_history(5)
    assert len(clan_hist) == 3


def test_chronicle_compaction_preserves_milestones():
    """Garante que a compactação preserva eventos de alta importância (>= 3) sem perdas genealógicas."""
    chronicle = EcosystemChronicle(max_events=10)
    
    # Insere 15 eventos de baixa importância
    for i in range(15):
        chronicle.record_event(
            event_type=ChronicleEventType.COMBAT_ENGAGEMENT.value,
            title=f"Escaramuça #{i}",
            description="Troca de golpes menor",
            tick=i * 2,
            cause="Atrito territorial",
            result="Ferimento leve",
            importance=2,
        )
    
    # Insere um evento de marco histórico maior (importância 4)
    chronicle.record_event(
        event_type=ChronicleEventType.CLAN_FOUNDED.value,
        title="Fundação do Grande Clã",
        description="Clã supremo unificado",
        tick=35,
        cause="Aliança mútua",
        result="Novo clã",
        importance=4,
    )

    # Como max_events=10, a crônica compactou
    assert len(chronicle._events) <= 10
    
    # O marco histórico de importância 4 DEVE continuar presente
    milestone_found = any(e.event_type == ChronicleEventType.CLAN_FOUNDED.value for e in chronicle._events)
    assert milestone_found


def test_chronicle_snapshot_persistence():
    """Verifica que o estado completo da crônica é perfeitamente preservado em snapshots."""
    world = World(seed=42, initial_organisms=10, initial_food=20)
    
    # Simula 5 passos para gerar eventos ambientais e metabólicos
    for _ in range(5):
        world.step()
        
    initial_event_count = len(world.chronicle._events)
    assert initial_event_count >= 10
    
    # Salva snapshot
    snapshot = world.to_snapshot()
    assert "chronicle" in snapshot
    assert snapshot["chronicle"]["event_count"] == initial_event_count
    
    # Restaura novo mundo a partir do snapshot
    restored_world = World.from_snapshot(snapshot)
    assert len(restored_world.chronicle._events) == initial_event_count
    assert restored_world.chronicle._next_event_id == world.chronicle._next_event_id
    
    # Verifica que as consultas continuam funcionando exatamente iguais
    q1 = world.chronicle.query_timeline()
    q2 = restored_world.chronicle.query_timeline()
    assert q1["total"] == q2["total"]
    assert len(q1["events"]) == len(q2["events"])
    assert q1["events"][0]["title"] == q2["events"][0]["title"]
