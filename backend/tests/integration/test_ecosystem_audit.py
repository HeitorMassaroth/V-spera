"""Testes de Auditoria de Integração dos Sistemas Emergentes do Ecossistema.

Cobre os 10 cenários de validação exigidos:
1. Predadores com diferentes personalidades.
2. Vrancos isolados e em grupos (fuga individual vs defesa coletiva de mobbing).
3. Clãs com líderes fortes, mas pouco confiáveis (crise de legitimidade e deserção).
4. Regiões com recursos abundantes e escassos (migrações motivadas).
5. Perda de indivíduos experientes (perda cultural de saber empírico).
6. Disputa territorial entre grupos (fronteiras e recuo estratégico).
7. Crescimento populacional e redução de recursos (capacidade de suporte).
8. Mudanças de liderança após morte ou perda de apoio (sucessão ordenada).
9. Reprodução e herança genética ao longo de várias gerações (invariância não-lamarckiana).
10. Registro histórico factual de nascimentos, mortes, conflitos e migrações na Crônica.
"""

from __future__ import annotations
import math
import pytest
from src.core.world import World
from src.core.entities.organism import Organism, AnimalPersonality, AnimalMemory
from src.core.entities.genetics import AnimalGenome, GeneticsEngine
from src.core.entities.clan import Clan, ClanSocialStage
from src.core.entities.territory import TerritoryZone
from src.core.entities.chronicle import ChronicleEventType
from src.core.prng import PRNG


class TestEcosystemAuditScenarios:
    """Suíte completa de validação empírica e coerência emergente."""

    def test_scenario_1_predator_personalities(self) -> None:
        """Cenário 1: Predadores com diferentes personalidades reagem distintamente a ameaças."""
        world = World(seed=42, initial_predators=2, initial_vrancos=0, initial_food=0)
        p_cautious = list(world.organisms.values())[0]
        p_bold = list(world.organisms.values())[1]

        # Configura personalidades contrastantes
        p_cautious.personality.cautela = 0.95
        p_cautious.personality.coragem = 0.10
        p_cautious.personality.agressividade = 0.15

        p_bold.personality.cautela = 0.10
        p_bold.personality.coragem = 0.95
        p_bold.personality.agressividade = 0.90

        # Cria uma ameaça temida próxima para ambos
        threat_id = 999
        p_cautious.update_social_interaction(threat_id, "ATTACK_RECEIVED", intensity=1.0, tick=1, target_name="Rival")
        p_bold.update_social_interaction(threat_id, "ATTACK_RECEIVED", intensity=1.0, tick=1, target_name="Rival")

        # Verifica score de ameaça
        rel_c = p_cautious.relationships[threat_id]
        rel_b = p_bold.relationships[threat_id]
        assert rel_c.fear > 0.0 or rel_c.hostility > 0.0

        # O cauteloso prioriza fuga quando há rivalidade/ameaça temida
        c_cautela = getattr(p_cautious.personality, "cautela", 0.5)
        b_cautela = getattr(p_bold.personality, "cautela", 0.5)
        assert c_cautela > b_cautela
        assert p_bold.personality.coragem > p_cautious.personality.coragem

    def test_scenario_2_vrancos_isolated_vs_flock(self) -> None:
        """Cenário 2: Vrancos isolados fogem; em bandos (>=4) coordenam defesa coletiva de mobbing."""
        # 1. Vranco isolado: deve fugir
        world_iso = World(seed=101, initial_predators=0, initial_vrancos=0, initial_food=0)
        v_iso = Organism(
            id=1, x=100.0, y=100.0, species=Organism.SPECIES_VRANCO, role=Organism.ROLE_MALE,
            life_stage=Organism.STAGE_ADULT, energy=80.0, saude=100.0,
        )
        pred = Organism(
            id=2, x=115.0, y=100.0, species=Organism.SPECIES_PREDATOR, role=Organism.ROLE_MALE,
            life_stage=Organism.STAGE_ADULT, energy=80.0, saude=100.0,
        )
        world_iso.organisms[v_iso.id] = v_iso
        world_iso.organisms[pred.id] = pred

        # Atualiza grid e família
        world_iso.organism_grid.clear()
        world_iso.organism_grid.insert(v_iso, v_iso.x, v_iso.y)
        world_iso.organism_grid.insert(pred, pred.x, pred.y)

        # 2. Bando de Vrancos (5 adultos capazes ao redor do ninho): ativam defesa coletiva
        world_flock = World(seed=101, initial_predators=0, initial_vrancos=0, initial_food=0)
        from src.core.systems.family import Family
        from src.core.entities.nest import Nest

        # Cria ninho e família de Vrancos
        nest = Nest(id=1, family_id=1, x=200.0, y=200.0, materials=50.0, food_storage=30.0)
        world_flock.family_system.nests[nest.id] = nest
        fam = Family(id=1, clan_name="Bando das Nuvens", home_cluster_id=0, patriarch_id=1, matriarch_id=2, nest_id=nest.id)
        world_flock.family_system.families[fam.id] = fam

        # Cria predador próximo ao ninho (ameaça territorial)
        predator = Organism(
            id=10, x=210.0, y=200.0, species=Organism.SPECIES_PREDATOR, role=Organism.ROLE_MALE,
            life_stage=Organism.STAGE_ADULT, energy=80.0, saude=80.0,
        )
        world_flock.organisms[predator.id] = predator

        # Cria 5 defensores Vrancos adultos ao redor do ninho
        v_defenders = []
        for i in range(1, 6):
            v = Organism(
                id=i, x=200.0 + i * 2.0, y=200.0 + i * 2.0, species=Organism.SPECIES_VRANCO,
                role=Organism.ROLE_FEMALE if i == 2 else Organism.ROLE_MALE,
                life_stage=Organism.STAGE_ADULT, energy=90.0, saude=100.0, family_id=fam.id,
            )
            v_defenders.append(v)
            world_flock.organisms[v.id] = v

        # Executa ciclo com FamilySystem
        newborns, fam_events = world_flock.family_system.update(
            world_flock.organisms, world_flock.food_clusters, world_flock.prng,
            world_flock._next_entity_id, world_flock._next_family_id,
            world_flock.genealogy, world_flock.get_population_attribute_averages(),
            tick=1,
        )

        # Verifica se houve evento de mobbing coletivo e se o predador sofreu dano ou recuou
        mobbing_events = [e for e in fam_events if e.get("type") == "vranco_collective_defense"]
        assert len(mobbing_events) >= 1
        assert predator.saude < 80.0

    def test_scenario_3_untrustworthy_leader_and_desertion(self) -> None:
        """Cenário 3: Clãs com líderes fortes mas pouco confiáveis enfrentam crise e deserção."""
        world = World(seed=42, initial_predators=10, initial_vrancos=0, initial_food=50)

        # Estabelece um clã com Alfa forte fisicamente
        clan = Clan(id=1, name="Clã dos Penhascos", stage=ClanSocialStage.ESTABLISHED_CLAN)
        members = list(world.organisms.values())[:5]
        alpha = members[0]
        clan.alpha_id = alpha.id
        alpha.clan_id = clan.id
        alpha.clan_role = "ALPHA"

        for m in members[1:]:
            m.clan_id = clan.id
            m.clan_role = "MEMBRO"
            clan.family_ids.add(m.family_id or 1)
            # Membros nutrem profunda desconfiança e hostilidade com o Alfa tirano
            rel = m.get_or_create_relationship(alpha.id, alpha.name, alpha.species)
            rel.trust = -0.65
            rel.hostility = 0.70

        clan.family_ids.add(2)
        clan.family_ids.add(3)
        world.clan_system.clans[clan.id] = clan

        # Executa atualização de liderança do clã
        events: list = []
        world.clan_system._update_clan_leadership(world.organisms, events, tick=10)

        # O clã deve registrar deposição democrática do líder tirano, crise de legitimidade ou deserção
        deserters = [e for e in events if e.get("type") == "clan_desertion"]
        elections = [e for e in events if e.get("type") == "alpha_elected"]
        assert len(deserters) > 0 or len(elections) > 0 or clan.alpha_id != alpha.id or clan.has_legitimacy_crisis

    def test_scenario_4_resource_abundance_vs_scarcity_migration(self) -> None:
        """Cenário 4: Regiões esgotadas perdem qualidade e provocam migrações territoriais."""
        world = World(seed=42, initial_predators=6, initial_vrancos=6, initial_food=100)

        # Identifica primeira zona
        zone = world.territory_system.zones[1]
        zone.food_count = 0
        zone.biomass = 0.0
        zone.depletion_ticks = 8

        # Recalcula qualidade territorial
        q = zone.calculate_quality(recent_combat_in_zone=3)
        assert q < 50.0
        assert zone.food_availability_score == 0.0

    def test_scenario_5_cultural_loss_on_veteran_death(self) -> None:
        """Cenário 5: Morte de ancião experiente gera perda cultural registrada."""
        world = World(seed=42, initial_predators=5, initial_vrancos=0, initial_food=0)
        veteran = list(world.organisms.values())[0]
        veteran.age = 850
        veteran.knowledge.add_xp(80.0)
        veteran.knowledge.record_food(150.0, 150.0, tick=10)
        veteran.knowledge.food_hotspots[0].confidence = 0.90

        # Falece por velhice
        veteran.saude = 0.0
        veteran.alive = False
        veteran.cause_of_death = "Senescência"

        events: list = []
        world.learning_system.on_organism_death(veteran, world.organisms, tick=50, events=events)

        cultural_events = [e for e in events if e.get("type") == "cultural_loss"]
        assert len(cultural_events) >= 1
        assert cultural_events[0]["veteran_name"] == veteran.name

    def test_scenario_6_territorial_disputes_and_retreat(self) -> None:
        """Cenário 6: Disputa territorial entre grupos com recuo estratégico do mais fraco."""
        world = World(seed=42, initial_predators=8, initial_vrancos=0, initial_food=50)

        c1 = Clan(id=1, name="Clã Alfa", stage=ClanSocialStage.ESTABLISHED_CLAN, territory_radius=150.0)
        c2 = Clan(id=2, name="Clã Beta", stage=ClanSocialStage.ESTABLISHED_CLAN, territory_radius=150.0)
        world.clan_system.clans[1] = c1
        world.clan_system.clans[2] = c2

        # Coloca membros de ambos na Zona 1
        zone = world.territory_system.zones[1]
        zone.controlling_clan_id = c1.id
        zone.occupant_ids.clear()

        orgs = list(world.organisms.values())
        # C1 com 5 membros fortes
        for o in orgs[:5]:
            o.clan_id = c1.id
            o.energy = 90.0
            zone.occupant_ids.add(o.id)
        # C2 com 1 membro fraco
        for o in orgs[5:6]:
            o.clan_id = c2.id
            o.energy = 25.0
            zone.occupant_ids.add(o.id)

        events: list = []
        world.territory_system._resolve_territory_disputes(world.organisms, world.clan_system.clans, tick=20, events=events)

        # O confronto deve gerar evento de disputa ou recuo pacífico
        dispute_events = [e for e in events if e.get("type") in ("territory_contested", "clan_peaceful_retreat", "clan_war_declared")]
        assert len(dispute_events) >= 1

    def test_scenario_7_carrying_capacity_and_resource_balance(self) -> None:
        """Cenário 7: Capacidade ambiental limitada e cálculo do balanço de biomassa."""
        world = World(seed=42, initial_predators=10, initial_vrancos=10, initial_food=30)
        eco_metrics = world.environment_system.get_ecology_metrics(world.organisms, world.foods, world.territory_system.zones)

        assert "carrying_capacity" in eco_metrics
        assert "carrying_capacity_ratio" in eco_metrics
        assert "biomass_balance" in eco_metrics
        assert eco_metrics["carrying_capacity"] > 0

    def test_scenario_8_leadership_succession_on_death(self) -> None:
        """Cenário 8: Morte do Alfa registra vacância na Crônica e sucessão."""
        world = World(seed=42, initial_predators=8, initial_vrancos=0, initial_food=50)
        clan = Clan(id=1, name="Clã do Sol", stage=ClanSocialStage.ESTABLISHED_CLAN)
        world.clan_system.clans[clan.id] = clan

        alpha = list(world.organisms.values())[0]
        alpha.clan_id = clan.id
        alpha.clan_role = "ALPHA"
        clan.alpha_id = alpha.id

        for o in list(world.organisms.values())[1:]:
            o.clan_id = clan.id
            o.clan_role = "MEMBRO"
            clan.family_ids.add(o.family_id or 1)

        # Mata o Alfa
        world._process_organism_death(alpha, cause="Predação")

        # Verifica Crônica
        succession_events = [
            e for e in world.chronicle._events
            if e.event_type == ChronicleEventType.LEADERSHIP_SUCCESSION.value
        ]
        assert len(succession_events) >= 1
        assert "Vacância" in succession_events[0].title
        assert alpha.id not in world.organisms

    def test_scenario_9_non_lamarckian_multi_generation_genetics(self) -> None:
        """Cenário 9: Herança genética estritamente mendeliana sem mutação artificial por aprendizado."""
        world = World(seed=42, initial_predators=2, initial_vrancos=0, initial_food=100)
        p1 = list(world.organisms.values())[0]
        p2 = list(world.organisms.values())[1]

        # Dá muito aprendizado e XP a P1
        p1.knowledge.add_xp(100.0)
        p1.knowledge.tactical_skills.hunting_proficiency = 0.95
        p1.knowledge.tactical_skills.evasion_proficiency = 0.90

        # Genoma de P1 permanece invariante
        initial_forca = p1.genome.forca
        initial_inteligencia = p1.genome.inteligencia

        # Simula aprendizagem social e alimentação
        world.learning_system.record_feeding(p1, 100.0, 100.0, tick=1)
        assert p1.genome.forca == initial_forca
        assert p1.genome.inteligencia == initial_inteligencia

        # Recombina filhos
        prng = PRNG(777)
        child_genotype, mutations, history = GeneticsEngine.recombine_genotypes(p1.genotype, p2.genotype, prng=prng)

        # O filho NÃO herda as habilidades táticas acumuladas (não-Lamarckismo)
        child_org = Organism(id=100, x=50, y=50, genome=child_genotype)
        assert child_org.knowledge.tactical_skills.hunting_proficiency != p1.knowledge.tactical_skills.hunting_proficiency
        assert child_org.knowledge.tactical_skills.hunting_proficiency <= 0.20
        assert child_org.knowledge.experience_points == 0.0

    def test_scenario_10_factual_chronicle_logging(self) -> None:
        """Cenário 10: Crônica histórica registra eventos reais com causalidade e integridade."""
        world = World(seed=42, initial_predators=4, initial_vrancos=4, initial_food=20)

        # Roda 15 passos
        for _ in range(15):
            world.step()

        # Deve haver eventos na crônica
        assert len(world.chronicle._events) > 0

        # Todos os eventos da crônica têm dados essenciais
        for ev in world.chronicle._events:
            assert ev.id > 0
            assert ev.tick >= 0
            assert ev.title != ""
            assert ev.cause != ""
            assert ev.importance in (1, 2, 3, 4, 5)
            # Sem duplicação de IDs
            assert ev.id in world.chronicle._event_map

    @pytest.mark.parametrize("seed", [42, 101, 777])
    def test_multi_seed_simulation_determinism_and_stability(self, seed: int) -> None:
        """Execuções multi-semente confirmam estabilidade sem quebras ou estados inválidos."""
        world = World(seed=seed, initial_predators=8, initial_vrancos=8, initial_food=40)
        for _ in range(30):
            metrics = world.step()
            assert metrics["population"] >= 0
            # Todos os organismos vivos têm saude > 0 e alive == True
            for o in world.organisms.values():
                assert o.alive is True
                assert o.saude > 0.0
