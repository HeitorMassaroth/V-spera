"""Testes unitários e comportamentais para o Sistema de Territórios e Disputa por Recursos."""

import pytest
import math
from src.core.world import World
from src.core.prng import PRNG
from src.core.entities.organism import Organism
from src.core.entities.food import Food
from src.core.entities.territory import TerritoryZone
from src.core.entities.genetics import Genotype
from src.core.entities.clan import Clan, ClanRelation, ClanSocialStage
from src.core.systems.territory_system import TerritorySystem
from src.core.systems.movement import MovementSystem


def test_territory_initialization():
    """Valida a criação e distribuição espacial inicial das 8 regiões estratégicas."""
    clusters = [(300.0, 200.0), (900.0, 200.0), (300.0, 600.0), (900.0, 600.0)]
    prng = PRNG(42)
    sys = TerritorySystem(world_width=1200.0, world_height=800.0, food_clusters=clusters, prng=prng)

    assert len(sys.zones) == 8
    central_zones = [z for z in sys.zones.values() if not z.is_peripheral]
    peripheral_zones = [z for z in sys.zones.values() if z.is_peripheral]

    assert len(central_zones) == 4
    assert len(peripheral_zones) == 4

    # Zonas centrais mapeadas nos clusters
    for idx, (cx, cy) in enumerate(clusters, start=1):
        z = sys.zones[idx]
        assert z.x == cx and z.y == cy
        assert z.base_fertility > 1.0


def test_territory_quality_calculation_and_finitude():
    """Valida indicadores de qualidade e o princípio de recursos finitos e degradação."""
    zone = TerritoryZone(
        id=1,
        name="Teste Oásis",
        x=500.0,
        y=400.0,
        radius=100.0,
        base_fertility=1.2,
        current_fertility=1.2,
        carrying_capacity=10,
    )

    # Estado com comida abundante e sem predadores
    zone.food_count = 20
    zone.biomass = 600.0
    zone.predator_count = 0
    zone.vranco_count = 5
    zone.occupant_ids = {1, 2, 3, 4, 5}
    zone.calculate_quality(recent_combat=False)

    high_quality = zone.quality_score
    assert high_quality >= 70.0
    assert zone.food_availability_score >= 0.8
    assert zone.safety_score == 1.0

    # Simula superexploração: recursos esgotados e sobrepopulação (25 ocupantes em capacidade 10)
    zone.food_count = 0
    zone.biomass = 0.0
    zone.occupant_ids = set(range(1, 26))
    zone.predator_count = 4

    # Avança ecologia por vários ciclos com recursos esgotados
    for t in range(1, 40):
        zone.update_resource_ecology(t)

    assert zone.depletion_ticks > 0
    assert zone.current_fertility < zone.base_fertility  # Degradação da fertilidade
    zone.calculate_quality(recent_combat=True)

    degraded_quality = zone.quality_score
    assert degraded_quality < 45.0
    assert zone.competition_pressure > 0.5
    assert zone.status == "DEGRADED"

    # Pousio ecológico: esvaziando a zona para permitir regeneração natural
    zone.occupant_ids.clear()
    zone.food_count = 5
    for t in range(40, 150):
        zone.update_resource_ecology(t)

    assert zone.recovery_ticks > 0
    assert zone.current_fertility > 0.5  # Recuperação progressiva


def test_motivated_abandonment_and_emigration():
    """Testa se indivíduos abandonam regiões degradadas ou com perigo excessivo de predadores."""
    world = World(width=1200.0, height=800.0, seed=123, initial_organisms=0, initial_food=0)

    # Zona 1: Degradada e perigosa
    z1 = world.territory_system.zones[1]
    z1.status = "DEGRADED"
    z1.quality_score = 15.0
    z1.food_count = 0
    z1.predator_count = 5
    z1.safety_score = 0.10

    # Garante que zonas vizinhas tenham boa qualidade para atrair migração
    for zid in range(2, 9):
        world.territory_system.zones[zid].quality_score = 65.0

    # Cria um Vranco saudável na zona 1
    vranco = Organism(
        id=world._next_entity_id(),
        x=z1.x,
        y=z1.y,
        species=Organism.SPECIES_VRANCO,
        energy=30.0,
        saude=60.0,
    )
    vranco.territory_id = z1.id
    world.organisms[vranco.id] = vranco
    z1.occupant_ids = {vranco.id}

    # Avaliação periódica no tick 35
    events = []
    world.territory_system._evaluate_occupancy_and_migrations(
        world.organisms,
        world.family_system.families,
        world.clan_system.clans,
        tick=35,
        events=events,
    )

    # O Vranco deve ter recebido um novo destino de migração e abandonado a zona degradada
    assert vranco.target_migration_zone is not None
    assert vranco.territory_cooldown > 0
    assert vranco.territory_id != z1.id
    assert any(e["type"] == "territory_migration" for e in events)


def test_peaceful_strategic_retreat_in_clan_disputes():
    """Verifica que clãs em desvantagem recuam pacificamente em vez de lutar até o extermínio."""
    clusters = [(400.0, 300.0), (800.0, 300.0)]
    prng = PRNG(99)
    sys = TerritorySystem(world_width=1200.0, world_height=800.0, food_clusters=clusters, prng=prng)

    zone = sys.zones[1]

    # Clã 1: Fraco / Poucos membros
    c1 = Clan(id=1, name="Clã Lobo Menor", alpha_id=10, communal_food=10.0, territory_x=zone.x, territory_y=zone.y)
    m1 = Organism(id=10, x=zone.x, y=zone.y, energy=40.0, saude=40.0, clan_id=1)
    m1.genome = Genotype(forca=30.0)

    # Clã 2: Forte / Dominante
    c2 = Clan(id=2, name="Clã Predadores Apex", alpha_id=20, communal_food=80.0, territory_x=zone.x, territory_y=zone.y)
    m2 = Organism(id=20, x=zone.x, y=zone.y, energy=90.0, saude=100.0, clan_id=2)
    m2.genome = Genotype(forca=85.0)
    m3 = Organism(id=21, x=zone.x, y=zone.y, energy=85.0, saude=95.0, clan_id=2)
    m3.genome = Genotype(forca=80.0)

    organisms = {10: m1, 20: m2, 21: m3}
    clans = {1: c1, 2: c2}
    zone.occupant_ids = {10, 20, 21}

    events = []
    sys._resolve_territory_disputes(organisms, clans, tick=5, events=events)

    # Clã 1 deve ter recuado pacificamente (power_c1 << power_c2)
    retreat_events = [e for e in events if e.get("type") == "clan_peaceful_retreat"]
    assert len(retreat_events) == 1
    assert retreat_events[0]["clan_name"] == c1.name
    assert m1.target_migration_zone is not None
    assert zone.controlling_clan_id == c2.id
    assert zone.status == "SETTLED"


def test_balanced_forces_trigger_contested_zone():
    """Valida que forças equilibradas e hostis colocam a zona em estado CONTESTED."""
    clusters = [(400.0, 300.0)]
    prng = PRNG(77)
    sys = TerritorySystem(world_width=1200.0, world_height=800.0, food_clusters=clusters, prng=prng)

    zone = sys.zones[1]
    c1 = Clan(id=1, name="Clã Alfa", alpha_id=1, territory_x=zone.x, territory_y=zone.y)
    c2 = Clan(id=2, name="Clã Beta", alpha_id=2, territory_x=zone.x, territory_y=zone.y)

    m1 = Organism(id=1, x=zone.x, y=zone.y, energy=80.0, saude=80.0, clan_id=1)
    m1.genome = Genotype(forca=60.0)
    m2 = Organism(id=2, x=zone.x, y=zone.y, energy=80.0, saude=80.0, clan_id=2)
    m2.genome = Genotype(forca=60.0)

    organisms = {1: m1, 2: m2}
    clans = {1: c1, 2: c2}
    zone.occupant_ids = {1, 2}

    events = []
    sys._resolve_territory_disputes(organisms, clans, tick=10, events=events)

    assert zone.status == "CONTESTED"
    assert zone.dispute_ticks > 0


def test_vrancos_peripheral_flexibility_under_starvation():
    """Vrancos preferem a periferia, mas sob inanição podem explorar o centro do mapa."""
    world = World(width=1200.0, height=800.0, seed=42, initial_organisms=0, initial_food=0)

    # 1. Vranco bem alimentado no centro do mapa sofre repulsão radial para a periferia
    vranco_well_fed = Organism(
        id=1,
        x=600.0,
        y=400.0,
        species=Organism.SPECIES_VRANCO,
        energy=85.0,
        saude=100.0,
    )
    p_fx, p_fy = world.movement._seek_periphery(vranco_well_fed)
    # No centro exato (dist_center < 1e-3), gera força para fora
    assert p_fx > 0 or p_fy > 0

    # 2. Vranco faminto (energia < 38.0) tem liberdade de cruzar o interior em busca de comida
    vranco_hungry = Organism(
        id=2,
        x=600.0,
        y=400.0,
        species=Organism.SPECIES_VRANCO,
        energy=25.0,
        saude=80.0,
    )
    p_fx_hungry, p_fy_hungry = world.movement._seek_periphery(vranco_hungry)
    assert p_fx_hungry == 0.0
    assert p_fy_hungry == 0.0


def test_predator_hunting_and_abandoning_empty_territories():
    """Predadores solitários sem presas locais avaliam e abandonam zonas infrutíferas."""
    world = World(width=1200.0, height=800.0, seed=55, initial_organisms=0, initial_food=0)
    z1 = world.territory_system.zones[1]

    # Predador na zona 1 sem nenhum Vranco ou alimento por perto
    predator = Organism(
        id=1,
        x=z1.x,
        y=z1.y,
        species=Organism.SPECIES_PREDATOR,
        energy=40.0,
        saude=90.0,
    )
    predator.territory_id = z1.id
    predator.territory_cooldown = 0
    world.organisms[1] = predator
    z1.occupant_ids = {1}
    z1.food_count = 0
    z1.vranco_count = 0

    # Zonas vizinhas férteis
    for zid in range(2, 9):
        world.territory_system.zones[zid].quality_score = 70.0

    events = []
    world.territory_system._evaluate_occupancy_and_migrations(
        world.organisms,
        world.family_system.families,
        world.clan_system.clans,
        tick=35,
        events=events,
    )

    # Predador deve ter decidido migrar para zona com maior potencial
    assert predator.target_migration_zone is not None
    assert predator.territory_cooldown > 0
    assert any(e["type"] == "predator_forage_migration" for e in events)


def test_nomadic_and_expelled_organisms_without_fixed_territory():
    """Garante que organismos podem ser nômades sem pertencer a um território fixo."""
    world = World(width=1200.0, height=800.0, seed=77, initial_organisms=0, initial_food=0)

    # Organismo isolado em coordenadas entre zonas
    nomad = Organism(
        id=999,
        x=600.0,
        y=150.0,
        species=Organism.SPECIES_PREDATOR,
        energy=60.0,
    )
    nomad.territory_id = None
    world.organisms[999] = nomad

    # Executa o ciclo do mundo
    world.step()

    # O nômade consegue se mover e sobreviver normalmente sem território obrigatório
    assert nomad.alive
    assert nomad.x > 0 and nomad.y > 0
