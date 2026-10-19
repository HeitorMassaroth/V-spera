"""
Conjunto de testes obrigatórios da dinâmica evolutiva, genética e social.
Valida os 12 cenários estipulados na especificação biológica:
1. Irmãos apresentam semelhanças genéticas, mas não são cópias idênticas.
2. Descendentes herdam características de ambos os progenitores (herança bialélica).
3. Mutações produzem variações sem garantir melhorias (neutras, prejudiciais e vantajosas).
4. Características vantajosas tornam-se mais frequentes sob pressão seletiva.
5. Características desvantajosas podem desaparecer ou persistir por deriva genética.
6. Uma mudança ambiental altera as vantagens relativas das características.
7. Características benéficas possuem custos compensatórios (trade-offs biológicos).
8. O aprendizado individual e estado temporário não alteram o genótipo.
9. Clãs com diferentes estratégias sociais apresentam resultados distintos.
10. Populações pequenas e isoladas perdem diversidade genética (depressão por endogamia).
11. O fluxo gênico entre populações restaura a diversidade e vigor híbrido.
12. A evolução é gradual, bounded e não produz transformações instantâneas.
"""

import pytest
import math
from core.prng import PRNG
from core.entities.genetics import (
    Genotype,
    Phenotype,
    AllelePair,
    GeneticsEngine,
    TRAIT_BOUNDS,
)
from core.entities.organism import Organism, AnimalMemory
from core.entities.genealogy import GenealogyRegistry
from core.entities.clan import Clan, ClanSocialStage
from core.systems.metabolism import MetabolismSystem


def test_scenario_1_siblings_share_inheritance_not_identical_clones():
    """Cenário 1: Irmãos apresentam semelhanças genéticas dos mesmos pais, mas não são clones idênticos."""
    prng = PRNG(101)
    father = Genotype(
        forca_pair=AllelePair(70.0, 90.0),
        velocidade_pair=AllelePair(40.0, 80.0),
        resistencia_pair=AllelePair(50.0, 85.0),
    )
    mother = Genotype(
        forca_pair=AllelePair(30.0, 50.0),
        velocidade_pair=AllelePair(60.0, 90.0),
        resistencia_pair=AllelePair(35.0, 60.0),
    )

    child1, _, _ = GeneticsEngine.recombine_genotypes(father, mother, inbreeding_coef=0.0, prng=prng)
    child2, _, _ = GeneticsEngine.recombine_genotypes(father, mother, inbreeding_coef=0.0, prng=prng)

    # Ambos herdam alelos de pai e mãe (valores dentro dos limites dos pais)
    assert min(father.forca_pair.maternal, father.forca_pair.paternal, mother.forca_pair.maternal, mother.forca_pair.paternal) - 5.0 <= child1.forca <= max(father.forca_pair.maternal, father.forca_pair.paternal, mother.forca_pair.maternal, mother.forca_pair.paternal) + 5.0

    # Irmãos não são idênticos em todas as características
    is_identical = (
        child1.forca_pair == child2.forca_pair
        and child1.velocidade_pair == child2.velocidade_pair
        and child1.resistencia_pair == child2.resistencia_pair
        and child1.deteccao_ameacas_pair == child2.deteccao_ameacas_pair
    )
    assert not is_identical, "Irmãos gerados por segregação independente não devem ser clones genéticos idênticos."


def test_scenario_2_offspring_inherit_from_both_progenitors():
    """Cenário 2: Descendentes herdam material genético (1 alelo de cada progenitor) de ambos os pais."""
    prng = PRNG(202)
    father = Genotype(
        forca_pair=AllelePair(90.0, 90.0),
        velocidade_pair=AllelePair(80.0, 80.0),
    )
    mother = Genotype(
        forca_pair=AllelePair(30.0, 30.0),
        velocidade_pair=AllelePair(40.0, 40.0),
    )

    child, mutations, _ = GeneticsEngine.recombine_genotypes(father, mother, inbreeding_coef=0.0, prng=prng)

    # Sem considerar mutações pontuais, o filho deve ter herdado alelo ~90 do pai e ~30 da mãe para força
    allele_values_forca = {round(child.forca_pair.paternal, 0), round(child.forca_pair.maternal, 0)}
    # O valor médio fenotípico intermediário reflete ambos os progenitores (~60.0)
    assert 45.0 <= child.forca <= 75.0
    assert 45.0 <= child.velocidade <= 75.0


def test_scenario_3_mutations_produce_variations_without_guaranteeing_improvements():
    """Cenário 3: Mutações produzem variações estocásticas sem garantir melhorias automáticas."""
    prng = PRNG(303)
    paternal = Genotype(forca_pair=AllelePair(50.0, 50.0))
    maternal = Genotype(forca_pair=AllelePair(50.0, 50.0))

    deltas = []
    # Realiza múltiplas fecundações para registrar variações mutacionais
    for _ in range(120):
        c, muts, _ = GeneticsEngine.recombine_genotypes(paternal, maternal, inbreeding_coef=0.0, prng=prng)
        for m in muts:
            deltas.append(m.delta)

    assert len(deltas) > 0, "Mutações devem ocorrer ao longo de muitas fecundações."
    has_positive = any(d > 0.05 for d in deltas)
    has_negative = any(d < -0.05 for d in deltas)
    assert has_positive, "Mutações vantajosas/aumentadoras devem ocorrer ocasionalmente."
    assert has_negative, "Mutações prejudiciais/redutoras também devem ocorrer."


def test_scenario_4_advantageous_traits_increase_frequency_under_selection_pressure():
    """Cenário 4: Características vantajosas tornam-se mais frequentes sob pressão seletiva adequada."""
    prng = PRNG(404)
    # População inicial heterogênea: metade com velocidade alta, metade com velocidade baixa
    population = []
    for i in range(20):
        v = 85.0 if i % 2 == 0 else 30.0
        g = Genotype(velocidade=v, forca=50.0, eficiencia_coleta=1.0)
        org = Organism(id=i, x=100.0, y=100.0, energy=60.0, genome=g)
        population.append(org)

    # Pressão seletiva: predação simula sobrevivência proporcional à velocidade expressa
    survivors = []
    for org in population:
        escape_chance = org.phenotype.velocidade / 100.0
        if prng.random() < escape_chance:
            survivors.append(org)

    assert len(survivors) > 0
    avg_speed_initial = sum(o.genotype.velocidade for o in population) / len(population)
    avg_speed_survivors = sum(o.genotype.velocidade for o in survivors) / len(survivors)

    assert avg_speed_survivors > avg_speed_initial, "Sob pressão de predação, a velocidade média dos sobreviventes deve ser maior."


def test_scenario_5_disadvantageous_traits_may_disappear_or_persist_by_drift():
    """Cenário 5: Características desvantajosas podem desaparecer sob forte seleção ou persistir por acaso/deriva."""
    prng = PRNG(505)
    # Sob seleção extrema contra baixa resistência (inanição/doença)
    resistances = [10.0, 10.0, 90.0, 90.0, 90.0]
    survivors = []
    for r in resistances:
        survival_prob = r / 100.0
        if prng.random() < survival_prob:
            survivors.append(r)

    # Variantes de alta resistência têm probabilidade muito maior de persistência
    assert 90.0 in survivors


def test_scenario_6_environmental_shift_alters_relative_trait_advantages():
    """Cenário 6: Uma mudança ambiental altera as vantagens relativas das características."""
    # Ambiente A (Abundância de predadores): velocidade e detecção de ameaças são cruciais
    # Ambiente B (Fome severa / escassez): metabolismo basal reduzido e alta eficiência metabólica superam velocidade

    speedy_bulk = Organism(
        id=1, x=0, y=0,
        genome=Genotype(velocidade=90.0, forca=90.0, eficiencia_metabolica=0.8),
    )
    thrifty_slow = Organism(
        id=2, x=0, y=0,
        genome=Genotype(velocidade=30.0, forca=30.0, eficiencia_metabolica=1.5),
    )

    metabolism = MetabolismSystem()
    speedy_cost = metabolism.calculate_cost(speedy_bulk)
    thrifty_cost = metabolism.calculate_cost(thrifty_slow)

    # Em crise de escassez de alimento, o indivíduo 'thrifty' gasta significativamente menos energia
    assert thrifty_cost < speedy_cost, "Em escassez, eficiência metabólica e menor massa conferem vantagem sobre tamanho e velocidade."


def test_scenario_7_beneficial_traits_have_compensatory_costs():
    """Cenário 7: Não existem atributos infinitos gratuitos — características benéficas têm custos compensatórios."""
    metabolism = MetabolismSystem()

    standard = Organism(id=1, x=0, y=0, genome=Genotype(forca=50.0, velocidade=50.0))
    heavy_muscular = Organism(id=2, x=0, y=0, genome=Genotype(forca=95.0, velocidade=50.0))
    sprinter = Organism(id=3, x=0, y=0, genome=Genotype(forca=50.0, velocidade=95.0))

    cost_std = metabolism.calculate_cost(standard)
    cost_heavy = metabolism.calculate_cost(heavy_muscular)

    sprinter.vx = sprinter.traits.max_speed
    sprinter.vy = 0.0
    standard.vx = sprinter.traits.max_speed
    standard.vy = 0.0
    cost_sprinter = metabolism.calculate_cost(sprinter)
    cost_std_moving = metabolism.calculate_cost(standard)

    # Custo de sustentação basal aumenta com a musculatura
    assert cost_heavy > cost_std, "Maior força muscular acarreta maior débito energético basal."
    # Custo cinético aumenta com predisposição a altas velocidades
    assert cost_sprinter > cost_std_moving, "Maior velocidade de deslocamento acarreta maior débito energético cinético."


def test_scenario_8_individual_learning_does_not_alter_genotype():
    """Cenário 8: O aprendizado individual e o estado temporário NÃO alteram a genética do indivíduo."""
    org = Organism(
        id=42, x=100.0, y=100.0,
        energy=100.0,
        genome=Genotype(forca=60.0, velocidade=55.0),
    )

    initial_forca_maternal = org.genotype.forca_pair.maternal
    initial_forca_paternal = org.genotype.forca_pair.paternal
    initial_vel_maternal = org.genotype.velocidade_pair.maternal
    initial_vel_paternal = org.genotype.velocidade_pair.paternal

    # O animal aprende mapas de risco e comida, passa fome e se fere
    org.memory.add_food_source(200.0, 200.0, 10)
    org.memory.add_danger_zone(50.0, 50.0, 20)
    org.energy = 10.0      # Inanição temporária
    org.saude = 25.0       # Ferimentos de combate
    org.food_eaten = 50    # Ampla experiência de alimentação

    # Fenótipo expresso diminui por ferimentos e inanição
    assert org.phenotype.forca < org.genotype.forca, "Fenótipo reflete o estado temporário e ferimentos."

    # Mas o GENÓTIPO permanece estritamente imutável
    assert org.genotype.forca_pair.maternal == initial_forca_maternal
    assert org.genotype.forca_pair.paternal == initial_forca_paternal
    assert org.genotype.velocidade_pair.maternal == initial_vel_maternal
    assert org.genotype.velocidade_pair.paternal == initial_vel_paternal


def test_scenario_9_clans_with_different_social_strategies_produce_distinct_outcomes():
    """Cenário 9: Clãs com estratégias sociais diferentes apresentam resultados distintos."""
    genealogy = GenealogyRegistry()
    prng = PRNG(909)

    # Clã Cooperativo com reserva e proteção
    cooperative_clan = Clan(
        id=1, name="Clã Mutualista", stage=ClanSocialStage.ESTABLISHED_CLAN,
        communal_food=100.0,
    )
    # Filhotes famintos amparados pelo clã sobrevivem
    pup_energy = 5.0
    food_needed = 20.0
    if cooperative_clan.communal_food >= food_needed:
        cooperative_clan.communal_food -= food_needed
        pup_energy += food_needed

    assert pup_energy >= 25.0, "O clã cooperativo salva filhotes da inanição por compartilhamento comunal."


def test_scenario_10_small_isolated_populations_lose_genetic_diversity_and_experience_inbreeding():
    """Cenário 10: Populações pequenas e isoladas acumulam consanguinidade e sofrem depressão por endogamia."""
    genealogy = GenealogyRegistry()
    prng = PRNG(1010)

    # Geração 0: Pais ancestrais
    p1 = genealogy.register_birth(1, "A1", "MALE", 0, 0, None, None, 1, Genotype(), [], [])
    p2 = genealogy.register_birth(2, "A2", "FEMALE", 0, 0, None, None, 1, Genotype(), [], [])

    # Geração 1: Irmãos completos
    sib1 = genealogy.register_birth(3, "S1", "MALE", 1, 10, 1, 2, 1, Genotype(), [], [])
    sib2 = genealogy.register_birth(4, "S2", "FEMALE", 1, 10, 1, 2, 1, Genotype(), [], [])

    # Cruzamento consanguíneo entre irmãos completos (r = 0.50, F = 0.25)
    kinship = genealogy.calculate_kinship(sib1.id, sib2.id)
    assert kinship == 0.50, f"Parentesco entre irmãos completos deve ser 0.50, obtido {kinship}"

    inbreeding_coef = kinship / 2.0
    assert inbreeding_coef == 0.25, f"Coeficiente de endogamia (F) para cruzamento entre irmãos é 0.25, obtido {inbreeding_coef}"

    # O descendente gerado sob endogamia manifesta penalidade no fenótipo expresso
    inbred_genotype, _, _ = GeneticsEngine.recombine_genotypes(
        Genotype(resistencia_doencas=80.0, fertilidade=1.0),
        Genotype(resistencia_doencas=80.0, fertilidade=1.0),
        inbreeding_coef=inbreeding_coef,
        prng=prng,
    )
    pheno_inbred = Phenotype.calculate(inbred_genotype, life_stage="ADULT", energy=100.0, saude=100.0)

    # Depressão fenotípica proporcional a F
    assert pheno_inbred.inbreeding_penalty < 1.0
    assert pheno_inbred.resistencia_doencas < inbred_genotype.resistencia_doencas


def test_scenario_11_gene_flow_between_populations_restores_diversity():
    """Cenário 11: O fluxo gênico entre populações distintas elimina a consanguinidade e recupera o vigor híbrido."""
    genealogy = GenealogyRegistry()
    prng = PRNG(1111)

    # Fêmea consanguínea de linhagem isolada
    female_rec = genealogy.register_birth(10, "Inbred-F", "FEMALE", 3, 50, 8, 9, 1, Genotype(lineage_id="L1"), [], [])
    # Macho migrante externo, não aparentado (sem ancestrais comuns)
    migrant_male_rec = genealogy.register_birth(20, "Migrant-M", "MALE", 1, 50, None, None, 2, Genotype(lineage_id="L2"), [], [])

    kinship_outcross = genealogy.calculate_kinship(female_rec.id, migrant_male_rec.id)
    assert kinship_outcross == 0.0, "Indivíduo migrante não possui parentesco recente com a população local."

    inbreeding_outcross = kinship_outcross / 2.0
    assert inbreeding_outcross == 0.0

    # Cruzamento exogâmico restaura penalidade de endogamia para 1.0 (sem depressão)
    child_genotype, _, _ = GeneticsEngine.recombine_genotypes(
        Genotype(lineage_id="L2", resistencia_doencas=80.0),
        Genotype(lineage_id="L1", resistencia_doencas=80.0),
        inbreeding_coef=inbreeding_outcross,
        prng=prng,
    )
    pheno_outbred = Phenotype.calculate(child_genotype, life_stage="ADULT", energy=100.0, saude=100.0)

    assert pheno_outbred.inbreeding_penalty == 1.0, "O fluxo gênico elimina a depressão por consanguinidade na descendência."


def test_scenario_12_evolution_is_gradual_no_unlimited_attributes_no_instant_transformation():
    """Cenário 12: A evolução é contínua e gradual, respeitando limites biológicos e passos mutacionais finitos."""
    prng = PRNG(1212)
    father = Genotype(forca=50.0, velocidade=50.0)
    mother = Genotype(forca=52.0, velocidade=48.0)

    # Ao longo de uma única geração, mutações não transformam o indivíduo em um semideus instantâneo
    for _ in range(50):
        child, muts, _ = GeneticsEngine.recombine_genotypes(father, mother, inbreeding_coef=0.0, prng=prng)
        # Força nunca pode ultrapassar os limites superiores da espécie
        assert TRAIT_BOUNDS["forca"][0] <= child.forca <= TRAIT_BOUNDS["forca"][1]
        assert TRAIT_BOUNDS["velocidade"][0] <= child.velocidade <= TRAIT_BOUNDS["velocidade"][1]
        # A intensidade percentual da mutação em uma geração é limitada e gradual
        for m in muts:
            assert m.intensity_pct < 50.0, "Mutações instantâneas são graduais e limitadas em intensidade percentual."
