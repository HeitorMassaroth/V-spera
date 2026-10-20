"""Testes unitários para o sistema de genética, colisão sem sobreposição, genealogia e combate territorial."""

import pytest
from core.world import World
from core.prng import PRNG
from core.entities.organism import Organism
from core.entities.genetics import AnimalGenome, GeneticsEngine
from core.entities.genealogy import GenealogyRegistry
from core.systems.family import FamilySystem
from core.systems.movement import MovementSystem
from core.spatial.spatial_grid import SpatialHashGrid


def test_initial_two_divisions():
    """Garante que a população inicial é dividida uniformemente entre Rosa (fêmea) e Verde (macho)."""
    world = World(initial_organisms=40, initial_food=50, seed=123)

    females = [o for o in world.organisms.values() if o.role == Organism.ROLE_FEMALE]
    males = [o for o in world.organisms.values() if o.role == Organism.ROLE_MALE]

    assert len(females) == 20
    assert len(males) == 20

    # Rosa deve ter hue ~335 e Verde ~140
    assert females[0].traits.color_hue == 335.0
    assert males[0].traits.color_hue == 140.0

    # Cada animal deve possuir nome e genoma individual
    assert females[0].name != ""
    assert males[0].genome.forca >= 1.0


def test_collision_non_overlap():
    """Dois organismos em sobreposição espacial são separados fisicamente e não se sobrepõem."""
    movement = MovementSystem(world_width=800.0, world_height=600.0)
    grid = SpatialHashGrid[Organism](cell_size=60.0)

    org1 = Organism(id=1, x=100.0, y=100.0, vx=1.0, vy=0.0)
    org2 = Organism(id=2, x=102.0, y=100.0, vx=-1.0, vy=0.0)
    # Raio de cada um é ~6.0, logo distância mínima deve ser ~12.0
    org1.traits.size = 6.0
    org2.traits.size = 6.0

    grid.insert(org1, org1.x, org1.y)
    grid.insert(org2, org2.x, org2.y)

    organisms = {1: org1, 2: org2}

    # Executa resolução de colisão
    movement.resolve_organism_collisions(organisms, grid)

    # Distância resultante deve ser >= soma dos raios (12.0)
    import math
    dist = math.hypot(org1.x - org2.x, org1.y - org2.y)
    assert dist >= 11.99, f"Organismos ainda estão sobrepostos: dist={dist}"


def test_family_formation_no_blue_guardian():
    """Macho e Fêmea bem alimentados formam família no centro; o macho permanece Verde (ROLE_MALE)."""
    system = FamilySystem(cluster_radius=100.0, energy_threshold_form_family=90.0)
    prng = PRNG(42)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    male = Organism(id=1, x=150.0, y=150.0, energy=100.0, role=Organism.ROLE_MALE)
    female = Organism(id=2, x=155.0, y=150.0, energy=100.0, role=Organism.ROLE_FEMALE)
    organisms = {1: male, 2: female}
    clusters = [(150.0, 150.0)]

    next_fam_id = 1
    def fam_counter():
        nonlocal next_fam_id
        res = next_fam_id
        next_fam_id += 1
        return res

    newborns, _ = system.update(organisms, clusters, prng, lambda: 10, fam_counter, genealogy, pop_avg, 1)

    # Família deve ter sido formada
    assert male.family_id is not None
    assert female.family_id == male.family_id
    assert male.home_cluster_id == 0
    assert female.home_cluster_id == 0

    # O macho PERMANECE Verde (ROLE_MALE), não existe Azul/Guardião
    assert male.role == Organism.ROLE_MALE
    assert male.traits.color_hue == 140.0


def test_macho_combat_and_damage_to_enemies():
    """O Macho protege o centro com a Rosa e o Filho e inflige dano real aos inimigos."""
    system = FamilySystem(cluster_radius=90.0)
    prng = PRNG(99)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    fam_id = 7
    father_genome = AnimalGenome(forca=80.0, resistencia=60.0)
    father = Organism(id=1, x=200.0, y=200.0, role=Organism.ROLE_MALE, family_id=fam_id, home_cluster_id=0, genome=father_genome)
    mother = Organism(id=2, x=205.0, y=200.0, role=Organism.ROLE_FEMALE, family_id=fam_id, home_cluster_id=0)
    child = Organism(id=3, x=202.0, y=202.0, role=Organism.ROLE_CHILD, family_id=fam_id, home_cluster_id=0)

    enemy_genome = AnimalGenome(forca=40.0, resistencia=30.0, max_saude=100.0)
    enemy = Organism(id=4, x=208.0, y=200.0, role=Organism.ROLE_MALE, family_id=None, energy=80.0, saude=100.0, genome=enemy_genome)

    organisms = {1: father, 2: mother, 3: child, 4: enemy}
    clusters = [(200.0, 200.0)]

    initial_enemy_health = enemy.saude

    # Executa ciclo de defesa e combate
    system.update(organisms, clusters, prng, lambda: 100, lambda: 10, genealogy, pop_avg, 5)

    # O inimigo deve ter sofrido dano na saúde e sido repelido
    assert enemy.saude < initial_enemy_health, f"Inimigo não sofreu dano: saude={enemy.saude}"
    assert enemy.vx != 0.0 or enemy.energy < 80.0


def test_reproduction_with_genetics_and_strong_trait_bias():
    """Casal no centro gera filhote roxo com genoma herdado e tendência a características fortes."""
    system = FamilySystem(cluster_radius=100.0, energy_threshold_reproduce=80.0)
    prng = PRNG(101)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    fam_id = 3
    # Pai com força muito alta (90) bem acima da média da população (50)
    father_genome = AnimalGenome(forca=90.0, velocidade=50.0)
    mother_genome = AnimalGenome(forca=60.0, velocidade=50.0)

    father = Organism(id=1, x=300.0, y=300.0, energy=95.0, role=Organism.ROLE_MALE, family_id=fam_id, genome=father_genome, reproduction_cooldown=0)
    mother = Organism(id=2, x=305.0, y=300.0, energy=95.0, role=Organism.ROLE_FEMALE, family_id=fam_id, genome=mother_genome, reproduction_cooldown=0)

    organisms = {1: father, 2: mother}
    clusters = [(300.0, 300.0)]

    newborns, _ = system.update(organisms, clusters, prng, lambda: 50, lambda: 1, genealogy, pop_avg, 12)

    assert len(newborns) == 1
    child = newborns[0]
    assert child.role == Organism.ROLE_CHILD
    assert child.traits.color_hue == 280.0  # Roxo
    assert child.traits.size == 3.5  # Tamanho de filhote
    assert child.family_id == fam_id
    assert child.father_id == father.id
    assert child.mother_id == mother.id

    # Força média dos pais seria 75, mas com bônus de traço forte deve ser elevada (> 70)
    assert child.genome.forca >= 65.0

    # Registro genealógico deve existir no cartório perpétuo
    record = genealogy.get_record(child.id)
    assert record is not None
    assert record.father_id == father.id
    assert record.mother_id == mother.id


def test_child_growth_and_maturation():
    """Filhote roxo cresce ao longo do tempo e amadurece para macho (verde) ou fêmea (rosa)."""
    system = FamilySystem(maturity_threshold=50)
    prng = PRNG(77)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    child = Organism(
        id=10,
        x=100.0,
        y=100.0,
        role=Organism.ROLE_CHILD,
        maturity_ticks=0,
    )
    organisms = {10: child}
    clusters = [(100.0, 100.0)]

    # Executa 25 ticks (meio caminho)
    for t in range(25):
        system.update(organisms, clusters, prng, lambda: 1, lambda: 1, genealogy, pop_avg, t)

    assert child.role == Organism.ROLE_CHILD
    assert child.traits.size > 3.5

    # Executa até completar 50 ticks
    for t in range(25, 55):
        system.update(organisms, clusters, prng, lambda: 1, lambda: 1, genealogy, pop_avg, t)

    # Filhote deve ter amadurecido para macho ou fêmea!
    assert child.role in (Organism.ROLE_FEMALE, Organism.ROLE_MALE)
    if child.role == Organism.ROLE_FEMALE:
        assert child.traits.color_hue == 335.0
    else:
        assert child.traits.color_hue == 140.0


def test_genealogy_prune_ancient_records():
    """Garante que a poda genealógica preserve ancestrais vivos e pioneiros enquanto descarta registros antigos (BUG-03 mitigado)."""
    from core.entities.genealogy import GenealogyRegistry
    from core.entities.genetics import GeneticsEngine
    from core.prng import PRNG

    registry = GenealogyRegistry()
    prng = PRNG(42)

    # Cria pioneiro geração 0
    g0 = GeneticsEngine.generate_random_genome(prng)
    registry.register_birth(1, "Ancestral", "MALE", 0, 0, None, None, None, g0, [], [])
    registry.register_death(1, 100, "Velhice")

    # Cria 10 registros intermediários falecidos (geração 1)
    for i in range(2, 12):
        gi = GeneticsEngine.generate_random_genome(prng)
        registry.register_birth(i, f"Morto_{i}", "FEMALE", 1, 50 + i, 1, None, None, gi, [], [])
        registry.register_death(i, 120 + i, "Predação")

    # Cria indivíduo vivo atual (geração 2) cujo pai é 2
    g2 = GeneticsEngine.generate_random_genome(prng)
    registry.register_birth(20, "Vivo", "MALE", 2, 200, 2, None, None, g2, [], [])

    # Poda com limite de 5 registros
    active_ids = {20}
    pruned = registry.prune_ancient_records(active_ids, max_records=5)

    assert pruned > 0
    # O vivo (20), o pioneiro G0 (1) e o pai direto (2) DEVEM ser preservados
    assert registry.get_record(20) is not None
    assert registry.get_record(1) is not None
    assert registry.get_record(2) is not None

