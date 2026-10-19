"""Testes aprofundados para o ciclo de vida completo e funcional das famílias e clãs."""

import pytest
from core.prng import PRNG
from core.entities.organism import Organism
from core.entities.genetics import AnimalGenome
from core.entities.genealogy import GenealogyRegistry
from core.systems.family import FamilySystem, Family, get_clan_name


def test_persistent_territory_and_no_erasure_by_intruders():
    """Território do clã permanece firme mesmo se intrusos pisarem no oásis."""
    system = FamilySystem(cluster_radius=90.0)
    prng = PRNG(42)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    clusters = [(200.0, 200.0)]

    # Macho e Fêmea bem alimentados fundam Clã 1 no centro 0
    male = Organism(id=1, x=200.0, y=200.0, energy=120.0, role=Organism.ROLE_MALE)
    female = Organism(id=2, x=205.0, y=200.0, energy=120.0, role=Organism.ROLE_FEMALE)

    organisms = {1: male, 2: female}
    system.update(organisms, clusters, prng, lambda: 10, lambda: 1, genealogy, pop_avg, 1)

    assert 0 in system.cluster_homes
    assert system.cluster_homes[0] == 1
    fam = system.families[1]
    assert fam.is_active is True
    assert fam.patriarch_id == 1
    assert fam.matriarch_id == 2

    # Um intruso entra no oásis para se alimentar
    intruder = Organism(id=99, x=210.0, y=200.0, energy=80.0, role=Organism.ROLE_MALE, family_id=None)
    organisms[99] = intruder

    system.update(organisms, clusters, prng, lambda: 11, lambda: 2, genealogy, pop_avg, 2)

    # O território NÃO pode ser apagado! O centro 0 continua pertencendo ao Clã 1!
    assert 0 in system.cluster_homes
    assert system.cluster_homes[0] == 1
    # E o macho deve ter desferido dano contra o invasor
    assert intruder.saude < intruder.genome.max_saude


def test_child_dispersal_upon_adulthood():
    """Ao atingir maturidade, filhote se torna adulto independente (dispersão biológica)."""
    system = FamilySystem(maturity_threshold=30)
    prng = PRNG(99)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    child = Organism(
        id=5,
        x=100.0,
        y=100.0,
        role=Organism.ROLE_CHILD,
        family_id=2,
        home_cluster_id=0,
        maturity_ticks=29,  # Falta 1 tick para maturação
    )
    organisms = {5: child}
    clusters = [(100.0, 100.0)]

    system.update(organisms, clusters, prng, lambda: 1, lambda: 1, genealogy, pop_avg, 1)

    # Deve ter amadurecido
    assert child.role in (Organism.ROLE_FEMALE, Organism.ROLE_MALE)
    # E deve ter se desvinculado do ninho parental para fundar seu próprio clã
    assert child.family_id is None
    assert child.home_cluster_id is None


def test_widow_succession_and_remarriage():
    """Se o patriarca morre, um macho solteiro bem alimentado pode assumir o papel de protetor do clã."""
    system = FamilySystem(cluster_radius=90.0, energy_threshold_form_family=100.0)
    prng = PRNG(10)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    clusters = [(150.0, 150.0)]

    # Clã com viúva e filhote
    matriarch = Organism(id=20, x=150.0, y=150.0, role=Organism.ROLE_FEMALE, family_id=4, home_cluster_id=0, energy=90.0)
    child = Organism(id=21, x=152.0, y=150.0, role=Organism.ROLE_CHILD, family_id=4, home_cluster_id=0, energy=70.0)

    # Macho solteiro bem alimentado entra no centro
    new_macho = Organism(id=30, x=155.0, y=150.0, role=Organism.ROLE_MALE, family_id=None, energy=115.0)

    organisms = {20: matriarch, 21: child, 30: new_macho}
    system.update(organisms, clusters, prng, lambda: 1, lambda: 1, genealogy, pop_avg, 1)

    # O novo macho deve ter assumido o papel de patriarca do Clã 4
    assert new_macho.family_id == 4
    assert new_macho.home_cluster_id == 0
    fam = system.families[4]
    assert fam.patriarch_id == 30
    assert fam.matriarch_id == 20


def test_clan_extinction_releases_territory():
    """Quando todos os membros de uma família morrem, o território fica livre para novas famílias."""
    system = FamilySystem(cluster_radius=90.0)
    prng = PRNG(5)
    genealogy = GenealogyRegistry()
    pop_avg = {"forca": 50.0, "velocidade": 50.0, "resistencia": 50.0, "inteligencia": 50.0, "max_saude": 100.0}

    clusters = [(100.0, 100.0)]

    # Família ativa
    male = Organism(id=1, x=100.0, y=100.0, role=Organism.ROLE_MALE, family_id=1, home_cluster_id=0, energy=110.0)
    female = Organism(id=2, x=105.0, y=100.0, role=Organism.ROLE_FEMALE, family_id=1, home_cluster_id=0, energy=110.0)

    organisms = {1: male, 2: female}
    system.update(organisms, clusters, prng, lambda: 10, lambda: 1, genealogy, pop_avg, 1)

    assert 0 in system.cluster_homes

    # Ambos falecem
    male.alive = False
    female.alive = False
    del organisms[1]
    del organisms[2]

    system.update(organisms, clusters, prng, lambda: 10, lambda: 1, genealogy, pop_avg, 2)

    # Território 0 deve estar livre agora!
    assert 0 not in system.cluster_homes
    assert system.families[1].is_active is False
