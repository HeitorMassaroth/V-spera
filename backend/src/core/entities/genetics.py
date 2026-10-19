"""Módulo de genética biológica, genótipo bialélico, expressão fenotípica, hereditariedade e mutações."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from ..prng import PRNG


NAME_PREFIXES = [
    "Ares", "Vesper", "Atlas", "Lyra", "Titan", "Gaia", "Zenith", "Nova",
    "Helios", "Selene", "Orion", "Chronos", "Kratos", "Nyx", "Eos", "Aura",
    "Zephyr", "Rhea", "Drakon", "Iris", "Castor", "Pollux", "Phoenix", "Sol"
]


@dataclass
class MutationRecord:
    """Registro imutável de uma mutação genética individual sofrida no nascimento."""

    attribute: str
    category: str        # 'PEQUENA', 'SIGNIFICATIVA', 'EXCEPCIONAL'
    direction: str       # 'POSITIVA', 'NEGATIVA', 'NEUTRA'
    expected_value: float
    resulting_value: float
    delta: float
    intensity_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "category": self.category,
            "direction": self.direction,
            "expected_value": round(self.expected_value, 2),
            "resulting_value": round(self.resulting_value, 2),
            "delta": round(self.delta, 2),
            "intensity_pct": round(self.intensity_pct, 1),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MutationRecord:
        return cls(
            attribute=data["attribute"],
            category=data["category"],
            direction=data["direction"],
            expected_value=float(data["expected_value"]),
            resulting_value=float(data["resulting_value"]),
            delta=float(data["delta"]),
            intensity_pct=float(data["intensity_pct"]),
        )


@dataclass
class AllelePair:
    """Par de alelos hereditários (materno e paterno) em um determinado loco gênico."""

    maternal: float
    paternal: float

    @property
    def value(self) -> float:
        """Valor genotípico base (codominância aditiva simples)."""
        return (self.maternal + self.paternal) / 2.0

    @property
    def heterozygosity(self) -> float:
        """Grau de heterozigose do loco (diferença normalizada entre os dois alelos)."""
        mean_val = max(0.001, abs(self.value))
        return min(1.0, abs(self.maternal - self.paternal) / mean_val)

    def segregate(self, prng: PRNG) -> float:
        """Segregação independente mendeliana: transmite 1 dos 2 alelos ao gameta."""
        return self.maternal if prng.random() < 0.50 else self.paternal

    def to_dict(self) -> Dict[str, float]:
        return {
            "maternal": round(self.maternal, 2),
            "paternal": round(self.paternal, 2),
            "value": round(self.value, 2),
        }

    @classmethod
    def from_dict(cls, data: Any) -> AllelePair:
        if isinstance(data, (int, float)):
            val = float(data)
            return cls(maternal=val, paternal=val)
        if isinstance(data, dict):
            m = float(data.get("maternal", data.get("value", 50.0)))
            p = float(data.get("paternal", data.get("value", 50.0)))
            return cls(maternal=m, paternal=p)
        return cls(maternal=50.0, paternal=50.0)


# Limites biológicos dos 14 traços fundamentais
TRAIT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "forca": (1.0, 120.0),
    "velocidade": (1.0, 120.0),
    "resistencia": (1.0, 120.0),
    "eficiencia_metabolica": (0.40, 2.00),
    "eficiencia_coleta": (0.50, 2.00),
    "deteccao_ameacas": (1.0, 120.0),
    "resistencia_doencas": (1.0, 120.0),
    "fertilidade": (0.40, 2.00),
    "longevidade_potencial": (1000.0, 3200.0),
    "adaptabilidade": (1.0, 120.0),
    "sociabilidade": (0.05, 0.95),
    "agressividade": (0.05, 0.95),
    "cautela": (0.05, 0.95),
    "instinto_protecao": (0.05, 0.95),
}


@dataclass
class Genotype:
    """Genótipo completo bialélico de um habitante contendo 14 características hereditárias."""

    forca_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    velocidade_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    resistencia_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    eficiencia_metabolica_pair: AllelePair = field(default_factory=lambda: AllelePair(1.0, 1.0))
    eficiencia_coleta_pair: AllelePair = field(default_factory=lambda: AllelePair(1.0, 1.0))
    deteccao_ameacas_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    resistencia_doencas_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    fertilidade_pair: AllelePair = field(default_factory=lambda: AllelePair(1.0, 1.0))
    longevidade_potencial_pair: AllelePair = field(default_factory=lambda: AllelePair(1800.0, 1800.0))
    adaptabilidade_pair: AllelePair = field(default_factory=lambda: AllelePair(50.0, 50.0))
    sociabilidade_pair: AllelePair = field(default_factory=lambda: AllelePair(0.50, 0.50))
    agressividade_pair: AllelePair = field(default_factory=lambda: AllelePair(0.50, 0.50))
    cautela_pair: AllelePair = field(default_factory=lambda: AllelePair(0.50, 0.50))
    instinto_protecao_pair: AllelePair = field(default_factory=lambda: AllelePair(0.50, 0.50))

    # Metadados populacionais e consanguinidade
    inbreeding_coefficient: float = 0.0
    lineage_id: int = 1
    lineage_name: str = "Pioneira"

    # Propriedades de conveniência e compatibilidade direta
    @property
    def forca(self) -> float:
        return self.forca_pair.value

    @property
    def velocidade(self) -> float:
        return self.velocidade_pair.value

    @property
    def resistencia(self) -> float:
        return self.resistencia_pair.value

    @property
    def inteligencia(self) -> float:
        return self.deteccao_ameacas_pair.value

    @property
    def deteccao_ameacas(self) -> float:
        return self.deteccao_ameacas_pair.value

    @property
    def max_saude(self) -> float:
        """Saúde física potencial intrínseca derivada da resistência genética."""
        return 70.0 + (self.resistencia / 100.0) * 60.0

    @property
    def eficiencia_metabolica(self) -> float:
        return self.eficiencia_metabolica_pair.value

    @property
    def eficiencia_coleta(self) -> float:
        return self.eficiencia_coleta_pair.value

    @property
    def resistencia_doencas(self) -> float:
        return self.resistencia_doencas_pair.value

    @property
    def fertilidade(self) -> float:
        return self.fertilidade_pair.value

    @property
    def longevidade_potencial(self) -> float:
        return self.longevidade_potencial_pair.value

    @property
    def adaptabilidade(self) -> float:
        return self.adaptabilidade_pair.value

    @property
    def sociabilidade(self) -> float:
        return self.sociabilidade_pair.value

    @property
    def agressividade(self) -> float:
        return self.agressividade_pair.value

    @property
    def cautela(self) -> float:
        return self.cautela_pair.value

    @property
    def instinto_protecao(self) -> float:
        return self.instinto_protecao_pair.value

    @property
    def average_heterozygosity(self) -> float:
        """Média de heterozigose de todos os locos do indivíduo (0.0 a 1.0)."""
        pairs = self.get_pairs()
        return sum(p.heterozygosity for p in pairs.values()) / len(pairs)

    def get_pairs(self) -> Dict[str, AllelePair]:
        return {
            "forca": self.forca_pair,
            "velocidade": self.velocidade_pair,
            "resistencia": self.resistencia_pair,
            "eficiencia_metabolica": self.eficiencia_metabolica_pair,
            "eficiencia_coleta": self.eficiencia_coleta_pair,
            "deteccao_ameacas": self.deteccao_ameacas_pair,
            "resistencia_doencas": self.resistencia_doencas_pair,
            "fertilidade": self.fertilidade_pair,
            "longevidade_potencial": self.longevidade_potencial_pair,
            "adaptabilidade": self.adaptabilidade_pair,
            "sociabilidade": self.sociabilidade_pair,
            "agressividade": self.agressividade_pair,
            "cautela": self.cautela_pair,
            "instinto_protecao": self.instinto_protecao_pair,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialização simplificada compatível com AnimalGenome legado."""
        return {
            "forca": round(self.forca, 2),
            "velocidade": round(self.velocidade, 2),
            "resistencia": round(self.resistencia, 2),
            "inteligencia": round(self.inteligencia, 2),
            "max_saude": round(self.max_saude, 2),
            "eficiencia_metabolica": round(self.eficiencia_metabolica, 2),
            "eficiencia_coleta": round(self.eficiencia_coleta, 2),
            "resistencia_doencas": round(self.resistencia_doencas, 2),
            "fertilidade": round(self.fertilidade, 2),
            "longevidade_potencial": round(self.longevidade_potencial, 1),
            "adaptabilidade": round(self.adaptabilidade, 2),
            "sociabilidade": round(self.sociabilidade, 2),
            "agressividade": round(self.agressividade, 2),
            "cautela": round(self.cautela, 2),
            "instinto_protecao": round(self.instinto_protecao, 2),
            "inbreeding_coefficient": round(self.inbreeding_coefficient, 3),
            "heterozygosity": round(self.average_heterozygosity, 3),
            "lineage_id": self.lineage_id,
            "lineage_name": self.lineage_name,
        }

    def to_detailed_dict(self) -> Dict[str, Any]:
        """Serialização detalhada com pares de alelos para o inspetor de genética."""
        base = self.to_dict()
        base["alleles"] = {k: v.to_dict() for k, v in self.get_pairs().items()}
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Genotype:
        """Desserialização resiliente suportando formato legado ou bialélico."""
        alleles_data = data.get("alleles", {})

        def get_pair(key: str, default_val: float) -> AllelePair:
            if key in alleles_data:
                return AllelePair.from_dict(alleles_data[key])
            if key in data:
                val = float(data[key])
                return AllelePair(val, val)
            return AllelePair(default_val, default_val)

        return cls(
            forca_pair=get_pair("forca", 50.0),
            velocidade_pair=get_pair("velocidade", 50.0),
            resistencia_pair=get_pair("resistencia", 50.0),
            eficiencia_metabolica_pair=get_pair("eficiencia_metabolica", 1.0),
            eficiencia_coleta_pair=get_pair("eficiencia_coleta", 1.0),
            deteccao_ameacas_pair=get_pair("deteccao_ameacas", data.get("inteligencia", 50.0)),
            resistencia_doencas_pair=get_pair("resistencia_doencas", 50.0),
            fertilidade_pair=get_pair("fertilidade", 1.0),
            longevidade_potencial_pair=get_pair("longevidade_potencial", 1800.0),
            adaptabilidade_pair=get_pair("adaptabilidade", 50.0),
            sociabilidade_pair=get_pair("sociabilidade", 0.50),
            agressividade_pair=get_pair("agressividade", 0.50),
            cautela_pair=get_pair("cautela", 0.50),
            instinto_protecao_pair=get_pair("instinto_protecao", 0.50),
            inbreeding_coefficient=float(data.get("inbreeding_coefficient", 0.0)),
            lineage_id=int(data.get("lineage_id", 1)),
            lineage_name=str(data.get("lineage_name", "Pioneira")),
        )


# Alias para retrocompatibilidade
AnimalGenome = Genotype


@dataclass
class AnimalPersonality:
    """Perfil comportamental complementar para compatibilidade com sistemas legados."""

    agressividade: float = 0.50
    sociabilidade: float = 0.50
    cautela: float = 0.50
    curiosidade: float = 0.50
    instinto_protecao: float = 0.50
    eficiencia_coleta: float = 1.00
    exploracao: float = 1.00
    fertilidade: float = 1.00

    def to_dict(self) -> Dict[str, float]:
        return {
            "agressividade": round(self.agressividade, 2),
            "sociabilidade": round(self.sociabilidade, 2),
            "cautela": round(self.cautela, 2),
            "curiosidade": round(self.curiosidade, 2),
            "instinto_protecao": round(self.instinto_protecao, 2),
            "eficiencia_coleta": round(self.eficiencia_coleta, 2),
            "exploracao": round(self.exploracao, 2),
            "fertilidade": round(self.fertilidade, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnimalPersonality:
        return cls(
            agressividade=float(data.get("agressividade", 0.50)),
            sociabilidade=float(data.get("sociabilidade", 0.50)),
            cautela=float(data.get("cautela", 0.50)),
            curiosidade=float(data.get("curiosidade", 0.50)),
            instinto_protecao=float(data.get("instinto_protecao", 0.50)),
            eficiencia_coleta=float(data.get("eficiencia_coleta", 1.00)),
            exploracao=float(data.get("exploracao", 1.00)),
            fertilidade=float(data.get("fertilidade", 1.00)),
        )


@dataclass
class Phenotype:
    """Fenótipo expresso do habitante: modulação ontogenética, fisiológica e ambiental."""

    forca: float
    velocidade: float
    resistencia: float
    eficiencia_metabolica: float
    eficiencia_coleta: float
    deteccao_ameacas: float
    resistencia_doencas: float
    fertilidade: float
    longevidade_potencial: float
    adaptabilidade: float
    sociabilidade: float
    agressividade: float
    cautela: float
    instinto_protecao: float
    max_saude: float

    # Fatores moduladores aplicados
    ontogeny_factor: float
    health_factor: float
    inbreeding_penalty: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forca": round(self.forca, 2),
            "velocidade": round(self.velocidade, 2),
            "resistencia": round(self.resistencia, 2),
            "eficiencia_metabolica": round(self.eficiencia_metabolica, 2),
            "eficiencia_coleta": round(self.eficiencia_coleta, 2),
            "deteccao_ameacas": round(self.deteccao_ameacas, 2),
            "resistencia_doencas": round(self.resistencia_doencas, 2),
            "fertilidade": round(self.fertilidade, 2),
            "longevidade_potencial": round(self.longevidade_potencial, 1),
            "adaptabilidade": round(self.adaptabilidade, 2),
            "sociabilidade": round(self.sociabilidade, 2),
            "agressividade": round(self.agressividade, 2),
            "cautela": round(self.cautela, 2),
            "instinto_protecao": round(self.instinto_protecao, 2),
            "max_saude": round(self.max_saude, 2),
            "ontogeny_factor": round(self.ontogeny_factor, 2),
            "health_factor": round(self.health_factor, 2),
            "inbreeding_penalty": round(self.inbreeding_penalty, 2),
        }

    @classmethod
    def calculate(
        cls,
        genotype: Genotype,
        life_stage: str,
        energy: float,
        saude: float,
        environmental_harshness: float = 0.0,
    ) -> Phenotype:
        """Calcula a expressão fenotípica atual integrando genótipo, estágio, nutrição e endogamia."""
        # 1. Fator Ontogenético (Desenvolvimento por idade)
        if life_stage == "NEWBORN":
            ontogeny = 0.15
        elif life_stage == "DEVELOPING":
            ontogeny = 0.35
        elif life_stage == "JUVENILE":
            ontogeny = 0.65
        elif life_stage == "INDEPENDENT":
            ontogeny = 0.85
        else:  # ADULT
            ontogeny = 1.00

        # 2. Fator de Saúde e Nutrição (Estado Atual)
        # Fraqueza temporária por inanição
        f_energy = 0.70 + 0.30 * min(1.0, max(0.0, energy / 40.0))
        # Fraqueza temporária por ferimentos graves
        f_saude = 0.75 + 0.25 * min(1.0, max(0.0, saude / 50.0))
        health_factor = f_energy * f_saude

        # 3. Penalidade por Endogamia (Depressão Consanguínea)
        f_inb = genotype.inbreeding_coefficient
        inbreeding_penalty = max(0.40, 1.0 - 0.45 * f_inb)

        # 4. Compensações Biológicas (Trade-offs)
        # Músculos pesados geram leve inércia sobre a velocidade ágil máxima
        weight_inertia = max(0.85, 1.05 - (genotype.forca / 250.0))

        # Expressão dos traços
        expr_forca = genotype.forca * ontogeny * health_factor
        expr_vel = genotype.velocidade * ontogeny * health_factor * weight_inertia
        expr_res = genotype.resistencia * (0.50 + 0.50 * ontogeny) * health_factor
        expr_metab = genotype.eficiencia_metabolica * (1.0 - 0.15 * environmental_harshness)
        expr_coleta = genotype.eficiencia_coleta * (0.60 + 0.40 * ontogeny)
        expr_visao = genotype.deteccao_ameacas * (0.40 + 0.60 * ontogeny) * health_factor

        # Traços vulneráveis à depressão por endogamia
        expr_imunidade = genotype.resistencia_doencas * inbreeding_penalty
        expr_fertilidade = genotype.fertilidade * inbreeding_penalty
        expr_max_saude = genotype.max_saude * inbreeding_penalty * (0.50 + 0.50 * ontogeny)

        return cls(
            forca=round(max(0.5, expr_forca), 2),
            velocidade=round(max(0.5, expr_vel), 2),
            resistencia=round(max(0.5, expr_res), 2),
            eficiencia_metabolica=round(max(0.2, expr_metab), 2),
            eficiencia_coleta=round(max(0.2, expr_coleta), 2),
            deteccao_ameacas=round(max(5.0, expr_visao), 2),
            resistencia_doencas=round(max(0.5, expr_imunidade), 2),
            fertilidade=round(max(0.1, expr_fertilidade), 2),
            longevidade_potencial=round(genotype.longevidade_potencial, 1),
            adaptabilidade=round(genotype.adaptabilidade, 2),
            sociabilidade=round(genotype.sociabilidade, 2),
            agressividade=round(genotype.agressividade, 2),
            cautela=round(genotype.cautela, 2),
            instinto_protecao=round(genotype.instinto_protecao, 2),
            max_saude=round(max(10.0, expr_max_saude), 2),
            ontogeny_factor=round(ontogeny, 2),
            health_factor=round(health_factor, 2),
            inbreeding_penalty=round(inbreeding_penalty, 2),
        )


class GeneticsEngine:
    """Motor evolutivo de herança alélica mendeliana, recombinação e mutações estocásticas."""

    # Taxas estocásticas de mutação alélica
    P_MUTATION_PER_LOCUS = 0.090   # 9% de chance por loco gênico
    P_EXCEPTIONAL = 0.06           # 6% das mutações são excepcionais
    P_SIGNIFICANT = 0.28           # 28% das mutações são significativas
    P_SMALL = 0.66                 # 66% das mutações são pequenas

    @classmethod
    def generate_random_genotype(
        cls,
        prng: PRNG,
        lineage_id: int = 1,
        lineage_name: Optional[str] = None,
    ) -> Genotype:
        """Gera genótipo inicial equilibrado para organismos pioneiros (Geração 0)."""
        if not lineage_name:
            lineage_name = f"Linhagem {NAME_PREFIXES[lineage_id % len(NAME_PREFIXES)]}"

        def pair(low: float, high: float) -> AllelePair:
            m = round(prng.uniform(low, high), 2)
            p = round(prng.uniform(low, high), 2)
            return AllelePair(m, p)

        return Genotype(
            forca_pair=pair(35.0, 65.0),
            velocidade_pair=pair(35.0, 65.0),
            resistencia_pair=pair(35.0, 65.0),
            eficiencia_metabolica_pair=pair(0.80, 1.25),
            eficiencia_coleta_pair=pair(0.80, 1.25),
            deteccao_ameacas_pair=pair(35.0, 65.0),
            resistencia_doencas_pair=pair(35.0, 65.0),
            fertilidade_pair=pair(0.80, 1.25),
            longevidade_potencial_pair=pair(1500.0, 2200.0),
            adaptabilidade_pair=pair(35.0, 65.0),
            sociabilidade_pair=pair(0.20, 0.80),
            agressividade_pair=pair(0.20, 0.80),
            cautela_pair=pair(0.20, 0.80),
            instinto_protecao_pair=pair(0.25, 0.85),
            inbreeding_coefficient=0.0,
            lineage_id=lineage_id,
            lineage_name=lineage_name,
        )

    @classmethod
    def generate_random_genome(cls, prng: PRNG) -> Genotype:
        """Compatibilidade retroativa com a API legada."""
        return cls.generate_random_genotype(prng)

    @classmethod
    def generate_random_personality(cls, prng: PRNG) -> AnimalPersonality:
        """Compatibilidade retroativa com a API legada."""
        return AnimalPersonality(
            agressividade=round(prng.uniform(0.20, 0.80), 2),
            sociabilidade=round(prng.uniform(0.20, 0.80), 2),
            cautela=round(prng.uniform(0.20, 0.80), 2),
            curiosidade=round(prng.uniform(0.20, 0.80), 2),
            instinto_protecao=round(prng.uniform(0.25, 0.85), 2),
            eficiencia_coleta=round(prng.uniform(0.80, 1.25), 2),
            exploracao=round(prng.uniform(0.80, 1.25), 2),
            fertilidade=round(prng.uniform(0.80, 1.25), 2),
        )

    @classmethod
    def recombine_personality(
        cls,
        father_p: AnimalPersonality,
        mother_p: AnimalPersonality,
        prng: PRNG,
    ) -> Tuple[AnimalPersonality, List[MutationRecord]]:
        """Compatibilidade retroativa."""
        f_dict = father_p.to_dict()
        m_dict = mother_p.to_dict()
        res_dict: Dict[str, float] = {}
        for t in f_dict:
            res_dict[t] = round((f_dict[t] + m_dict[t]) / 2.0, 2)
        return AnimalPersonality.from_dict(res_dict), []

    @classmethod
    def generate_name(cls, prefix_idx: int, generation: int, entity_id: int) -> str:
        """Gera nome individual sistemático (ex: Lyra-G2#18)."""
        prefix = NAME_PREFIXES[prefix_idx % len(NAME_PREFIXES)]
        return f"{prefix}-G{generation}#{entity_id}"

    @classmethod
    def recombine_genotypes(
        cls,
        father: Genotype,
        mother: Genotype,
        inbreeding_coef: float,
        population_averages: Dict[str, float],
        prng: PRNG,
    ) -> Tuple[Genotype, List[MutationRecord], List[Dict[str, Any]]]:
        """
        Executa segregação mendeliana de 2 alelos por traço, recombinação,
        avaliação estocástica de mutações e efeitos de endogamia.
        """
        f_pairs = father.get_pairs()
        m_pairs = mother.get_pairs()

        child_pairs: Dict[str, AllelePair] = {}
        mutations: List[MutationRecord] = []
        genetic_history: List[Dict[str, Any]] = []

        # Determinação da linhagem (transmissão de linhagem com fluxo gênico)
        if father.lineage_id == mother.lineage_id:
            child_lineage_id = father.lineage_id
            child_lineage_name = father.lineage_name
        else:
            # Linhagens distintas: herda com 50% de probabilidade de qualquer progenitor
            if prng.random() < 0.50:
                child_lineage_id = father.lineage_id
                child_lineage_name = father.lineage_name
            else:
                child_lineage_id = mother.lineage_id
                child_lineage_name = mother.lineage_name

        for trait, (low_bound, high_bound) in TRAIT_BOUNDS.items():
            # 1. Segregação Mendeliana Independente: 1 alelo do pai, 1 alelo da mãe
            alelo_paterno = f_pairs[trait].segregate(prng)
            alelo_materno = m_pairs[trait].segregate(prng)

            expected_mean = (alelo_paterno + alelo_materno) / 2.0

            # 2. Avaliação de Mutações Estocásticas
            mut_record: Optional[MutationRecord] = None
            if prng.random() < cls.P_MUTATION_PER_LOCUS:
                roll_cat = prng.random()
                if roll_cat < cls.P_EXCEPTIONAL:
                    category = "EXCEPCIONAL"
                    intensity = prng.uniform(0.25, 0.45)
                elif roll_cat < (cls.P_EXCEPTIONAL + cls.P_SIGNIFICANT):
                    category = "SIGNIFICATIVA"
                    intensity = prng.uniform(0.10, 0.22)
                else:
                    category = "PEQUENA"
                    intensity = prng.uniform(0.02, 0.08)

                # Mutação pode ser positiva, negativa ou neutra
                roll_dir = prng.random()
                if roll_dir < 0.45:
                    direction = "POSITIVA"
                    delta = expected_mean * intensity
                elif roll_dir < 0.90:
                    direction = "NEGATIVA"
                    delta = -expected_mean * intensity
                else:
                    direction = "NEUTRA"
                    delta = 0.0

                # Endogamia (Inbreeding): Se houver parentesco, eleva a chance de mutações deletérias
                if inbreeding_coef > 0.05 and trait in ["resistencia_doencas", "fertilidade", "resistencia"]:
                    if prng.random() < inbreeding_coef:
                        direction = "NEGATIVA"
                        delta = -expected_mean * prng.uniform(0.12, 0.30)

                # Aplica a mutação em um dos alelos herdados
                if prng.random() < 0.50:
                    alelo_paterno = max(low_bound, min(high_bound, alelo_paterno + delta))
                else:
                    alelo_materno = max(low_bound, min(high_bound, alelo_materno + delta))

                final_mean = (alelo_paterno + alelo_materno) / 2.0
                mut_record = MutationRecord(
                    attribute=trait,
                    category=category,
                    direction=direction,
                    expected_value=expected_mean,
                    resulting_value=final_mean,
                    delta=final_mean - expected_mean,
                    intensity_pct=intensity * 100.0,
                )
                mutations.append(mut_record)

            # Clamp estrito aos limites biológicos
            alelo_paterno = max(low_bound, min(high_bound, alelo_paterno))
            alelo_materno = max(low_bound, min(high_bound, alelo_materno))

            child_pairs[trait] = AllelePair(maternal=alelo_materno, paternal=alelo_paterno)

            genetic_history.append({
                "attribute": trait,
                "father_val": round(f_pairs[trait].value, 2),
                "mother_val": round(m_pairs[trait].value, 2),
                "parents_avg": round(expected_mean, 2),
                "final_val": round(child_pairs[trait].value, 2),
                "deviation_from_parents": round(child_pairs[trait].value - expected_mean, 2),
                "had_mutation": mut_record is not None,
            })

        child_genotype = Genotype(
            forca_pair=child_pairs["forca"],
            velocidade_pair=child_pairs["velocidade"],
            resistencia_pair=child_pairs["resistencia"],
            eficiencia_metabolica_pair=child_pairs["eficiencia_metabolica"],
            eficiencia_coleta_pair=child_pairs["eficiencia_coleta"],
            deteccao_ameacas_pair=child_pairs["deteccao_ameacas"],
            resistencia_doencas_pair=child_pairs["resistencia_doencas"],
            fertilidade_pair=child_pairs["fertilidade"],
            longevidade_potencial_pair=child_pairs["longevidade_potencial"],
            adaptabilidade_pair=child_pairs["adaptabilidade"],
            sociabilidade_pair=child_pairs["sociabilidade"],
            agressividade_pair=child_pairs["agressividade"],
            cautela_pair=child_pairs["cautela"],
            instinto_protecao_pair=child_pairs["instinto_protecao"],
            inbreeding_coefficient=inbreeding_coef,
            lineage_id=child_lineage_id,
            lineage_name=child_lineage_name,
        )

        return child_genotype, mutations, genetic_history

    @classmethod
    def recombine(
        cls,
        father_genome: Any,
        mother_genome: Any,
        population_averages: Dict[str, float],
        prng: PRNG,
    ) -> Tuple[Genotype, List[MutationRecord], List[Dict[str, Any]]]:
        """Wrapper de compatibilidade para código legado."""
        f_gt = father_genome if isinstance(father_genome, Genotype) else Genotype.from_dict(father_genome.to_dict())
        m_gt = mother_genome if isinstance(mother_genome, Genotype) else Genotype.from_dict(mother_genome.to_dict())
        return cls.recombine_genotypes(f_gt, m_gt, 0.0, population_averages, prng)
