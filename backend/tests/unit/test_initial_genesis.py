"""Testes para a gênese primordial: população inicial aleatória de 0 a 10 por tipo (Macho/Fêmea) e ausência de ninhos/clãs iniciais."""

import pytest
from core.world import World
from core.entities.organism import Organism


def test_random_initial_genesis_defaults():
    """Garante que a inicialização padrão sorteie de 0 a 10 de cada tipo (Macho e Fêmea) para cada espécie, sem ninhos nem clãs."""
    world = World(seed=999)

    # 1. Nenhum ninho nem clã formado inicialmente
    assert len(world.family_system.nests) == 0
    assert len(world.family_system.families) == 0
    assert len(world.clan_system.clans) == 0

    # 2. Contagens de cada tipo por espécie dentro dos limites [0, 10]
    pred_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_FEMALE]
    pred_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_MALE]
    vran_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_FEMALE]
    vran_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_MALE]

    assert 0 <= len(pred_females) <= 10
    assert 0 <= len(pred_males) <= 10
    assert 0 <= len(vran_females) <= 10
    assert 0 <= len(vran_males) <= 10

    # 3. Todos os pioneiros começam solitários e independentes
    for org in world.organisms.values():
        assert org.family_id is None
        assert org.nest_id is None
        assert org.clan_id is None
        assert org.partner_id is None
        assert org.father_id is None
        assert org.mother_id is None
        assert org.generation == 0


def test_organisms_never_appear_from_nowhere():
    """Garante que novos habitantes NUNCA surjam do nada; apenas nascem de reprodução biológica comprovada (mãe e pai)."""
    world = World(seed=42)
    initial_pioneer_ids = set(world.organisms.keys())

    # Roda a simulação por 60 ticks
    for _ in range(60):
        world.step()

    # Cada novo indivíduo nascido durante a simulação deve ter pais registrados na genealogia
    for oid, org in world.organisms.items():
        if oid not in initial_pioneer_ids:
            # Novo habitante DEVE ser fruto de reprodução legítima
            assert org.generation >= 1
            assert org.mother_id is not None
            assert org.father_id is not None
            # Ambos os pais devem existir no registro genealógico
            rec = world.genealogy.get_record(oid)
            assert rec is not None
            assert rec.mother_id is not None
            assert rec.father_id is not None


def test_explicit_sex_counts():
    """Garante que parâmetros específicos de machos e fêmeas sejam respeitados quando fornecidos."""
    world = World(
        seed=123,
        initial_predator_females=3,
        initial_predator_males=2,
        initial_vranco_females=5,
        initial_vranco_males=4,
    )

    pred_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_FEMALE]
    pred_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_MALE]
    vran_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_FEMALE]
    vran_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_MALE]

    assert len(pred_females) == 3
    assert len(pred_males) == 2
    assert len(vran_females) == 5
    assert len(vran_males) == 4
    assert len(world.organisms) == 14
    assert len(world.family_system.nests) == 0
    assert len(world.clan_system.clans) == 0


def test_zero_species_does_not_trigger_false_extinction():
    """Garante que quando uma espécie é inicializada com zero indivíduos, não dispara falso evento de extinção no tick 1."""
    world = World(
        seed=123,
        initial_predator_females=2,
        initial_predator_males=2,
        initial_vranco_females=0,
        initial_vranco_males=0,
    )
    # Roda 5 ticks
    for _ in range(5):
        world.step()

    # Não deve existir evento de extinção de Vrancos na crônica
    extinction_events = [
        e for e in world.chronicle._events
        if e.event_type == "SPECIES_EXTINCTION" and e.species == Organism.SPECIES_VRANCO
    ]
    assert len(extinction_events) == 0


def test_sexual_viability_pioneers():
    """Garante que qualquer espécie que apareça na gênese aleatória possua ambos os sexos (BUG-01 mitigado)."""
    for seed in range(50):
        world = World(seed=seed)
        p_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_FEMALE]
        p_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_PREDATOR and o.role == Organism.ROLE_MALE]
        v_females = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_FEMALE]
        v_males = [o for o in world.organisms.values() if o.species == Organism.SPECIES_VRANCO and o.role == Organism.ROLE_MALE]

        # Se houver predadores, ambos os sexos devem estar presentes
        if p_females or p_males:
            assert len(p_females) > 0 and len(p_males) > 0

        # Se houver vrancos, ambos os sexos devem estar presentes
        if v_females or v_males:
            assert len(v_females) > 0 and len(v_males) > 0


def test_initial_food_proportional_to_pioneers():
    """Garante que a quantidade de comida inicial escale proporcionalmente à população pioneira (BUG-02 mitigado)."""
    world = World(seed=999)
    total_pioneers = len(world.organisms)
    assert len(world.foods) <= max(12, total_pioneers * 4)


