"""Sistema de Aprendizado Individual, Consolidação Cognitiva e Transmissão Cultural Coletiva."""

from __future__ import annotations
import math
from typing import List, Dict, Tuple, Optional, Any
from ..entities.organism import Organism
from ..entities.knowledge import AnimalKnowledge, FoodHotspot, DangerHotspot
from ..spatial.spatial_grid import SpatialHashGrid
from ..prng import PRNG


class LearningSystem:
    """
    Gerencia a aquisição individual de experiência, consolidação de conhecimento empírico,
    extinção de crenças desatualizadas, transmissão cultural intergeracional e perda de tradições.
    """

    def __init__(self) -> None:
        self.total_social_transmissions = 0
        self.cultural_losses_count = 0
        self._last_decay_tick = 0

    def process_social_transmission(
        self,
        organisms: Dict[int, Organism],
        organism_grid: SpatialHashGrid[Organism],
        tick: int,
        events: List[Dict[str, Any]],
        prng: PRNG,
    ) -> None:
        """
        Executa transmissão social de conhecimento por proximidade espacial,
        oportunidade de observação e receptividade individual.
        """
        if tick % 8 != 0:
            return

        for learner in organisms.values():
            if not learner.alive:
                continue

            # Jovens e filhotes têm maior receptividade à aprendizagem social
            is_juvenile = getattr(learner, "life_stage", None) in (
                Organism.STAGE_DEVELOPING,
                Organism.STAGE_JUVENILE,
                Organism.STAGE_INDEPENDENT,
            )
            is_vranco = getattr(learner, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO

            # Raio de observação social (45px a 70px)
            obs_radius = 65.0
            nearby = organism_grid.query_radius(learner.x, learner.y, obs_radius)

            for teacher, dist in nearby:
                if teacher.id == learner.id or not teacher.alive:
                    continue

                # Somente mesma espécie transmite tradições sociais
                if getattr(teacher, "species", "") != learner.species:
                    continue

                # O mestre/modelo deve ser mais experiente que o aprendiz
                t_xp = teacher.knowledge.experience_points
                l_xp = learner.knowledge.experience_points
                if t_xp <= l_xp + 10.0 and getattr(teacher, "life_stage", "") != Organism.STAGE_ADULT:
                    continue

                # Taxa de assimilação modulada por inteligência genética e sociabilidade
                inteligencia = getattr(learner.genome, "inteligencia", 50.0)
                sociabilidade = getattr(learner.personality, "sociabilidade", 0.5)
                assimilation_chance = (0.20 + 0.35 * (inteligencia / 100.0) + 0.25 * sociabilidade)

                # Parentesco imediato (mãe/pai) potencializa transmissão
                is_parent = learner.father_id == teacher.id or learner.mother_id == teacher.id
                if is_parent:
                    assimilation_chance += 0.30

                if prng.random() > assimilation_chance:
                    continue

                # 1. Transmissão de Sítios Alimentares (Tradição de Forrageamento)
                for t_spot in teacher.knowledge.food_hotspots:
                    if t_spot.confidence >= 0.45:
                        already_knows = any(
                            math.hypot(s.x - t_spot.x, s.y - t_spot.y) <= 40.0
                            for s in learner.knowledge.food_hotspots
                        )
                        if not already_knows:
                            learner.knowledge.reinforce_food_spot(
                                t_spot.x,
                                t_spot.y,
                                tick,
                                learning_rate=0.20,
                                discovered_via="TRANSMISSAO_SOCIAL" if not is_parent else "IMITACAO_PARENTEAL",
                            )
                            learner.knowledge.social_transmissions_received += 1
                            teacher.knowledge.social_transmissions_given += 1
                            learner.knowledge.mentor_id = teacher.id
                            self.total_social_transmissions += 1

                            if prng.random() < 0.15 and len(events) < 50:
                                events.append({
                                    "type": "social_learning",
                                    "learner_name": learner.name,
                                    "teacher_name": teacher.name,
                                    "knowledge_type": "Sítio de Alimento",
                                    "tick": tick,
                                    "message": f"{learner.name} aprendeu sítio de alimento observando {teacher.name}",
                                })
                            break

                # 2. Transmissão de Consciência de Perigos (Zonas de Risco Conhecidas)
                for t_danger in teacher.knowledge.danger_hotspots:
                    if t_danger.danger_level >= 0.45:
                        already_knows = any(
                            math.hypot(d.x - t_danger.x, d.y - t_danger.y) <= 45.0
                            for d in learner.knowledge.danger_hotspots
                        )
                        if not already_knows:
                            learner.knowledge.reinforce_danger_spot(
                                t_danger.x,
                                t_danger.y,
                                tick,
                                intensity=t_danger.danger_level * 0.70,
                                threat_type=t_danger.threat_type,
                                discovered_via="ALERTA_SOCIAL",
                            )
                            learner.knowledge.social_transmissions_received += 1
                            teacher.knowledge.social_transmissions_given += 1
                            self.total_social_transmissions += 1
                            break

                # 3. Transmissão de Habilidades Táticas
                # Vrancos aprendem coordenação de evasão e mobbing
                if is_vranco:
                    t_evs = teacher.knowledge.tactical_skills.evasion_proficiency
                    l_evs = learner.knowledge.tactical_skills.evasion_proficiency
                    if t_evs > l_evs + 0.15:
                        learner.knowledge.tactical_skills.improve("evasion_proficiency", 0.04)
                        learner.knowledge.tactical_skills.improve("mobbing_coordination", 0.04)

                # Predadores aprendem discernimento e eficiência de caça
                else:
                    t_hunt = teacher.knowledge.tactical_skills.hunting_proficiency
                    l_hunt = learner.knowledge.tactical_skills.hunting_proficiency
                    if t_hunt > l_hunt + 0.15:
                        learner.knowledge.tactical_skills.improve("hunting_proficiency", 0.04)

    def record_feeding(self, organism: Organism, x: float, y: float, tick: int) -> None:
        """Registra e consolida experiência alimentar bem-sucedida."""
        inteligencia = getattr(organism.genome, "inteligencia", 50.0)
        # Taxa de aprendizado individual modulada por inteligência biológica
        learning_rate = 0.20 * (0.60 + 0.80 * (inteligencia / 100.0))
        organism.knowledge.reinforce_food_spot(x, y, tick, learning_rate=learning_rate)

    def check_food_site_extinction(
        self,
        organism: Organism,
        food_grid: SpatialHashGrid[Any],
        tick: int,
    ) -> None:
        """
        Verifica se um animal que procurava comida em um sítio consolidado encontrou a área desprovida de recursos.
        Provoca desaprendizado (extinção de crença desatualizada).
        """
        if getattr(organism, "current_state", "") != Organism.STATE_FORAGING:
            return

        for spot in organism.knowledge.food_hotspots:
            dist = math.hypot(organism.x - spot.x, organism.y - spot.y)
            if dist <= 35.0 and (tick - spot.last_visited_tick) >= 40:
                # Animal está no sítio aprendido. Há comida disponível nas redondezas imediatas?
                nearby_foods = food_grid.query_radius(spot.x, spot.y, 40.0)
                if not nearby_foods:
                    # Sítio esgotado! Aplica penalização de crença
                    organism.knowledge.penalize_food_spot(spot.x, spot.y, tick, penalty_rate=0.28)
                    break

    def record_attack(
        self,
        victim: Organism,
        attacker: Organism,
        x: float,
        y: float,
        tick: int,
        intensity: float = 0.60,
    ) -> None:
        """Registra experiência de agressão ou emboscada."""
        # 1. Consolida zona de perigo
        victim.knowledge.reinforce_danger_spot(
            x, y, tick, intensity=intensity, threat_type="PREDACAO"
        )
        # 2. Identifica e categoriza o agressor individual
        victim.knowledge.register_threat(
            attacker.id, attacker.name, tick, delta=intensity * 0.40
        )
        # 3. Desenvolve habilidade de fuga
        victim.knowledge.tactical_skills.improve("evasion_proficiency", 0.05)

    def record_witnessed_kill(
        self,
        witness: Organism,
        x: float,
        y: float,
        tick: int,
    ) -> None:
        """Consolida percepção de perigo ao testemunhar o óbito violento de outro animal."""
        witness.knowledge.reinforce_danger_spot(
            x, y, tick, intensity=0.50, threat_type="MORTE_TESTEMUNHADA"
        )
        witness.knowledge.tactical_skills.improve("evasion_proficiency", 0.03)

    def record_successful_hunt(self, predator: Organism, target: Organism, tick: int) -> None:
        """Aprimora a proficiência de caça do predador após abate bem-sucedido."""
        predator.knowledge.tactical_skills.improve("hunting_proficiency", 0.06)
        predator.knowledge.experience_points += 6.0

    def record_successful_defense(self, vranco: Organism, tick: int) -> None:
        """Aprimora a coordenação de mobbing e autoconfiança defensiva do Vranco."""
        vranco.knowledge.tactical_skills.improve("mobbing_coordination", 0.06)
        vranco.knowledge.experience_points += 4.5

    def on_organism_death(
        self,
        deceased: Organism,
        surviving_organisms: Dict[int, Organism],
        tick: int,
        events: List[Dict[str, Any]],
    ) -> None:
        """
        Detecta e registra potencial perda cultural e empírica com a morte de indivíduos veteranos.
        """
        if deceased.knowledge.experience_points < 35.0 and len(deceased.knowledge.food_hotspots) < 2:
            return

        # Verifica se algum sobrevivente da mesma espécie/clã compartilha o conhecimento do falecido
        same_cohort = [
            o for o in surviving_organisms.values()
            if o.alive and o.species == deceased.species and (deceased.clan_id is None or o.clan_id == deceased.clan_id)
        ]

        if not same_cohort:
            return

        # Compara se há sítios conhecidos exclusivamente pelo veterano
        unshared_spots = 0
        for spot in deceased.knowledge.food_hotspots:
            if spot.confidence >= 0.45:
                shared = any(
                    any(math.hypot(s.x - spot.x, s.y - spot.y) <= 40.0 for s in survivor.knowledge.food_hotspots)
                    for survivor in same_cohort
                )
                if not shared:
                    unshared_spots += 1

        if unshared_spots > 0:
            self.cultural_losses_count += 1
            if len(events) < 50:
                events.append({
                    "type": "cultural_loss",
                    "veteran_name": deceased.name,
                    "lost_hotspots": unshared_spots,
                    "experience_lost": round(deceased.knowledge.experience_points, 1),
                    "tick": tick,
                    "message": f"Perda Cultural: {deceased.name} faleceu levando conhecimento exclusivo de {unshared_spots} sítio(s)",
                })

    def decay_and_maintain(self, organisms: Dict[int, Organism], current_tick: int) -> None:
        """Aplica decaimento temporal suave em crenças e sítios não revisitados."""
        if current_tick - self._last_decay_tick < 40:
            return
        self._last_decay_tick = current_tick

        for o in organisms.values():
            if o.alive:
                o.knowledge.decay_all(current_tick)

    def get_cultural_metrics(self, organisms: Dict[int, Organism]) -> Dict[str, Any]:
        """Calcula indicadores consolidados de inteligência ecológica e sabedoria coletiva."""
        alive_orgs = [o for o in organisms.values() if o.alive]
        total_alive = max(1, len(alive_orgs))

        vrancos = [o for o in alive_orgs if getattr(o, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO]
        predators = [o for o in alive_orgs if getattr(o, "species", Organism.SPECIES_PREDATOR) != Organism.SPECIES_VRANCO]

        total_xp = sum(o.knowledge.experience_points for o in alive_orgs)
        avg_xp = round(total_xp / total_alive, 1)

        veterans_count = sum(1 for o in alive_orgs if o.knowledge.experience_points >= 40.0)

        avg_evasion = round(sum(o.knowledge.tactical_skills.evasion_proficiency for o in vrancos) / max(1, len(vrancos)), 2)
        avg_mobbing = round(sum(o.knowledge.tactical_skills.mobbing_coordination for o in vrancos) / max(1, len(vrancos)), 2)
        avg_hunting = round(sum(o.knowledge.tactical_skills.hunting_proficiency for o in predators) / max(1, len(predators)), 2)
        avg_foraging = round(sum(o.knowledge.tactical_skills.foraging_efficiency for o in alive_orgs) / total_alive, 2)

        # Média de sítios de comida retidos por animal
        total_hotspots = sum(len(o.knowledge.food_hotspots) for o in alive_orgs)
        avg_hotspots = round(total_hotspots / total_alive, 1)

        mentored_count = sum(1 for o in alive_orgs if o.knowledge.mentor_id is not None)

        return {
            "avg_experience": avg_xp,
            "veterans_count": veterans_count,
            "veterans_pct": round((veterans_count / total_alive) * 100.0, 1),
            "total_social_transmissions": self.total_social_transmissions,
            "cultural_losses_count": self.cultural_losses_count,
            "avg_evasion_skill": avg_evasion,
            "avg_mobbing_skill": avg_mobbing,
            "avg_hunting_skill": avg_hunting,
            "avg_foraging_skill": avg_foraging,
            "avg_learned_hotspots": avg_hotspots,
            "mentored_count": mentored_count,
        }
