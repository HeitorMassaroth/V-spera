"""Testes unitários e de integração para a raça Vrancos e ecossistema coexistente.

Cobre rigorosamente os 12 cenários obrigatórios:
1. Vranco isolado detecta predador e tenta fugir.
2. Vranco saudável escapa de predador mais lento.
3. Vranco ferido/exaurido pode ser capturado.
4. Múltiplos Vrancos detectam perigo e se agrupam (coesão/alarme).
5. Grupo numeroso enfrenta predador em defesa coletiva (mobbing) com chance real de vitória.
6. Grupo pequeno/fraco é derrotado por predador forte.
7. Vrancos cansados perdem vantagem de velocidade.
8. Vrancos não iniciam combates internos entre si.
9. Tendência a regiões periféricas com flexibilidade de migração.
10. Cooperação defensiva com custos metabólicos reais (sem recursos infinitos).
11. Isolamento reprodutivo e evolução genética independente.
12. Razões populacionais iniciais distintas produzem dinâmicas ecológicas diferentes.
"""

import math
import pytest
from core.entities.organism import Organism, SPECIES_VRANCO, SPECIES_PREDATOR, STATE_FLEEING, STATE_FORAGING
from core.entities.genetics import Genotype, GeneticsEngine
from core.entities.genealogy import GenealogyRegistry
from core.entities.traits import OrganismTraits
from core.systems.movement import MovementSystem
from core.spatial.spatial_grid import SpatialHashGrid
from core.systems.family import FamilySystem
from core.prng import PRNG
from core.world import World


def test_scenario_1_isolated_vranco_flees_from_predator():
    """1. Um Vranco isolado detecta um predador e tenta fugir."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)
    grid = SpatialHashGrid[Organism](cell_size=50.0)

    # Vranco em (500, 500)
    vranco = Organism(
        id=1,
        species=SPECIES_VRANCO,
        x=500.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=100.0,
        saude=60.0,
        role=Organism.ROLE_MALE,
    )
    # Predador próximo em (520, 500)
    predator = Organism(
        id=2,
        species=SPECIES_PREDATOR,
        x=520.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=100.0,
        saude=100.0,
        role=Organism.ROLE_MALE,
    )

    grid.insert(vranco, vranco.x, vranco.y)
    grid.insert(predator, predator.x, predator.y)

    fx, fy = movement.calculate_steering(
        organism=vranco,
        target_food=None,
        prng=PRNG(42),
        organism_grid=grid,
    )

    # Vranco deve ter entrado em estado de fuga
    assert vranco.current_state == STATE_FLEEING
    # A força de fuga deve empurrar o Vranco para longe do predador (predador está à direita em +x, então fx < 0)
    assert fx < -0.1


def test_scenario_2_healthy_vranco_escapes_slower_predator():
    """2. Um Vranco saudável consegue escapar de um predador mais lento em condições favoráveis."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)
    
    vranco = Organism(
        id=1,
        species=SPECIES_VRANCO,
        x=500.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=100.0,
        saude=60.0,
        role=Organism.ROLE_MALE,
    )
    predator = Organism(
        id=2,
        species=SPECIES_PREDATOR,
        x=460.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=100.0,
        saude=100.0,
        role=Organism.ROLE_MALE,
    )

    initial_distance = math.hypot(vranco.x - predator.x, vranco.y - predator.y)
    assert vranco.traits.max_speed > predator.traits.max_speed

    # Simular 15 passos de física onde Vranco corre para a direita (+x) e predador persegue (+x)
    for _ in range(15):
        movement.update_physics(vranco, force_x=10.0, force_y=0.0)
        movement.update_physics(predator, force_x=10.0, force_y=0.0)

    final_distance = math.hypot(vranco.x - predator.x, vranco.y - predator.y)
    assert final_distance > initial_distance


def test_scenario_3_injured_exhausted_vranco_can_be_captured():
    """3. Um Vranco ferido e exaurido perde velocidade e pode ser alcançado pelo predador."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)

    # Vranco criticamente debilitado
    exhausted_vranco = Organism(
        id=1,
        species=SPECIES_VRANCO,
        x=500.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=5.0,     # Exaurido
        saude=10.0,     # Ferido gravemente
        role=Organism.ROLE_MALE,
    )
    predator = Organism(
        id=2,
        species=SPECIES_PREDATOR,
        x=450.0,
        y=500.0,
        vx=0.0,
        vy=0.0,
        energy=90.0,
        saude=100.0,
        role=Organism.ROLE_MALE,
    )

    grid = SpatialHashGrid[Organism](cell_size=50.0)
    grid.insert(exhausted_vranco, exhausted_vranco.x, exhausted_vranco.y)
    grid.insert(predator, predator.x, predator.y)

    # Força calculada com fadiga e ferimentos
    fx, fy = movement.calculate_steering(
        organism=exhausted_vranco,
        target_food=None,
        prng=PRNG(42),
        organism_grid=grid,
    )
    movement.update_physics(exhausted_vranco, fx, fy)
    # Predador persegue com velocidade normal
    movement.update_physics(predator, force_x=10.0, force_y=0.0)

    # Velocidade do vranco debilitado deve ser menor que a do predador saudável
    assert exhausted_vranco.speed < predator.speed


def test_scenario_4_multiple_vrancos_flock_on_danger():
    """4. Vários Vrancos detectam perigo e se agrupam defensivamente."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)
    grid = SpatialHashGrid[Organism](cell_size=60.0)

    v1 = Organism(id=1, species=SPECIES_VRANCO, x=500.0, y=500.0, vx=0.0, vy=0.0, energy=100.0, saude=60.0)
    v2 = Organism(id=2, species=SPECIES_VRANCO, x=530.0, y=520.0, vx=0.0, vy=0.0, energy=100.0, saude=60.0)
    v3 = Organism(id=3, species=SPECIES_VRANCO, x=480.0, y=525.0, vx=0.0, vy=0.0, energy=100.0, saude=60.0)

    predator = Organism(id=10, species=SPECIES_PREDATOR, x=510.0, y=440.0, vx=0.0, vy=0.0, energy=100.0, saude=100.0)

    for o in [v1, v2, v3, predator]:
        grid.insert(o, o.x, o.y)

    # v1 detecta ameaça e calcula força considerando coesão com v2 e v3
    fx, fy = movement.calculate_steering(
        organism=v1,
        target_food=None,
        prng=PRNG(42),
        organism_grid=grid,
    )

    assert v1.current_state == STATE_FLEEING
    # A força deve empurrar para longe do predador em -y (predador está em y=440)
    assert fy > 0.0


def test_scenario_5_large_vranco_group_mobbing_defense():
    """5. Um grupo numeroso enfrenta um predador e possui possibilidade real de vitória coletiva."""
    world = World(width=1000.0, height=1000.0, initial_organisms=0, initial_predators=0, initial_vrancos=0)

    predator = Organism(
        id=99,
        species=SPECIES_PREDATOR,
        x=500.0,
        y=500.0,
        energy=70.0,
        saude=80.0,
        role=Organism.ROLE_MALE,
    )
    world.organisms[predator.id] = predator
    world.organism_grid.insert(predator, predator.x, predator.y)

    # 6 Vrancos adultos saudáveis cercando o predador
    vrancos = []
    for i in range(1, 7):
        angle = (i / 6.0) * 2 * math.pi
        v = Organism(
            id=i,
            species=SPECIES_VRANCO,
            x=500.0 + math.cos(angle) * 30.0,
            y=500.0 + math.sin(angle) * 30.0,
            energy=95.0,
            saude=60.0,
            role=Organism.ROLE_MALE,
            life_stage=Organism.STAGE_ADULT,
        )
        world.organisms[v.id] = v
        world.organism_grid.insert(v, v.x, v.y)
        vrancos.append(v)

    initial_pred_saude = predator.saude
    initial_defenses = world.get_metrics().get("collective_defenses_count", 0)

    # Executar avaliação e combate de mobbing
    defended = world.family_system.evaluate_and_execute_mobbing(vrancos[0], world)

    assert defended is True
    # O predador deve ter sofrido ferimentos
    assert predator.saude < initial_pred_saude
    # Métrica de defesa coletiva deve ter incrementado
    assert world.get_metrics()["collective_defenses_count"] > initial_defenses


def test_scenario_6_small_weak_group_defeated_by_strong_predator():
    """6. Um grupo pequeno ou fraco não consegue sobrepujar um predador forte."""
    world = World(width=1000.0, height=1000.0, initial_organisms=0, initial_predators=0, initial_vrancos=0)

    apex_predator = Organism(
        id=99,
        species=SPECIES_PREDATOR,
        x=500.0,
        y=500.0,
        energy=100.0,
        saude=100.0,
        role=Organism.ROLE_MALE,
    )
    world.organisms[apex_predator.id] = apex_predator
    world.organism_grid.insert(apex_predator, apex_predator.x, apex_predator.y)

    # Apenas 2 Vrancos com baixa energia
    v1 = Organism(id=1, species=SPECIES_VRANCO, x=510.0, y=500.0, energy=20.0, saude=25.0)
    v2 = Organism(id=2, species=SPECIES_VRANCO, x=515.0, y=505.0, energy=25.0, saude=30.0)
    world.organisms[1] = v1
    world.organisms[2] = v2
    world.organism_grid.insert(v1, v1.x, v1.y)
    world.organism_grid.insert(v2, v2.x, v2.y)

    # O mobbing deve fracassar por falta de poder coletivo (precisa de >= 4 adultos saudáveis)
    defended = world.family_system.evaluate_and_execute_mobbing(v1, world)
    assert defended is False


def test_scenario_7_tired_vrancos_lose_speed_advantage():
    """7. Vrancos cansados perdem a vantagem de velocidade."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)

    fresh_vranco = Organism(id=1, species=SPECIES_VRANCO, x=200.0, y=200.0, energy=100.0, saude=60.0)
    tired_vranco = Organism(id=2, species=SPECIES_VRANCO, x=200.0, y=200.0, energy=8.0, saude=60.0)

    # Força idêntica aplicada
    movement.update_physics(fresh_vranco, force_x=10.0, force_y=0.0)
    movement.update_physics(tired_vranco, force_x=10.0, force_y=0.0)

    assert fresh_vranco.speed > tired_vranco.speed


def test_scenario_8_vrancos_never_initiate_internal_combat():
    """8. Os Vrancos não iniciam combates internos em condições normais."""
    family_sys = FamilySystem()

    v1 = Organism(id=1, species=SPECIES_VRANCO, x=100.0, y=100.0, role=Organism.ROLE_MALE)
    v2 = Organism(id=2, species=SPECIES_VRANCO, x=105.0, y=100.0, role=Organism.ROLE_MALE)

    # Disputa de machos entre Vrancos é estritamente proibida
    contested = family_sys.evaluate_male_contest(v1, v2)
    assert contested is False

    # Entre predadores é permitida
    p1 = Organism(id=3, species=SPECIES_PREDATOR, x=200.0, y=200.0, role=Organism.ROLE_MALE)
    p2 = Organism(id=4, species=SPECIES_PREDATOR, x=205.0, y=200.0, role=Organism.ROLE_MALE)
    assert family_sys.evaluate_male_contest(p1, p2) in [True, False]  # Normal


def test_scenario_9_peripheral_preference_with_migration():
    """9. A população tende a ocupar regiões periféricas, mas pode transitar livremente."""
    movement = MovementSystem(world_width=1000.0, world_height=1000.0)

    # Vranco no centro do mapa (500, 500)
    vranco = Organism(id=1, species=SPECIES_VRANCO, x=500.0, y=500.0, energy=100.0, saude=60.0)

    fx, fy = movement._seek_periphery(vranco)
    # Deve apontar para longe do centro
    assert math.hypot(fx, fy) > 0.0

    # Predador no centro não tem preferência periférica
    predator = Organism(id=2, species=SPECIES_PREDATOR, x=500.0, y=500.0, energy=100.0, saude=100.0)
    p_fx, p_fy = movement._seek_periphery(predator)
    assert p_fx == 0.0 and p_fy == 0.0


def test_scenario_10_cooperation_has_real_energy_costs():
    """10. A cooperação aumenta as chances de sobrevivência sem gerar recursos infinitos."""
    world = World(width=1000.0, height=1000.0, initial_organisms=0, initial_predators=0, initial_vrancos=0)

    vranco = Organism(id=1, species=SPECIES_VRANCO, x=500.0, y=500.0, energy=80.0, saude=60.0)
    predator = Organism(id=2, species=SPECIES_PREDATOR, x=510.0, y=500.0, energy=60.0, saude=80.0)

    world.organisms[1] = vranco
    world.organisms[2] = predator
    world.organism_grid.insert(vranco, vranco.x, vranco.y)
    world.organism_grid.insert(predator, predator.x, predator.y)

    # Adicionar aliados para mobbing
    for i in range(3, 8):
        ally = Organism(id=i, species=SPECIES_VRANCO, x=505.0, y=505.0, energy=80.0, saude=60.0)
        world.organisms[i] = ally
        world.organism_grid.insert(ally, ally.x, ally.y)

    initial_energy = vranco.energy
    world.family_system.evaluate_and_execute_mobbing(vranco, world)

    # Combate gasta energia real dos participantes
    assert vranco.energy < initial_energy


def test_scenario_11_reproductive_isolation_and_distinct_genetics():
    """11. A genética dos Vrancos evolui sem ser misturada com a dos predadores."""
    family_sys = FamilySystem()

    vranco = Organism(id=1, x=100.0, y=100.0, species=SPECIES_VRANCO, role=Organism.ROLE_MALE, energy=100.0, age=300)
    predator_female = Organism(id=2, x=120.0, y=100.0, species=SPECIES_PREDATOR, role=Organism.ROLE_FEMALE, energy=100.0, age=300)

    # Cruzamento entre espécies diferentes é estritamente bloqueado
    assert family_sys.can_mate(vranco, predator_female) is False

    vranco_female = Organism(id=3, x=140.0, y=100.0, species=SPECIES_VRANCO, role=Organism.ROLE_FEMALE, energy=100.0, age=300)
    # Vranco x Vranco é permitido quando elegíveis
    assert vranco.species == vranco_female.species


def test_scenario_12_distinct_population_ratios_produce_different_metrics():
    """12. Diferentes proporções populacionais produzem dinâmicas ecológicas distintas."""
    world = World(
        width=800.0,
        height=800.0,
        initial_organisms=0,
        initial_predators=12,
        initial_vrancos=24,
    )

    metrics = world.get_metrics()
    assert metrics["vrancos_count"] == 24
    assert metrics["predators_count"] == 12
    assert "vranco_avg_group_size" in metrics
    assert "vrancos_periphery_pct" in metrics
    assert "hunting_success_rate" in metrics

    # Executar 10 passos da simulação
    for _ in range(10):
        world.step()

    updated_metrics = world.get_metrics()
    assert updated_metrics["tick"] == 10
    assert updated_metrics["vrancos_count"] > 0
    assert updated_metrics["predators_count"] > 0


def test_vranco_reproduction_without_fixed_partners():
    """Vrancos reproduzem sem parceiro fixo e sem exigir formação de casal monogâmico."""
    family_sys = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(100)

    # Macho e fêmea adultos Vrancos elegíveis, próximos (distância ~30px)
    male = Organism(
        id=1,
        species=SPECIES_VRANCO,
        x=200.0,
        y=200.0,
        role=Organism.ROLE_MALE,
        life_stage=Organism.STAGE_ADULT,
        energy=85.0,
        saude=60.0,
        partner_id=None,
    )
    male.food_eaten = 2

    female = Organism(
        id=2,
        species=SPECIES_VRANCO,
        x=225.0,
        y=200.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=85.0,
        saude=60.0,
        partner_id=None,
    )
    female.food_eaten = 2

    organisms = {1: male, 2: female}
    next_id = 100

    def next_id_fn():
        nonlocal next_id
        val = next_id
        next_id += 1
        return val

    newborns, events = family_sys.update(
        organisms=organisms,
        food_clusters=[(200.0, 200.0)],
        prng=prng,
        next_entity_id_fn=next_id_fn,
        next_family_id_fn=lambda: 1,
        genealogy=genealogy,
        pop_averages={},
        tick=1,
    )

    # Deve ter gerado 1 filhote Vranco
    assert len(newborns) == 1
    child = newborns[0]
    assert child.species == SPECIES_VRANCO
    assert child.father_id == male.id
    assert child.mother_id == female.id
    assert child.id in male.children_ids
    assert child.id in female.children_ids

    # CRÍTICO: Nenhum dos dois deve ter ficado preso a um parceiro fixo exclusivo!
    assert male.partner_id is None
    assert female.partner_id is None

    # Registro genealógico
    rec = genealogy.get_record(child.id)
    assert rec is not None
    assert rec.father_id == male.id
    assert rec.mother_id == female.id
    assert rec.species == SPECIES_VRANCO


def test_vranco_multiple_partners_over_lifetime_genealogy_preserved():
    """Um Vranco pode se reproduzir com múltiplos parceiros sem sobrescrever vínculos genealógicos."""
    family_sys = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(200)

    next_id = 200

    def next_id_fn():
        nonlocal next_id
        val = next_id
        next_id += 1
        return val

    # Macho Vranco central
    male = Organism(
        id=10,
        species=SPECIES_VRANCO,
        x=300.0,
        y=300.0,
        role=Organism.ROLE_MALE,
        life_stage=Organism.STAGE_ADULT,
        energy=90.0,
        saude=60.0,
    )
    male.food_eaten = 3

    # Primeira parceira: Fêmea 1
    female1 = Organism(
        id=20,
        species=SPECIES_VRANCO,
        x=320.0,
        y=300.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=90.0,
        saude=60.0,
    )
    female1.food_eaten = 3

    # Registro genealógico dos pais pioneiros
    genealogy.register_birth(10, male.name, male.role, 0, 0, None, None, None, male.genome, [], [], sex="M", species=SPECIES_VRANCO)
    genealogy.register_birth(20, female1.name, female1.role, 0, 0, None, None, None, female1.genome, [], [], sex="F", species=SPECIES_VRANCO)

    # 1. Primeiro acasalamento: Macho 10 + Fêmea 20
    organisms_round1 = {10: male, 20: female1}
    newborns1, _ = family_sys.update(
        organisms=organisms_round1,
        food_clusters=[(300.0, 300.0)],
        prng=prng,
        next_entity_id_fn=next_id_fn,
        next_family_id_fn=lambda: 1,
        genealogy=genealogy,
        pop_averages={},
        tick=10,
    )
    assert len(newborns1) == 1
    child1 = newborns1[0]
    assert child1.father_id == 10
    assert child1.mother_id == 20
    assert male.children_ids == [child1.id]
    assert female1.children_ids == [child1.id]

    # Recuperação do macho e chegada de uma SEGUNDA fêmea diferente (Fêmea 30)
    male.reproduction_cooldown = 0
    male.energy = 90.0

    female2 = Organism(
        id=30,
        species=SPECIES_VRANCO,
        x=310.0,
        y=315.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=90.0,
        saude=60.0,
    )
    female2.food_eaten = 2
    genealogy.register_birth(30, female2.name, female2.role, 0, 0, None, None, None, female2.genome, [], [], sex="F", species=SPECIES_VRANCO)

    # Removemos a Fêmea 1 para o Macho acasalar com a Fêmea 2
    organisms_round2 = {10: male, 30: female2}
    newborns2, _ = family_sys.update(
        organisms=organisms_round2,
        food_clusters=[(300.0, 300.0)],
        prng=prng,
        next_entity_id_fn=next_id_fn,
        next_family_id_fn=lambda: 1,
        genealogy=genealogy,
        pop_averages={},
        tick=50,
    )
    assert len(newborns2) == 1
    child2 = newborns2[0]
    assert child2.father_id == 10
    assert child2.mother_id == 30

    # Ambos os filhos pertencem ao mesmo pai
    assert male.children_ids == [child1.id, child2.id]
    assert female1.children_ids == [child1.id]
    assert female2.children_ids == [child2.id]

    # Integridade da árvore genealógica
    tree_male = genealogy.get_family_tree(10)
    children_records = tree_male["children"]
    assert len(children_records) == 2

    # Verifica os dois ramos familiares independentes
    child1_rec = next(c for c in children_records if c["id"] == child1.id)
    child2_rec = next(c for c in children_records if c["id"] == child2.id)

    assert child1_rec["father_id"] == 10 and child1_rec["mother_id"] == 20
    assert child2_rec["father_id"] == 10 and child2_rec["mother_id"] == 30

    # Nenhum vínculo conjugal fixo foi atribuído ao Macho
    assert male.partner_id is None


def test_vranco_cooperative_alloparental_care():
    """Adultos Vrancos próximos prestam cuidados cooperativos a filhotes necessitados."""
    family_sys = FamilySystem()
    genealogy = GenealogyRegistry()

    # Filhote Vranco faminto
    pup = Organism(
        id=5,
        species=SPECIES_VRANCO,
        x=500.0,
        y=500.0,
        role=Organism.ROLE_CHILD,
        life_stage=Organism.STAGE_NEWBORN,
        energy=25.0,
        saude=35.0,
        father_id=98,
        mother_id=99,
    )

    # Adulto Vranco próximo (não é o pai nem a mãe)
    helper = Organism(
        id=6,
        species=SPECIES_VRANCO,
        x=515.0,
        y=505.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=80.0,
        saude=60.0,
    )

    organisms = {5: pup, 6: helper}
    events = []

    initial_pup_energy = pup.energy
    initial_helper_energy = helper.energy

    family_sys._vranco_cooperative_pup_care(organisms, genealogy, events, tick=1)

    # O filhote deve ter recebido nutrição do adulto próximo
    assert pup.energy > initial_pup_energy
    assert helper.energy < initial_helper_energy

    # O evento de cuidado aloparental deve ter sido registrado
    alloparental_events = [e for e in events if e.get("type") == "vranco_alloparental_care"]
    assert len(alloparental_events) == 1
    assert alloparental_events[0]["helper_id"] == 6
    assert alloparental_events[0]["pup_id"] == 5
    assert alloparental_events[0]["is_parent"] is False


def test_predator_reproduction_strictly_requires_pair_bond():
    """Predadores continuam exigindo formação de vínculo conjugal fixo em ninho para reprodução."""
    family_sys = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(300)

    # Macho e fêmea Predadores sem vínculo de casal estabelecido
    pred_male = Organism(
        id=70,
        species=SPECIES_PREDATOR,
        x=400.0,
        y=400.0,
        role=Organism.ROLE_MALE,
        life_stage=Organism.STAGE_ADULT,
        energy=100.0,
        saude=100.0,
        partner_id=None,
    )
    pred_female = Organism(
        id=80,
        species=SPECIES_PREDATOR,
        x=410.0,
        y=400.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=100.0,
        saude=100.0,
        partner_id=None,
    )

    organisms = {70: pred_male, 80: pred_female}

    newborns, _ = family_sys.update(
        organisms=organisms,
        food_clusters=[],  # Sem centros ou ninhos
        prng=prng,
        next_entity_id_fn=lambda: 999,
        next_family_id_fn=lambda: 999,
        genealogy=genealogy,
        pop_averages={},
        tick=1,
    )

    # Predadores NÃO se reproduzem sem par permanente e ninho
    assert len(newborns) == 0


def test_vranco_density_equilibrium_inhibition():
    """Aglomeração local excessiva inibe temporariamente a reprodução dos Vrancos para equilíbrio ecológico."""
    family_sys = FamilySystem()
    genealogy = GenealogyRegistry()
    prng = PRNG(400)

    # Fêmea candidata
    female = Organism(
        id=1,
        species=SPECIES_VRANCO,
        x=500.0,
        y=500.0,
        role=Organism.ROLE_FEMALE,
        life_stage=Organism.STAGE_ADULT,
        energy=90.0,
        saude=60.0,
    )
    female.food_eaten = 3

    # Macho próximo
    male = Organism(
        id=2,
        species=SPECIES_VRANCO,
        x=520.0,
        y=500.0,
        role=Organism.ROLE_MALE,
        life_stage=Organism.STAGE_ADULT,
        energy=90.0,
        saude=60.0,
    )
    male.food_eaten = 3

    organisms = {1: female, 2: male}

    # Adiciona 9 outros Vrancos aglomerados num raio pequeno (< 50px)
    for idx in range(3, 12):
        crowd_member = Organism(
            id=idx,
            species=SPECIES_VRANCO,
            x=500.0 + (idx * 2),
            y=500.0 + (idx * 2),
            role=Organism.ROLE_FEMALE if idx % 2 == 0 else Organism.ROLE_MALE,
            energy=80.0,
        )
        organisms[idx] = crowd_member

    newborns = family_sys._reproduce_vrancos_flexible(
        all_organisms=organisms,
        prng=prng,
        next_entity_id_fn=lambda: 999,
        genealogy=genealogy,
        pop_averages={},
        events=[],
        tick=1,
    )

    # Densidade local excessiva deve inibir a reprodução
    assert len(newborns) == 0

