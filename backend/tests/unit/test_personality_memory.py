"""Testes unitários e de integração para o Sistema de Personalidade e Memória Individual."""

import math
import time
import pytest
from core.prng import PRNG
from core.spatial.spatial_grid import SpatialHashGrid
from core.entities.genetics import AnimalGenome, AnimalPersonality, GeneticsEngine
from core.entities.organism import Organism, AnimalMemory, EpisodicMemory, SPECIES_PREDATOR, SPECIES_VRANCO
from core.systems.movement import MovementSystem
from core.systems.family import FamilySystem
from core.world import World


def test_1_different_personalities_across_individuals():
    """1. Verifica se animais diferentes (mesmo com genética idêntica) apresentam personalidades distintas."""
    prng = PRNG(seed=42)
    genome = GeneticsEngine.generate_random_genome(prng, is_vranco=False)

    personalities = [
        GeneticsEngine.generate_random_personality(prng, is_vranco=False, genome=genome)
        for _ in range(20)
    ]

    # Todos os atributos devem estar no intervalo normalizado [0.0, 1.0]
    for p in personalities:
        assert 0.0 <= p.coragem <= 1.0
        assert 0.0 <= p.agressividade <= 1.0
        assert 0.0 <= p.sociabilidade <= 1.0
        assert 0.0 <= p.curiosidade <= 1.0
        assert 0.0 <= p.cautela <= 1.0
        assert 0.0 <= p.protecao <= 1.0
        assert 0.0 <= p.persistencia <= 1.0

    # Pelo menos duas personalidades devem ter diferenças nos traços
    diff_coragem = len({round(p.coragem, 4) for p in personalities})
    diff_agress = len({round(p.agressividade, 4) for p in personalities})
    diff_cautela = len({round(p.cautela, 4) for p in personalities})

    assert diff_coragem > 1, "Personalidades deveriam variar estocasticamente entre indivíduos"
    assert diff_agress > 1, "Agressividade deveria apresentar variação individual"
    assert diff_cautela > 1, "Cautela deveria apresentar variação individual"


def test_2_experiences_alter_future_decisions():
    """2. Verifica se experiências passadas (memória de ataques/ajuda) alteram decisões de movimento e fuga."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)
    prng = PRNG(seed=999)

    # Predador A ferido e cauteloso
    org_a = Organism(
        id=1,
        species=SPECIES_PREDATOR,
        x=200.0,
        y=200.0,
        energy=60.0,
        saude=30.0,
        personality=AnimalPersonality(cautela=0.8, coragem=0.3, persistencia=0.5),
    )

    # Adversário B
    org_b = Organism(
        id=2,
        species=SPECIES_PREDATOR,
        x=230.0,
        y=200.0,
        energy=80.0,
        saude=80.0,
    )

    grid = SpatialHashGrid[Organism](cell_size=100.0)
    grid.insert(org_a, org_a.x, org_a.y)
    grid.insert(org_b, org_b.x, org_b.y)

    # Antes de ter memória traumática de B:
    steer_before = movement.calculate_steering(org_a, target_food=None, prng=prng, organism_grid=grid)

    # Registra memória de ataque sofrido de B
    org_a.memory.add_episode(
        event_type="ATTACKED_BY",
        description=f"Atacado pelo predador {org_b.name}",
        tick=10,
        x=org_b.x,
        y=org_b.y,
        intensity=0.9,
        relevance=1.0,
        involved_id=org_b.id,
        involved_name=org_b.name,
    )

    # Após o ataque: o ressentimento e trauma alteram a resposta motora (afastamento de B)
    steer_after = movement.calculate_steering(org_a, target_food=None, prng=prng, organism_grid=grid)

    # Força na direção X deve ser mais negativa (empurrando para longe de B em x=230)
    assert steer_after[0] < steer_before[0], (
        f"A memória do ataque deveria intensificar o vetor de repulsão/evasão: antes={steer_before}, depois={steer_after}"
    )


def test_3_memories_associated_with_correct_individuals():
    """3. Verifica se as memórias são associadas aos indivíduos corretos (grudges e gratidão)."""
    org = Organism(id=1, species=SPECIES_VRANCO, x=100.0, y=100.0)

    # Registra ataque pelo predador 99
    org.memory.add_episode(
        event_type="ATTACKED_BY",
        description="Atacado por Predador Alfa",
        tick=5,
        x=120.0,
        y=100.0,
        intensity=0.8,
        relevance=1.0,
        involved_id=99,
        involved_name="Predador Alfa",
    )

    # Registra ajuda recebida da fêmea 42
    org.memory.add_episode(
        event_type="RECEIVED_HELP",
        description="Recebeu auxílio alimentar de Protetora",
        tick=8,
        x=105.0,
        y=100.0,
        intensity=0.7,
        relevance=1.0,
        involved_id=42,
        involved_name="Protetora",
    )

    # Grudge associado a 99
    assert org.memory.get_grudge_score(99) > 0.5
    assert org.memory.get_grudge_score(42) == 0.0
    assert org.memory.get_grudge_score(123) == 0.0

    # Gratidão associada a 42
    assert org.memory.get_gratitude_score(42) > 0.5
    assert org.memory.get_gratitude_score(99) == 0.0
    assert org.memory.get_gratitude_score(123) == 0.0

    # Verificação dos metadados das memórias
    episodes = org.memory.episodes
    assert len(episodes) == 2
    assert episodes[0].involved_name == "Predador Alfa"
    assert episodes[0].involved_id == 99
    assert episodes[1].involved_name == "Protetora"
    assert episodes[1].involved_id == 42


def test_4_memory_count_strictly_limited_and_compacted():
    """4. Verifica se a quantidade de memórias permanece estritamente limitada e aplica compactação."""
    memory = AnimalMemory(max_episodes=12)

    # Insere 25 eventos com relevâncias e intensidades distintas
    for i in range(25):
        memory.add_episode(
            event_type="FOUND_FOOD" if i % 2 == 0 else "ATTACKED_BY",
            description=f"Evento #{i}",
            tick=i * 10,
            x=100.0 + i,
            y=100.0 + i,
            intensity=0.2 + (i / 50.0),
            relevance=0.3 + (i / 50.0),
            involved_id=i,
        )

    # O número total não pode exceder o limite estrito (12)
    assert len(memory.episodes) <= 12
    assert memory.max_episodes == 12

    # Verifica decaimento temporal
    initial_relevance = memory.episodes[0].relevance
    memory.decay_memories(current_tick=500, rate=0.002)
    decayed_relevance = memory.episodes[0].relevance
    assert decayed_relevance < initial_relevance


def test_5_species_preserve_characteristic_behaviors():
    """5. Verifica se Predadores e Vrancos preservam comportamentos característicos da raça."""
    family_sys = FamilySystem()

    # Vrancos não disputam liderança agressiva entre si
    vranco_m1 = Organism(id=1, species=SPECIES_VRANCO, x=100.0, y=100.0, role=Organism.ROLE_MALE)
    vranco_m2 = Organism(id=2, species=SPECIES_VRANCO, x=105.0, y=100.0, role=Organism.ROLE_MALE)
    assert not family_sys.evaluate_male_contest(vranco_m1, vranco_m2)

    # Predadores podem disputar território / liderança
    pred_m1 = Organism(id=3, species=SPECIES_PREDATOR, x=200.0, y=200.0, role=Organism.ROLE_MALE)
    pred_m2 = Organism(id=4, species=SPECIES_PREDATOR, x=205.0, y=200.0, role=Organism.ROLE_MALE)
    assert family_sys.evaluate_male_contest(pred_m1, pred_m2)

    # Vrancos têm maior propensão à sociabilidade base do que Predadores
    prng = PRNG(seed=123)
    vranco_soc = [GeneticsEngine.generate_random_personality(prng, is_vranco=True).sociabilidade for _ in range(30)]
    pred_soc = [GeneticsEngine.generate_random_personality(prng, is_vranco=False).sociabilidade for _ in range(30)]

    avg_vranco_soc = sum(vranco_soc) / len(vranco_soc)
    avg_pred_soc = sum(pred_soc) / len(pred_soc)
    assert avg_vranco_soc > avg_pred_soc, "Vrancos devem apresentar maior sociabilidade média que Predadores"


def test_6_simulation_performance_with_large_populations():
    """6. Verifica se o ecossistema com personalidade e memórias individuais mantém alta taxa de processamento."""
    world = World(width=1600.0, height=1200.0, seed=777, initial_predators=40, initial_vrancos=40, initial_food=120)

    assert len(world.organisms) == 80

    start_time = time.perf_counter()
    ticks_to_run = 40
    for _ in range(ticks_to_run):
        world.step()
    elapsed = time.perf_counter() - start_time

    ms_per_tick = (elapsed / ticks_to_run) * 1000.0

    # Menos de 30ms por tick mesmo com resolução física, memórias, decaimento e clãs
    assert ms_per_tick < 30.0, f"Tempo de ciclo muito alto: {ms_per_tick:.2f} ms/tick (limite 30ms)"
