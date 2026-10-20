"""Registro imutável e preservação histórica da árvore genealógica de todos os animais."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .genetics import AnimalGenome, AnimalPersonality, MutationRecord


@dataclass
class AnimalRecord:
    """Ficha histórica imutável de um animal para consultas genealógicas perpétuas."""

    id: int
    name: str
    role: str
    generation: int
    birth_tick: int
    death_tick: Optional[int] = None
    cause_of_death: Optional[str] = None
    sex: str = "M"
    life_stage: str = "ADULT"
    father_id: Optional[int] = None
    mother_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)
    partner_id: Optional[int] = None
    partner_bond_duration: int = 0
    family_id: Optional[int] = None
    species: str = "PREDATOR"
    inbreeding_coefficient: float = 0.0
    lineage_id: str = "L0"
    lineage_name: str = "Ancestral"
    genome: Dict[str, float] = field(default_factory=dict)
    personality: Dict[str, float] = field(default_factory=dict)
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    genetic_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "sex": self.sex,
            "life_stage": self.life_stage,
            "species": self.species,
            "generation": self.generation,
            "birth_tick": self.birth_tick,
            "death_tick": self.death_tick,
            "cause_of_death": self.cause_of_death,
            "father_id": self.father_id,
            "mother_id": self.mother_id,
            "children_ids": self.children_ids,
            "partner_id": self.partner_id,
            "partner_bond_duration": self.partner_bond_duration,
            "family_id": self.family_id,
            "inbreeding_coefficient": round(self.inbreeding_coefficient, 3),
            "lineage_id": self.lineage_id,
            "lineage_name": self.lineage_name,
            "genome": self.genome,
            "personality": self.personality,
            "mutations": self.mutations,
            "genetic_history": self.genetic_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnimalRecord:
        return cls(
            id=data["id"],
            name=data["name"],
            role=data["role"],
            sex=data.get("sex", "M"),
            life_stage=data.get("life_stage", "ADULT"),
            species=data.get("species", "PREDATOR"),
            generation=data["generation"],
            birth_tick=data["birth_tick"],
            death_tick=data.get("death_tick"),
            cause_of_death=data.get("cause_of_death"),
            father_id=data.get("father_id"),
            mother_id=data.get("mother_id"),
            children_ids=data.get("children_ids", []),
            partner_id=data.get("partner_id"),
            partner_bond_duration=data.get("partner_bond_duration", 0),
            family_id=data.get("family_id"),
            inbreeding_coefficient=float(data.get("inbreeding_coefficient", 0.0)),
            lineage_id=int(data["lineage_id"]) if (isinstance(data.get("lineage_id"), int) or (isinstance(data.get("lineage_id"), str) and str(data.get("lineage_id")).isdigit())) else str(data.get("lineage_id", "L0")),
            lineage_name=str(data.get("lineage_name", "Ancestral")),
            genome=data.get("genome", {}),
            personality=data.get("personality", {}),
            mutations=data.get("mutations", []),
            genetic_history=data.get("genetic_history", []),
        )


class GenealogyRegistry:
    """Registro histórico de todos os organismos que já existiram na simulação."""

    def __init__(self) -> None:
        self._records: Dict[int, AnimalRecord] = {}

    def register_birth(
        self,
        organism_id: int,
        name: str,
        role: str,
        generation: int,
        birth_tick: int,
        father_id: Optional[int],
        mother_id: Optional[int],
        family_id: Optional[int],
        genome: AnimalGenome,
        mutations: List[MutationRecord],
        genetic_history: List[Dict[str, Any]],
        personality: Optional[AnimalPersonality] = None,
        sex: Optional[str] = None,
        life_stage: Optional[str] = None,
        species: str = "PREDATOR",
        inbreeding_coefficient: float = 0.0,
        lineage_id: str = "L0",
        lineage_name: str = "Ancestral",
    ) -> AnimalRecord:
        """Registra o nascimento de um novo animal e atualiza a descendência dos pais."""
        computed_sex = sex if sex is not None else ("F" if role == "FEMALE" else "M")
        computed_stage = life_stage if life_stage is not None else ("ADULT" if role != "CHILD" else "NEWBORN")
        record = AnimalRecord(
            id=organism_id,
            name=name,
            role=role,
            sex=computed_sex,
            life_stage=computed_stage,
            species=species,
            generation=generation,
            birth_tick=birth_tick,
            death_tick=None,
            cause_of_death=None,
            father_id=father_id,
            mother_id=mother_id,
            children_ids=[],
            family_id=family_id,
            inbreeding_coefficient=inbreeding_coefficient,
            lineage_id=lineage_id,
            lineage_name=lineage_name,
            genome=genome.to_dict(),
            personality=personality.to_dict() if personality else {},
            mutations=[m.to_dict() for m in mutations],
            genetic_history=genetic_history,
        )
        self._records[organism_id] = record

        # Atualiza a lista de filhos do pai
        if father_id is not None and father_id in self._records:
            if organism_id not in self._records[father_id].children_ids:
                self._records[father_id].children_ids.append(organism_id)

        # Atualiza a lista de filhos da mãe
        if mother_id is not None and mother_id in self._records:
            if organism_id not in self._records[mother_id].children_ids:
                self._records[mother_id].children_ids.append(organism_id)

        return record

    def register_death(self, organism_id: int, death_tick: int, cause_of_death: Optional[str] = None) -> None:
        """Registra o falecimento de um organismo sem apagar seus dados genealógicos."""
        if organism_id in self._records:
            self._records[organism_id].death_tick = death_tick
            if cause_of_death:
                self._records[organism_id].cause_of_death = cause_of_death

    def register_pair_bond(self, id1: int, id2: int, tick: int) -> None:
        """Registra vínculo reprodutivo permanente entre dois parceiros."""
        if id1 in self._records:
            self._records[id1].partner_id = id2
        if id2 in self._records:
            self._records[id2].partner_id = id1

    def update_record_stage(self, organism_id: int, stage: str, role: Optional[str] = None) -> None:
        """Atualiza estágio de vida e papel do indivíduo no registro histórico."""
        if organism_id in self._records:
            self._records[organism_id].life_stage = stage
            if role:
                self._records[organism_id].role = role
                self._records[organism_id].sex = "F" if role == "FEMALE" else "M"

    def update_bond_duration(self, organism_id: int, duration: int) -> None:
        """Atualiza duração do vínculo conjugal ativo."""
        if organism_id in self._records:
            self._records[organism_id].partner_bond_duration = duration

    def get_record(self, organism_id: int) -> Optional[AnimalRecord]:
        return self._records.get(organism_id)

    def get_family_tree(self, organism_id: int) -> Dict[str, Any]:
        """Constrói a árvore genealógica completa (pais, parceiro, avós e filhos) do indivíduo."""
        target = self.get_record(organism_id)
        if target is None:
            return {}

        father_rec = self.get_record(target.father_id) if target.father_id is not None else None
        mother_rec = self.get_record(target.mother_id) if target.mother_id is not None else None
        partner_rec = self.get_record(target.partner_id) if target.partner_id is not None else None

        # Avós
        grandparents: Dict[str, Optional[Dict[str, Any]]] = {
            "paternal_grandfather": None,
            "paternal_grandmother": None,
            "maternal_grandfather": None,
            "maternal_grandmother": None,
        }

        if father_rec is not None:
            if father_rec.father_id is not None:
                pgf = self.get_record(father_rec.father_id)
                if pgf:
                    grandparents["paternal_grandfather"] = pgf.to_dict()
            if father_rec.mother_id is not None:
                pgm = self.get_record(father_rec.mother_id)
                if pgm:
                    grandparents["paternal_grandmother"] = pgm.to_dict()

        if mother_rec is not None:
            if mother_rec.father_id is not None:
                mgf = self.get_record(mother_rec.father_id)
                if mgf:
                    grandparents["maternal_grandfather"] = mgf.to_dict()
            if mother_rec.mother_id is not None:
                mgm = self.get_record(mother_rec.mother_id)
                if mgm:
                    grandparents["maternal_grandmother"] = mgm.to_dict()

        children = [
            self._records[cid].to_dict()
            for cid in target.children_ids
            if cid in self._records
        ]

        return {
            "animal": target.to_dict(),
            "partner": partner_rec.to_dict() if partner_rec else None,
            "father": father_rec.to_dict() if father_rec else None,
            "mother": mother_rec.to_dict() if mother_rec else None,
            "grandparents": grandparents,
            "children": children,
        }

    def calculate_kinship(
        self,
        id1: Optional[int],
        id2: Optional[int],
        memo: Optional[Dict[Tuple[int, int], float]] = None,
        depth: int = 0,
    ) -> float:
        """
        Calcula o coeficiente de parentesco/consanguinidade de Wright (r) entre dois indivíduos por recorrência de Malécot.
        Retorna valor entre 0.0 (sem parentesco recente conhecido) e 1.0 (mesmo indivíduo ou clones).
        - Mesma identidade: 1.0
        - Pais e filhos: 0.50
        - Irmãos completos: 0.50
        - Meio-irmãos: 0.25
        - Avós e netos: 0.25
        - Primos de 1º grau: 0.125
        """
        if id1 is None or id2 is None:
            return 0.0
        if id1 == id2:
            return 1.0
        if depth > 6:
            return 0.0

        pair_key = (min(id1, id2), max(id1, id2))
        if memo is not None and pair_key in memo:
            return memo[pair_key]

        if memo is None:
            memo = {}

        rec1 = self.get_record(id1)
        rec2 = self.get_record(id2)
        if not rec1 or not rec2:
            memo[pair_key] = 0.0
            return 0.0

        # Expandir pais do indivíduo com maior geração (mais jovem)
        if rec1.generation > rec2.generation:
            p_f = self.calculate_kinship(rec1.father_id, id2, memo, depth + 1) if rec1.father_id is not None else 0.0
            p_m = self.calculate_kinship(rec1.mother_id, id2, memo, depth + 1) if rec1.mother_id is not None else 0.0
            kinship = 0.5 * (p_f + p_m)
        elif rec2.generation > rec1.generation:
            p_f = self.calculate_kinship(id1, rec2.father_id, memo, depth + 1) if rec2.father_id is not None else 0.0
            p_m = self.calculate_kinship(id1, rec2.mother_id, memo, depth + 1) if rec2.mother_id is not None else 0.0
            kinship = 0.5 * (p_f + p_m)
        else:
            # Mesma geração: expandir pais de rec1
            p_f = self.calculate_kinship(rec1.father_id, id2, memo, depth + 1) if rec1.father_id is not None else 0.0
            p_m = self.calculate_kinship(rec1.mother_id, id2, memo, depth + 1) if rec1.mother_id is not None else 0.0
            kinship = 0.5 * (p_f + p_m)

        memo[pair_key] = kinship
        return min(1.0, max(0.0, kinship))

    def get_evolution_metrics(
        self,
        active_organisms: List[Any],
        clans: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Calcula estatísticas populacionais, diversidade alélica, mortalidade e linhagens ativas."""
        active_count = len(active_organisms)
        if active_count == 0:
            return {
                "active_population_count": 0,
                "total_records": len(self._records),
                "generations": {},
                "genetic_diversity": {
                    "average_heterozygosity": 0.0,
                    "average_inbreeding_coefficient": 0.0,
                    "effective_population_size": 0.0,
                    "unique_lineages": 0,
                },
                "lineages": [],
                "mortality_by_cause": {},
                "trait_survival_correlation": {},
                "clan_differences": [],
            }

        # Contagens por sexo e diversidade genética populacional
        mature_males = 0
        mature_females = 0
        total_hetero = 0.0
        total_inbreeding = 0.0
        lineages_map: Dict[str, Dict[str, Any]] = {}

        for org in active_organisms:
            stage = getattr(org, "life_stage", "ADULT")
            sex = getattr(org, "sex", "M")
            if stage in ["ADULT", "INDEPENDENT"]:
                if sex == "M":
                    mature_males += 1
                else:
                    mature_females += 1

            geno = getattr(org, "genotype", None)
            if geno is not None:
                total_hetero += geno.average_heterozygosity
                total_inbreeding += geno.inbreeding_coefficient
                lid = geno.lineage_id
                lname = geno.lineage_name
                if lid not in lineages_map:
                    lineages_map[lid] = {
                        "id": lid,
                        "name": lname,
                        "count": 0,
                        "generations": [],
                        "heterozygosities": [],
                    }
                lineages_map[lid]["count"] += 1
                lineages_map[lid]["generations"].append(getattr(org, "generation", 0))
                lineages_map[lid]["heterozygosities"].append(geno.average_heterozygosity)

        # Tamanho efetivo da população Ne = 4 * Nm * Nf / (Nm + Nf)
        ne = 0.0
        if (mature_males + mature_females) > 0 and mature_males > 0 and mature_females > 0:
            ne = round((4.0 * mature_males * mature_females) / (mature_males + mature_females), 1)

        # Estatísticas por geração
        gen_groups: Dict[int, List[Any]] = {}
        for rec in self._records.values():
            g = rec.generation
            if g not in gen_groups:
                gen_groups[g] = []
            gen_groups[g].append(rec)

        generations_data: Dict[str, Any] = {}
        for g in sorted(gen_groups.keys()):
            recs = gen_groups[g]
            alive_in_g = sum(1 for r in recs if r.death_tick is None)

            forcas = [r.genome.get("forca", 50.0) for r in recs if r.genome]
            vels = [r.genome.get("velocidade", 50.0) for r in recs if r.genome]
            resists = [r.genome.get("resistencia", 50.0) for r in recs if r.genome]
            coletas = [r.genome.get("eficiencia_coleta", 50.0) for r in recs if r.genome]
            deteccoes = [r.genome.get("deteccao_ameacas", 50.0) for r in recs if r.genome]
            inbreedings = [r.inbreeding_coefficient for r in recs]

            generations_data[str(g)] = {
                "generation": g,
                "total_born": len(recs),
                "alive": alive_in_g,
                "avg_forca": round(sum(forcas) / len(forcas), 1) if forcas else 50.0,
                "avg_velocidade": round(sum(vels) / len(vels), 1) if vels else 50.0,
                "avg_resistencia": round(sum(resists) / len(resists), 1) if resists else 50.0,
                "avg_coleta": round(sum(coletas) / len(coletas), 1) if coletas else 50.0,
                "avg_deteccao": round(sum(deteccoes) / len(deteccoes), 1) if deteccoes else 50.0,
                "avg_inbreeding": round(sum(inbreedings) / len(inbreedings), 3) if inbreedings else 0.0,
            }

        # Linhagens formatadas
        lineages_summary = []
        for lid, linfo in lineages_map.items():
            gens = linfo["generations"]
            hets = linfo["heterozygosities"]
            lineages_summary.append({
                "id": lid,
                "name": linfo["name"],
                "active_members": linfo["count"],
                "avg_generation": round(sum(gens) / len(gens), 1) if gens else 0.0,
                "avg_heterozygosity": round(sum(hets) / len(hets), 3) if hets else 0.0,
            })
        lineages_summary.sort(key=lambda x: x["active_members"], reverse=True)

        # Mortalidade por causa
        mortality_counts: Dict[str, int] = {}
        deceased_forcas: List[float] = []
        deceased_vels: List[float] = []
        for rec in self._records.values():
            if rec.death_tick is not None and rec.cause_of_death:
                mortality_counts[rec.cause_of_death] = mortality_counts.get(rec.cause_of_death, 0) + 1
                if rec.genome:
                    deceased_forcas.append(rec.genome.get("forca", 50.0))
                    deceased_vels.append(rec.genome.get("velocidade", 50.0))

        # Correlação de sobrevivência de traços
        surviving_forcas = [getattr(o.genotype, "forca", 50.0) for o in active_organisms if getattr(o, "life_stage", "") == "ADULT"]
        surviving_vels = [getattr(o.genotype, "velocidade", 50.0) for o in active_organisms if getattr(o, "life_stage", "") == "ADULT"]

        trait_survival_correlation = {
            "surviving_adults_avg_forca": round(sum(surviving_forcas) / len(surviving_forcas), 1) if surviving_forcas else 50.0,
            "deceased_avg_forca": round(sum(deceased_forcas) / len(deceased_forcas), 1) if deceased_forcas else 50.0,
            "surviving_adults_avg_velocidade": round(sum(surviving_vels) / len(surviving_vels), 1) if surviving_vels else 50.0,
            "deceased_avg_velocidade": round(sum(deceased_vels) / len(deceased_vels), 1) if deceased_vels else 50.0,
        }

        # Estatísticas comparativas de clãs
        clan_differences = []
        if clans:
            org_by_id = {o.id: o for o in active_organisms}
            for c in clans:
                c_members = [org_by_id[mid] for mid in getattr(c, "member_ids", []) if mid in org_by_id]
                if not c_members:
                    continue
                c_forcas = [getattr(m.phenotype, "forca_muscular", 50.0) for m in c_members]
                c_vels = [getattr(m.phenotype, "velocidade", 50.0) for m in c_members]
                c_soc = [getattr(m.phenotype, "sociabilidade", 50.0) for m in c_members]
                c_inbreeding = [getattr(m.genotype, "inbreeding_coefficient", 0.0) for m in c_members]
                clan_differences.append({
                    "clan_id": getattr(c, "id", 0),
                    "clan_name": getattr(c, "name", f"Clã {getattr(c, 'id', 0)}"),
                    "member_count": len(c_members),
                    "avg_forca": round(sum(c_forcas) / len(c_forcas), 1),
                    "avg_velocidade": round(sum(c_vels) / len(c_vels), 1),
                    "avg_sociabilidade": round(sum(c_soc) / len(c_soc), 1),
                    "avg_inbreeding": round(sum(c_inbreeding) / len(c_inbreeding), 3),
                })

        return {
            "active_population_count": active_count,
            "total_records": len(self._records),
            "genetic_diversity": {
                "average_heterozygosity": round(total_hetero / active_count, 3),
                "average_inbreeding_coefficient": round(total_inbreeding / active_count, 3),
                "effective_population_size": ne,
                "unique_lineages": len(lineages_map),
            },
            "generations": generations_data,
            "lineages": lineages_summary,
            "mortality_by_cause": mortality_counts,
            "trait_survival_correlation": trait_survival_correlation,
            "clan_differences": clan_differences,
        }

    def to_snapshot(self) -> List[Dict[str, Any]]:
        return [rec.to_dict() for rec in self._records.values()]

    def from_snapshot(self, records_data: List[Dict[str, Any]]) -> None:
        self._records.clear()
        for data in records_data:
            rec = AnimalRecord.from_dict(data)
            self._records[rec.id] = rec

    def prune_ancient_records(
        self,
        active_organism_ids: Any,
        max_records: int = 2500,
    ) -> int:
        """
        Poda registros genealógicos antigos em sessões ultralongas para evitar crescimento ilimitado de memória (BUG-03).
        Preserva rigorosamente:
        1. Todos os organismos ativos vivos.
        2. Toda a árvore de ancestrais diretos dos organismos ativos até 6 gerações (profundidade de parentesco).
        3. Todos os pioneiros fundadores (Geração 0).
        Retorna a quantidade de registros podados.
        """
        if len(self._records) <= max_records:
            return 0

        active_set = set(active_organism_ids) if active_organism_ids else set()
        protected_ids: set[int] = set()

        # 1. Preserva todos os vivos e pioneiros
        for oid, rec in self._records.items():
            if oid in active_set or rec.generation == 0:
                protected_ids.add(oid)

        # 2. Preserva ancestrais diretos dos organismos vivos até 6 graus de parentesco
        frontier = set(active_set)
        for _ in range(6):
            next_frontier: set[int] = set()
            for oid in frontier:
                rec = self._records.get(oid)
                if rec:
                    if rec.father_id is not None:
                        protected_ids.add(rec.father_id)
                        next_frontier.add(rec.father_id)
                    if rec.mother_id is not None:
                        protected_ids.add(rec.mother_id)
                        next_frontier.add(rec.mother_id)
            frontier = next_frontier
            if not frontier:
                break

        # 3. Identifica registros descartáveis (falecidos fora da árvore de proteção)
        candidates = [
            (rec.birth_tick, oid)
            for oid, rec in self._records.items()
            if oid not in protected_ids and rec.death_tick is not None
        ]

        if not candidates:
            return 0

        # Ordena pelos mais antigos primeiro
        candidates.sort()
        to_prune_count = min(len(candidates), len(self._records) - max_records)
        pruned = 0
        for _, oid in candidates[:to_prune_count]:
            self._records.pop(oid, None)
            pruned += 1

        return pruned

    def get_phylogeny_tree(self, living_ids: Optional[set[int]] = None) -> Dict[str, Any]:
        """
        Gera uma representação em grafo e árvore hierárquica filogenética completa
        para visualização interativa de linhagens no frontend.
        """
        active_set = living_ids if living_ids is not None else set()
        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []
        lineages_summary: Dict[str, Dict[str, Any]] = {}
        max_gen = 0

        for oid, rec in self._records.items():
            if rec.generation > max_gen:
                max_gen = rec.generation

            genome = rec.genome or {}
            is_alive = oid in active_set

            nodes.append({
                "id": rec.id,
                "name": rec.name,
                "generation": rec.generation,
                "species": rec.species,
                "sex": rec.sex,
                "alive": is_alive,
                "birth_tick": rec.birth_tick,
                "death_tick": rec.death_tick,
                "father_id": rec.father_id,
                "mother_id": rec.mother_id,
                "inbreeding_coefficient": round(rec.inbreeding_coefficient, 3),
                "lineage_id": rec.lineage_id,
                "lineage_name": rec.lineage_name,
                "forca": round(genome.get("forca", 20.0), 1),
                "velocidade": round(genome.get("velocidade", 1.5), 1),
                "resistencia": round(genome.get("resistencia", 20.0), 1),
                "coleta": round(genome.get("coleta", 20.0), 1),
                "children_count": len(rec.children_ids),
            })

            # Conexões pai -> filho e mãe -> filho
            if rec.father_id is not None and rec.father_id in self._records:
                links.append({
                    "source": rec.father_id,
                    "target": rec.id,
                    "relationship": "father",
                })
            if rec.mother_id is not None and rec.mother_id in self._records:
                links.append({
                    "source": rec.mother_id,
                    "target": rec.id,
                    "relationship": "mother",
                })

            # Estatísticas da linhagem
            lin_name = rec.lineage_name or "Ancestral"
            if lin_name not in lineages_summary:
                lineages_summary[lin_name] = {
                    "name": lin_name,
                    "total_descendants": 0,
                    "alive_count": 0,
                    "founders": [],
                }
            lineages_summary[lin_name]["total_descendants"] += 1
            if is_alive:
                lineages_summary[lin_name]["alive_count"] += 1
            if rec.generation == 0 and rec.id not in lineages_summary[lin_name]["founders"]:
                lineages_summary[lin_name]["founders"].append(rec.id)

        return {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "max_generation": max_gen,
            "nodes": nodes,
            "links": links,
            "lineages": list(lineages_summary.values()),
        }


