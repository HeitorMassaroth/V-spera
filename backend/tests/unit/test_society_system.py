"""Testes unitários aprofundados para o Sistema de Sociedade Animal, Vínculos, Ninhos, Criação e Predação."""

import pytest
import math
from core.prng import PRNG
from core.entities.organism import Organism, AnimalMemory
from core.entities.nest import Nest
from core.entities.genetics import GeneticsEngine, AnimalGenome, AnimalPersonality
from core.entities.genealogy import GenealogyRegistry
from core.systems.family import FamilySystem, Family
from core.systems.movement import MovementSystem
from core.systems.metabolism import MetabolismSystem
from core.spatial.spatial_grid import SpatialHashGrid


def test_personality_generation_and_recombination():
    """Valida a geração de personalidade individual e recombinação com mutações."""
    prng = PRNG(42)
    p1 = GeneticsEngine.generate_random_personality(prng)
    p2 = GeneticsEngine.generate_random_personality(prng)

    assert 0.05 <= p1.agressividade <= 0.95
    assert 0.05 <= p1.instinto_protecao <= 0.95
    assert 0.50 <= p1.eficiencia_coleta <= 1.60

    child_p, mutations = GeneticsEngine.recombine_personality(p1, p2, prng)
    assert 0.05 <= child_p.agressividade <= 0.95
    assert 0.05 <= child_p.sociabilidade <= 0.95
    assert 0.05 <= child_p.instinto_protecao <= 0.95


def test_lifelong_pair_bonding_and_nest_creation():
    """Macho e Fêmea adultos estabelecem vínculo perpétuo e fundam um ninho familiar."""
    system = FamilySystem(cluster_radius=100.0, energy_threshold_form_family=90.0)
    prng = PRNG(123)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    male = Organism(id=1, x=200.0, y=200.0, energy=100.0, role=Organism.ROLE_MALE)
    female = Organism(id=2, x=205.0, y=200.0, energy=100.0, role=Organism.ROLE_FEMALE)
    organisms = {1: male, 2: female}
    clusters = [(200.0, 200.0)]

    newborns, events = system.update(organisms, clusters, prng, lambda: 10, lambda: 1, genealogy, pop_avg, 5)

    # Vínculo exclusivo mútuo
    assert male.partner_id == female.id
    assert female.partner_id == male.id
    assert male.partner_bond_tick == 5
    assert female.partner_bond_tick == 5

    # Ninho familiar criado
    assert male.nest_id is not None
    assert female.nest_id == male.nest_id
    assert male.nest_id in system.nests
    nest = system.nests[male.nest_id]
    assert nest.family_id == male.family_id
    assert nest.food_storage > 0.0


def test_nest_materials_and_upgrade():
    """Ninho acumula materiais e sobe de nível (1: Simples -> 2: Fortificado -> 3: Santuário)."""
    nest = Nest(id=1, family_id=1, x=100.0, y=100.0, materials=20.0, level=1)
    assert nest.level == 1

    nest.add_materials(35.0)  # Total 55
    assert nest.level == 2

    nest.add_materials(40.0)  # Total 95
    assert nest.level == 3


def test_five_developmental_stages_and_newborn_immobility():
    """Recém-nascido é imóvel no ninho; jovem independente vaga e coleta."""
    movement = MovementSystem(world_width=800.0, world_height=600.0)
    prng = PRNG(45)

    newborn = Organism(id=1, x=100.0, y=100.0, role=Organism.ROLE_CHILD, life_stage=Organism.STAGE_NEWBORN)
    assert newborn.traits.max_speed == 0.0
    fx, fy = movement.calculate_steering(newborn, None, prng)
    assert fx == 0.0 and fy == 0.0

    metabolism = MetabolismSystem()
    grid = SpatialHashGrid(cell_size=60.0)
    # Recém-nascido não coleta plantas silvestres
    eaten = metabolism.process_feeding(newborn, grid)
    assert eaten == []


def test_father_delivers_food_to_nest():
    """Pai com energia suficiente transporta biomassa alimentar e descarrega no ninho familiar."""
    system = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(55)
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    fam_id = 4
    nest_id = 9
    nest = Nest(id=nest_id, family_id=fam_id, x=200.0, y=200.0, food_storage=5.0)
    system.nests[nest_id] = nest

    # Pai próximo ao ninho com carried_food
    father = Organism(
        id=1,
        x=210.0,
        y=200.0,
        energy=90.0,
        role=Organism.ROLE_MALE,
        family_id=fam_id,
        nest_id=nest_id,
        carried_food=15.0,
    )
    fam = Family(id=fam_id, clan_name="Clã Teste", home_cluster_id=0, patriarch_id=1, matriarch_id=None, nest_id=nest_id)
    system.families[fam_id] = fam

    system.update({1: father}, [(200.0, 200.0)], prng, lambda: 1, lambda: 1, genealogy, pop_avg, 1)

    # Pai descarregou comida no ninho
    assert father.carried_food == 0.0
    assert nest.food_storage >= 20.0


def test_predator_intercepted_by_father():
    """Predador tenta aproximar-se de filhote vulnerável e é repelido pelo pai."""
    system = FamilySystem(cluster_radius=100.0)
    genealogy = GenealogyRegistry()
    prng = PRNG(88)
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    fam_id = 5
    nest_id = 3
    nest = Nest(id=nest_id, family_id=fam_id, x=300.0, y=300.0)
    system.nests[nest_id] = nest

    father = Organism(id=1, x=310.0, y=300.0, role=Organism.ROLE_MALE, family_id=fam_id, nest_id=nest_id, genome=AnimalGenome(forca=85.0))
    pup = Organism(id=2, x=300.0, y=300.0, role=Organism.ROLE_CHILD, life_stage=Organism.STAGE_NEWBORN, family_id=fam_id, nest_id=nest_id)
    predator = Organism(
        id=3,
        x=322.0,
        y=300.0,
        role=Organism.ROLE_MALE,
        family_id=99,
        energy=25.0,  # Faminto, comportamento predatório
        genome=AnimalGenome(max_saude=100.0),
    )

    fam = Family(id=fam_id, clan_name="Clã Alfa", home_cluster_id=0, patriarch_id=1, matriarch_id=None, nest_id=nest_id, children_ids=[2])
    system.families[fam_id] = fam

    organisms = {1: father, 2: pup, 3: predator}
    _, events = system.update(organisms, [(300.0, 300.0)], prng, lambda: 1, lambda: 1, genealogy, pop_avg, 10)

    # O pai atacou o predador em defesa
    combat_events = [e for e in events if e.get("type") == "combat"]
    assert len(combat_events) > 0
    assert predator.saude < 100.0
    # Predador registrou a zona de perigo na memória
    assert len(predator.memory.danger_zones) > 0


def test_mourning_on_partner_death():
    """Morte do parceiro desencadeia período de luto e memória afetiva no sobrevivente."""
    system = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(99)
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    fam_id = 6
    male = Organism(id=1, x=100.0, y=100.0, role=Organism.ROLE_MALE, family_id=fam_id, partner_id=2)
    # Fêmea não está no dicionário (faleceu)
    organisms = {1: male}

    fam = Family(id=fam_id, clan_name="Clã Ômega", home_cluster_id=0, patriarch_id=1, matriarch_id=2)
    system.families[fam_id] = fam

    system.update(organisms, [(100.0, 100.0)], prng, lambda: 1, lambda: 1, genealogy, pop_avg, 20)

    # Macho perdeu parceiro e entrou em luto
    assert male.partner_id is None
    assert male.mourning_ticks > 0
    assert len(male.memory.lost_relatives) > 0
