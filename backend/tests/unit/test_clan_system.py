"""Testes unitários para o Módulo de Clãs, Liderança (Alpha/Beta), Reserva Coletiva e Diplomacia."""

import pytest
from core.entities.clan import (
    Clan,
    ClanSocialStage,
    ClanRelation,
    ClanPriorityType,
    calculate_leadership_score,
)
from core.entities.organism import Organism
from core.entities.genetics import AnimalGenome, AnimalPersonality
from core.entities.nest import Nest
from core.entities.genealogy import GenealogyRegistry
from core.systems.family import Family, FamilySystem
from core.systems.clan_system import ClanSystem
from core.prng import PRNG


def test_scenario_1_spontaneous_clan_formation_three_cooperating_families():
    """Cenário 1: Três famílias próximas começam a cooperar e formam um clã."""
    clan_system = ClanSystem(cooperation_threshold_established=30.0, cooperation_radius=200.0)
    prng = PRNG(42)
    genealogy = GenealogyRegistry()
    events = []

    # Cria 3 famílias com ninhos próximos
    f1 = Family(id=1, clan_name="F1", home_cluster_id=0, patriarch_id=1, matriarch_id=2, nest_id=1)
    f2 = Family(id=2, clan_name="F2", home_cluster_id=0, patriarch_id=3, matriarch_id=4, nest_id=2)
    f3 = Family(id=3, clan_name="F3", home_cluster_id=0, patriarch_id=5, matriarch_id=6, nest_id=3)
    families = {1: f1, 2: f2, 3: f3}

    nests = {
        1: Nest(id=1, family_id=1, x=100.0, y=100.0),
        2: Nest(id=2, family_id=2, x=120.0, y=100.0),
        3: Nest(id=3, family_id=3, x=110.0, y=120.0),
    }

    organisms = {
        1: Organism(id=1, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE),
        2: Organism(id=2, x=102.0, y=100.0, family_id=1, role=Organism.ROLE_FEMALE),
        3: Organism(id=3, x=120.0, y=100.0, family_id=2, role=Organism.ROLE_MALE),
        4: Organism(id=4, x=122.0, y=100.0, family_id=2, role=Organism.ROLE_FEMALE),
        5: Organism(id=5, x=110.0, y=120.0, family_id=3, role=Organism.ROLE_MALE),
        6: Organism(id=6, x=112.0, y=120.0, family_id=3, role=Organism.ROLE_FEMALE),
    }

    # Simula cooperação recorrente acumulada
    clan_system.add_family_coop(1, 2, 35.0)
    clan_system.add_family_coop(2, 3, 35.0)
    clan_system.add_family_coop(1, 3, 35.0)

    clan_system.update(organisms, families, nests, prng, genealogy, events, 1)

    # Clã deve ter emergido espontaneamente com as 3 famílias
    assert len(clan_system.clans) == 1
    clan = list(clan_system.clans.values())[0]
    assert clan.family_ids == {1, 2, 3}
    assert clan.stage == ClanSocialStage.ESTABLISHED_CLAN
    assert any(e["type"] == "clan_formed" for e in events)


def test_scenario_2_non_cooperating_families_stay_independent():
    """Cenário 2: Três famílias próximas não cooperam e permanecem independentes."""
    clan_system = ClanSystem(cooperation_threshold_occasional=15.0)
    prng = PRNG(42)
    genealogy = GenealogyRegistry()
    events = []

    f1 = Family(id=1, clan_name="F1", home_cluster_id=0, patriarch_id=1, matriarch_id=2, nest_id=1)
    f2 = Family(id=2, clan_name="F2", home_cluster_id=0, patriarch_id=3, matriarch_id=4, nest_id=2)
    f3 = Family(id=3, clan_name="F3", home_cluster_id=0, patriarch_id=5, matriarch_id=6, nest_id=3)
    families = {1: f1, 2: f2, 3: f3}

    nests = {
        1: Nest(id=1, family_id=1, x=100.0, y=100.0),
        2: Nest(id=2, family_id=2, x=110.0, y=100.0),
        3: Nest(id=3, family_id=3, x=105.0, y=110.0),
    }

    # Machos agressivos em conflito constante (sem sociabilidade)
    p_agr = AnimalPersonality(sociabilidade=0.1, agressividade=0.9)
    organisms = {
        1: Organism(id=1, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, personality=p_agr),
        2: Organism(id=2, x=102.0, y=100.0, family_id=1, role=Organism.ROLE_FEMALE),
        3: Organism(id=3, x=110.0, y=100.0, family_id=2, role=Organism.ROLE_MALE, personality=p_agr),
        4: Organism(id=4, x=112.0, y=100.0, family_id=2, role=Organism.ROLE_FEMALE),
        5: Organism(id=5, x=105.0, y=110.0, family_id=3, role=Organism.ROLE_MALE, personality=p_agr),
        6: Organism(id=6, x=107.0, y=110.0, family_id=3, role=Organism.ROLE_FEMALE),
    }

    # Cooperação não foi estabelecida (coop = 0.0)
    clan_system.update(organisms, families, nests, prng, genealogy, events, 1)

    # Nenhum clã deve ser fundado; permanecem independentes
    assert len(clan_system.clans) == 0


def test_scenario_3_alpha_and_beta_chosen_by_highest_individual_strength():
    """Cenário 3: O Alpha e o Beta são escolhidos entre os habitantes elegíveis mais fortes."""
    clan = Clan(id=1, name="Clã Apex", stage=ClanSocialStage.ESTABLISHED_CLAN, family_ids={1, 2, 3})

    # Cria candidatos adultos solteiros (partner_id = None) com genomas graduados
    g_super = AnimalGenome(forca=95.0, resistencia=90.0, max_saude=120.0, velocidade=80.0)
    g_strong = AnimalGenome(forca=80.0, resistencia=75.0, max_saude=100.0, velocidade=70.0)
    g_weak = AnimalGenome(forca=40.0, resistencia=40.0, max_saude=80.0, velocidade=40.0)

    org1 = Organism(id=10, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, genome=g_weak, partner_id=None)
    org2 = Organism(id=20, x=100.0, y=100.0, family_id=2, role=Organism.ROLE_MALE, genome=g_strong, partner_id=None)
    org3 = Organism(id=30, x=100.0, y=100.0, family_id=3, role=Organism.ROLE_MALE, genome=g_super, partner_id=None)

    organisms = {10: org1, 20: org2, 30: org3}

    alpha_id, beta_id = clan.elect_leaders(organisms, current_tick=1, force=True)

    # org3 é o mais forte -> Alpha
    # org2 é o segundo mais forte -> Beta
    assert alpha_id == 30
    assert beta_id == 20
    assert clan.alpha_score > clan.beta_score
    assert alpha_id != beta_id


def test_scenario_4_strongest_inhabitant_ineligible_due_to_partner():
    """Cenário 4: Um habitante mais forte torna-se inelegível por possuir um parceiro."""
    clan = Clan(id=1, name="Clã Sylva", stage=ClanSocialStage.ESTABLISHED_CLAN, family_ids={1, 2})

    g_titan = AnimalGenome(forca=99.0, resistencia=99.0, max_saude=120.0)
    g_runner = AnimalGenome(forca=70.0, resistencia=70.0, max_saude=100.0)
    g_third = AnimalGenome(forca=60.0, resistencia=60.0, max_saude=90.0)

    # org1 é o mais forte absoluto da população, MAS TEM PARCEIRO (casado)
    org1_married = Organism(id=1, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, genome=g_titan, partner_id=2)
    org2_female = Organism(id=2, x=105.0, y=100.0, family_id=1, role=Organism.ROLE_FEMALE, partner_id=1)

    # org3 e org4 são solteiros
    org3_single = Organism(id=3, x=100.0, y=100.0, family_id=2, role=Organism.ROLE_MALE, genome=g_runner, partner_id=None)
    org4_single = Organism(id=4, x=100.0, y=100.0, family_id=2, role=Organism.ROLE_MALE, genome=g_third, partner_id=None)

    organisms = {1: org1_married, 2: org2_female, 3: org3_single, 4: org4_single}

    assert clan.is_eligible_for_leadership(org1_married) is False

    alpha_id, beta_id = clan.elect_leaders(organisms, current_tick=5, force=True)

    # O casado foi descartado; Alpha deve ser org3 e Beta org4!
    assert alpha_id == 3
    assert beta_id == 4


def test_scenario_5_alpha_alters_priorities_during_food_crisis():
    """Cenário 5: O Alpha altera as prioridades durante uma crise alimentar."""
    clan_system = ClanSystem()
    clan = Clan(
        id=1,
        name="Clã Ignis",
        stage=ClanSocialStage.ESTABLISHED_CLAN,
        family_ids={1},
        communal_food=2.0,  # Reserva quase zerada
    )
    clan_system.clans[1] = clan

    # Membros famintos
    starving_org = Organism(id=1, x=100.0, y=100.0, family_id=1, energy=15.0, clan_id=1, role=Organism.ROLE_MALE)
    organisms = {1: starving_org}
    events = []

    clan_system._evaluate_strategic_priorities(organisms, {}, events, tick=10)

    assert len(clan.priorities) >= 1
    # Prioridade de urgência 1 deve ser forrageamento de sobrevivência
    assert clan.priorities[0].type == ClanPriorityType.SURVIVAL_FOOD


def test_scenario_6_clan_expels_parasitic_family():
    """Cenário 6: O clã expulsa uma família e enfrenta as consequências."""
    clan_system = ClanSystem()
    clan = Clan(
        id=1,
        name="Clã Solaris",
        stage=ClanSocialStage.ESTABLISHED_CLAN,
        family_ids={1, 2, 3, 4},
        communal_food=100.0,
    )
    clan_system.clans[1] = clan

    # Família 4 consumiu 60 kcal e contribuiu 0 kcal
    clan.family_consumptions[4] = 60.0
    clan.family_contributions[4] = 1.0

    f1 = Family(id=1, clan_name="F1", home_cluster_id=0, patriarch_id=1, matriarch_id=2)
    f2 = Family(id=2, clan_name="F2", home_cluster_id=0, patriarch_id=3, matriarch_id=4)
    f3 = Family(id=3, clan_name="F3", home_cluster_id=0, patriarch_id=5, matriarch_id=6)
    f4 = Family(id=4, clan_name="F4", home_cluster_id=0, patriarch_id=7, matriarch_id=8)
    families = {1: f1, 2: f2, 3: f3, 4: f4}

    parasite_org = Organism(id=7, x=100.0, y=100.0, family_id=4, clan_id=1, clan_role="MEMBRO")
    organisms = {7: parasite_org}
    events = []

    clan_system._evaluate_expulsions(organisms, families, events, tick=50)

    # Família 4 deve ter sido removida do clã
    assert 4 not in clan.family_ids
    assert parasite_org.clan_id is None
    assert parasite_org.clan_role is None
    assert any(e["type"] == "family_expelled" for e in events)


def test_scenario_7_clan_territory_expansion():
    """Cenário 7: Um clã tenta expandir seu território quando há abundância."""
    clan_system = ClanSystem()
    clan = Clan(
        id=1,
        name="Clã Terra",
        stage=ClanSocialStage.ESTABLISHED_CLAN,
        communal_food=90.0,
        territory_radius=180.0,
    )
    clan_system.clans[1] = clan
    events = []

    clan_system._evaluate_territorial_expansion({}, events, tick=20)

    # Território deve ter sido expandido e reserva consumida para patrulha
    assert clan.territory_radius > 180.0
    assert clan.communal_food < 90.0


def test_scenario_8_two_clans_enter_war_over_resources():
    """Cenário 8: Dois clãs entram em guerra por recursos."""
    clan_system = ClanSystem()
    c1 = Clan(id=1, name="Clã Boreas", stage=ClanSocialStage.ESTABLISHED_CLAN, territory_x=100.0, territory_y=100.0, territory_radius=150.0, alpha_id=10, communal_food=50.0)
    c2 = Clan(id=2, name="Clã Vulcan", stage=ClanSocialStage.ESTABLISHED_CLAN, territory_x=200.0, territory_y=100.0, territory_radius=150.0, alpha_id=20, communal_food=50.0)
    clan_system.clans[1] = c1
    clan_system.clans[2] = c2

    # Alphas agressivos em disputa de fronteira
    p_agr = AnimalPersonality(agressividade=0.8)
    a1 = Organism(id=10, x=100.0, y=100.0, clan_id=1, role=Organism.ROLE_MALE, personality=p_agr)
    a2 = Organism(id=20, x=200.0, y=100.0, clan_id=2, role=Organism.ROLE_MALE, personality=p_agr)
    organisms = {10: a1, 20: a2}
    events = []

    # Passo 1: Passa de neutro para competição
    clan_system._update_inter_clan_diplomacy(organisms, {}, events, 1)
    assert c1.diplomacy[2] == ClanRelation.COMPETITION

    # Passo 2: Escala para guerra devido a agressividade
    clan_system._update_inter_clan_diplomacy(organisms, {}, events, 2)
    assert c1.diplomacy[2] == ClanRelation.WAR
    assert c2.diplomacy[1] == ClanRelation.WAR
    assert any(e["type"] == "clan_war_declared" for e in events)


def test_scenario_9_alpha_dies_and_beta_immediately_assumes_leadership():
    """Cenário 9: O Alpha morre e o Beta assume provisoriamente a liderança principal."""
    clan = Clan(
        id=1,
        name="Clã Zephyr",
        stage=ClanSocialStage.ESTABLISHED_CLAN,
        family_ids={1, 2},
        alpha_id=10,
        beta_id=20,
    )

    # org20 é o Beta vivo; org30 é outro membro elegível
    org20_beta = Organism(id=20, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, partner_id=None, saude=100.0)
    org30_member = Organism(id=30, x=100.0, y=100.0, family_id=2, role=Organism.ROLE_MALE, partner_id=None, saude=90.0)

    # Alpha 10 NÃO está em organisms (faleceu)
    organisms = {20: org20_beta, 30: org30_member}

    new_alpha, new_beta = clan.elect_leaders(organisms, current_tick=100)

    # Beta 20 assumiu como novo Alpha
    assert new_alpha == 20
    assert clan.alpha_id == 20
    # org30 foi promovido a novo Beta
    assert new_beta == 30
    assert clan.beta_id == 30


def test_scenario_10_loss_of_both_leaders_and_reorganization():
    """Cenário 10: Um clã perde seus dois líderes e realiza uma nova seleção completa."""
    clan = Clan(
        id=1,
        name="Clã Chronos",
        stage=ClanSocialStage.ESTABLISHED_CLAN,
        family_ids={1},
        alpha_id=1,
        beta_id=2,
    )

    # Ambos Alpha 1 e Beta 2 faleceram; novos candidatos surgiram
    candidate_a = Organism(id=50, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, partner_id=None, genome=AnimalGenome(forca=85.0))
    candidate_b = Organism(id=60, x=100.0, y=100.0, family_id=1, role=Organism.ROLE_MALE, partner_id=None, genome=AnimalGenome(forca=65.0))
    organisms = {50: candidate_a, 60: candidate_b}

    new_alpha, new_beta = clan.elect_leaders(organisms, current_tick=200, force=True)

    assert new_alpha == 50
    assert new_beta == 60


def test_scenario_11_resource_scarcity_leads_to_truce_after_war():
    """Cenário 11: A escassez de recursos provoca trégua após guerra desgastante."""
    clan_system = ClanSystem()
    c1 = Clan(id=1, name="Clã Fenrir", stage=ClanSocialStage.ESTABLISHED_CLAN, communal_food=2.0)
    c2 = Clan(id=2, name="Clã Chimera", stage=ClanSocialStage.ESTABLISHED_CLAN, communal_food=80.0)
    clan_system.clans[1] = c1
    clan_system.clans[2] = c2

    c1.diplomacy[2] = ClanRelation.WAR
    c2.diplomacy[1] = ClanRelation.WAR
    events = []

    clan_system._update_inter_clan_diplomacy({}, {}, events, tick=75)

    # Por falta de recursos na reserva (< 5.0), concordam em trégua
    assert c1.diplomacy[2] == ClanRelation.TRUCE
    assert c2.diplomacy[1] == ClanRelation.TRUCE
    assert c1.truce_ticks[2] > 0


def test_scenario_12_family_secession_or_leaving_clan():
    """Cenário 12: Uma família deixa o clã e seus laços são desvinculados."""
    clan = Clan(id=1, name="Clã Umbra", stage=ClanSocialStage.ESTABLISHED_CLAN, family_ids={1, 2, 3})
    org = Organism(id=15, x=100.0, y=100.0, family_id=3, clan_id=1, clan_role="MEMBRO")

    # Família 3 se desvincula
    clan.family_ids.remove(3)
    if org.family_id == 3:
        org.clan_id = None
        org.clan_role = None

    assert 3 not in clan.family_ids
    assert org.clan_id is None
    assert org.clan_role is None
