"""Testes unitários e de integração para o Sistema de Relações Sociais e Reputação."""

import pytest
import math
from src.core.entities.organism import Organism
from src.core.entities.social import (
    SocialRelationship,
    calculate_candidate_support,
    DEFAULT_CLAN_ELECTION_WEIGHTS,
)
from src.core.entities.genetics import GeneticsEngine, AnimalPersonality
from src.core.entities.clan import Clan, ClanSocialStage
from src.core.systems.movement import MovementSystem
from src.core.prng import PRNG


def create_test_organism(
    oid: int,
    species: str = Organism.SPECIES_PREDATOR,
    role: str = Organism.ROLE_MALE,
    coragem: float = 0.5,
    agressividade: float = 0.5,
    sociabilidade: float = 0.5,
    cautela: float = 0.5,
) -> Organism:
    """Helper para criar organismos com personalidade customizada."""
    prng = PRNG(42 + oid)
    is_vranco = (species == Organism.SPECIES_VRANCO)
    genome = GeneticsEngine.generate_random_genome(prng, is_vranco=is_vranco)
    personality = AnimalPersonality(
        coragem=coragem,
        agressividade=agressividade,
        sociabilidade=sociabilidade,
        curiosidade=0.5,
        cautela=cautela,
        protecao=0.5,
        persistencia=0.5,
    )
    return Organism(
        id=oid,
        x=100.0 + oid * 10.0,
        y=100.0 + oid * 10.0,
        name=f"Animal_{oid}",
        vx=0.0,
        vy=0.0,
        energy=80.0,
        saude=100.0,
        species=species,
        genome=genome,
        personality=personality,
        role=role,
        sex="M" if role == Organism.ROLE_MALE else "F",
        life_stage=Organism.STAGE_ADULT,
    )


class TestSocialRelationships:
    """Testes dos 7 cenários obrigatórios de relações sociais e reputação."""

    def test_1_relationships_change_after_significant_events(self):
        """1. Relações mudam conforme os acontecimentos (ajuda, ataque, partilha, deserção)."""
        a1 = create_test_organism(1, Organism.SPECIES_PREDATOR)
        a2 = create_test_organism(2, Organism.SPECIES_PREDATOR)

        # Baseline inicial padrão entre predadores não aparentados
        rel = a1.get_or_create_relationship(a2.id, a2.name, a2.species)
        assert rel.trust == pytest.approx(0.50, 0.05)
        assert rel.affinity == pytest.approx(0.50, 0.05)
        assert rel.fear == 0.0
        assert rel.hostility == 0.0

        # Evento: A2 ajuda A1 (HELP_RECEIVED)
        a1.update_social_interaction(a2.id, "HELP_RECEIVED", intensity=0.8, tick=10)
        assert a1.relationships[a2.id].trust > 0.50
        assert a1.relationships[a2.id].affinity > 0.50
        assert a1.relationships[a2.id].cooperation_count == 1

        # Evento: Partilha de recursos fortalece ainda mais a cooperação
        a1.update_social_interaction(a2.id, "RESOURCE_SHARING", intensity=0.7, tick=15)
        assert a1.relationships[a2.id].trust > 0.65
        assert a1.relationships[a2.id].cooperation_count == 2

        # Uma única interação não transforma instantaneamente em aliado inseparável (+1.0)
        assert a1.relationships[a2.id].trust < 1.0

        # Outro animal A3 ataca A1 repetidamente
        a3 = create_test_organism(3, Organism.SPECIES_PREDATOR)
        a1.update_social_interaction(a3.id, "ATTACK_RECEIVED", intensity=0.9, tick=20)
        rel3 = a1.relationships[a3.id]
        assert rel3.trust < 0.30
        assert rel3.hostility > 0.25
        assert rel3.fear > 0.10

        # Segundo ataque intensifica medo e hostilidade
        a1.update_social_interaction(a3.id, "ATTACK_RECEIVED", intensity=0.9, tick=25)
        assert rel3.trust < 0.0
        assert rel3.hostility > 0.50
        assert rel3.fear > 0.35

    def test_2_allies_influence_cooperative_decisions_and_steering(self):
        """2. Aliados e parentes influenciam decisões de aproximação e cooperação."""
        movement = MovementSystem(world_width=1200.0, world_height=800.0)
        prng = PRNG(123)

        pup = create_test_organism(10, Organism.SPECIES_PREDATOR, role=Organism.ROLE_CHILD)
        parent = create_test_organism(11, Organism.SPECIES_PREDATOR, role=Organism.ROLE_FEMALE)
        pup.mother_id = parent.id
        pup.parent_id = parent.id

        # Parentesco estabelece alta confiança e afinidade mútua de base
        rel = pup.get_or_create_relationship(parent.id, parent.name, parent.species)
        assert rel.trust >= 0.85
        assert rel.affinity >= 0.85

        # Em posição próxima mas separada, filhote é atraído na direção do parente/aliado
        pup.x, pup.y = 200.0, 200.0
        parent.x, parent.y = 240.0, 200.0

        class MockGrid:
            def query_radius(self, x, y, r):
                return [(parent, 40.0)]

        steer_x, steer_y = movement.calculate_steering(pup, None, prng, organism_grid=MockGrid())
        # Deve ter componente de força positiva em X (em direção à mãe em 240.0)
        assert steer_x > 0.0

    def test_3_rivalries_affect_approach_and_confrontation(self):
        """3. Rivalidades afetam confrontos e geram evasão cautelosa."""
        movement = MovementSystem(world_width=1200.0, world_height=800.0)
        prng = PRNG(99)

        predator1 = create_test_organism(20, Organism.SPECIES_PREDATOR, coragem=0.3, cautela=0.8)
        predator2 = create_test_organism(21, Organism.SPECIES_PREDATOR, coragem=0.8, cautela=0.2)

        # Configura relacionamento com rivalidade e medo significativo
        rel = predator1.get_or_create_relationship(predator2.id, predator2.name, predator2.species)
        rel.fear = 0.70
        rel.hostility = 0.60
        rel.rivalry = 0.50

        predator1.x, predator1.y = 300.0, 300.0
        predator2.x, predator2.y = 330.0, 300.0

        class MockGrid:
            def query_radius(self, x, y, r):
                return [(predator2, 30.0)]

        steer_x, steer_y = movement.calculate_steering(predator1, None, prng, organism_grid=MockGrid())
        # Predador cauteloso com medo do rival foge (força negativa em X, afastando-se de 330.0)
        assert steer_x < 0.0
        assert predator1.current_state == Organism.STATE_FLEEING

    def test_4_trust_and_relationships_change_and_decay_over_time(self):
        """4. Confiança e hostilidade decaem suavemente ao longo do tempo na ausência de interações."""
        org1 = create_test_organism(30, Organism.SPECIES_PREDATOR)
        rel = org1.get_or_create_relationship(31, "Vizinho", Organism.SPECIES_PREDATOR)

        # Define estado de medo e hostilidade temporários por atrito pontual
        rel.fear = 0.60
        rel.hostility = 0.70
        rel.trust = 0.20
        rel.cooperation_count = 3
        rel.last_interaction_tick = 100

        # Passados 200 ticks sem interação, decaimento gradual
        rel.decay(elapsed_ticks=200, rate=0.001)

        # Medo e hostilidade diminuíram em direção a zero
        assert rel.fear < 0.60
        assert rel.hostility < 0.70
        # Confiança regressou gradualmente em direção ao baseline neutro (0.50)
        assert rel.trust > 0.20
        # Histórico de cooperação permanente é preservado
        assert rel.cooperation_count == 3

    def test_5_leaders_can_lose_approval_and_face_legitimacy_crisis(self):
        """5. Líderes de clã podem perder apoio dos membros e enfrentar crise de legitimidade."""
        clan = Clan(
            id=1,
            name="Clã Titan",
            stage=ClanSocialStage.ESTABLISHED_CLAN,
            family_ids={1, 2, 3},
            communal_food=40.0,
        )

        alpha = create_test_organism(100, Organism.SPECIES_PREDATOR)
        challenger = create_test_organism(101, Organism.SPECIES_PREDATOR)
        member1 = create_test_organism(102, Organism.SPECIES_PREDATOR)
        member2 = create_test_organism(103, Organism.SPECIES_PREDATOR)
        member3 = create_test_organism(104, Organism.SPECIES_PREDATOR)

        all_orgs = {
            alpha.id: alpha,
            challenger.id: challenger,
            member1.id: member1,
            member2.id: member2,
            member3.id: member3,
        }
        for o in all_orgs.values():
            o.clan_id = clan.id
            o.clan_role = "MEMBRO"
        alpha.clan_role = "ALPHA"
        clan.alpha_id = alpha.id

        # Membros têm desconfiança profunda e hostilidade contra o Alpha atual
        for m in (member1, member2, member3):
            rel = m.get_or_create_relationship(alpha.id, alpha.name, alpha.species)
            rel.trust = -0.50
            rel.hostility = 0.75
            rel.affinity = -0.40

            # E apoiam o desafiante com alta confiança e histórico de cooperação
            rel_c = m.get_or_create_relationship(challenger.id, challenger.name, challenger.species)
            rel_c.trust = 0.85
            rel_c.cooperation_count = 5
            rel_c.affinity = 0.80

        # Calcula suporte eleitoral
        alpha_score, alpha_trust, alpha_approval = calculate_candidate_support(alpha, [member1, member2, member3])
        chal_score, chal_trust, chal_approval = calculate_candidate_support(challenger, [member1, member2, member3])

        # Alpha perdeu aprovação da maioria (0% dos membros aprovam)
        assert alpha_approval == 0.0
        assert alpha_trust < 0.0
        assert chal_approval == 100.0
        assert chal_trust > 0.70

        # Executa eleição no clã
        clan.elect_leaders(all_orgs, current_tick=50, force=False)

        # O desafiante legítimo depõe o antigo Alpha desacreditado!
        assert clan.alpha_id == challenger.id
        assert clan.alpha_approval_rating >= 80.0
        assert not clan.has_legitimacy_crisis

    def test_6_vranco_species_remains_socially_cohesive(self):
        """6. A espécie Vranco mantém coesão social inata e ausência de disputas fratricidas."""
        v1 = create_test_organism(201, Organism.SPECIES_VRANCO)
        v2 = create_test_organism(202, Organism.SPECIES_VRANCO)

        # Baseline inato entre Vrancos é altamente positivo e solidário
        rel = v1.get_or_create_relationship(v2.id, v2.name, v2.species)
        assert rel.trust >= 0.65
        assert rel.affinity >= 0.70
        assert rel.fear == 0.0
        assert rel.hostility == 0.0
        assert rel.rivalry == 0.0

        # Cooperação em cuidados aloparentais intensifica o vínculo
        v1.update_social_interaction(v2.id, "COOPERATION", intensity=0.7, tick=10)
        assert v1.relationships[v2.id].trust >= 0.70
        assert v1.relationships[v2.id].cooperation_count == 1

        # Relação contra predador desenvolve medo/hostilidade seletivos, sem afetar companheiros de bando
        pred = create_test_organism(300, Organism.SPECIES_PREDATOR)
        rel_pred = v1.get_or_create_relationship(pred.id, pred.name, pred.species)
        assert rel_pred.fear >= 0.40  # Medo natural de predador

    def test_7_bounded_memory_and_pruning_prevents_performance_degradation(self):
        """7. Limite seletivo de relações (max 15) descarta relações irrelevantes e protege parentes."""
        org = create_test_organism(400, Organism.SPECIES_PREDATOR)
        org.max_relationships = 15

        # Define parentes protegidos
        org.partner_id = 401
        org.father_id = 402
        org.mother_id = 403
        org.children_ids = [404]

        # Cria relacionamentos para parentes
        org.get_or_create_relationship(401, "Parceira", Organism.SPECIES_PREDATOR)
        org.get_or_create_relationship(402, "Pai", Organism.SPECIES_PREDATOR)
        org.get_or_create_relationship(403, "Mãe", Organism.SPECIES_PREDATOR)
        org.get_or_create_relationship(404, "Filhote", Organism.SPECIES_PREDATOR)

        # Adiciona um aliado relevante com alta cooperação
        for _ in range(5):
            org.update_social_interaction(600, "HELP_RECEIVED", intensity=0.9, tick=150, target_name="Grande Aliado")

        # Adiciona 20 transeuntes neutros com baixa relevância
        for i in range(500, 520):
            org.get_or_create_relationship(i, f"Transeunte_{i}", Organism.SPECIES_PREDATOR)

        # Executa poda
        org.prune_relationships()

        # Quantidade de relacionamentos armazenados respeita estritamente o teto
        assert len(org.relationships) <= org.max_relationships

        # Parentes protegidos NUNCA são descartados
        assert 401 in org.relationships
        assert 402 in org.relationships
        assert 403 in org.relationships
        assert 404 in org.relationships

        # Aliado relevante com alta significância social foi preservado
        assert 600 in org.relationships
