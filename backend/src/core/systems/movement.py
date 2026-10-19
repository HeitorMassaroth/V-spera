"""Sistema de cinemática e steering behaviors para organismos autônomos."""

from __future__ import annotations
import math
from typing import Tuple, Optional, Dict, Set
from ..entities.organism import Organism
from ..entities.food import Food
from ..prng import PRNG
from ..spatial.spatial_grid import SpatialHashGrid


class MovementSystem:
    """Implementa cinemática newtoniana e comportamentos de navegação (Reynolds)."""

    def __init__(
        self,
        world_width: float,
        world_height: float,
        boundary_margin: float = 40.0,
        wall_repulsion_force: float = 0.8,
    ) -> None:
        self.width = float(world_width)
        self.height = float(world_height)
        self.margin = float(boundary_margin)
        self.wall_force = float(wall_repulsion_force)

    def calculate_steering(
        self,
        organism: Organism,
        target_food: Optional[Food],
        prng: PRNG,
        organism_grid: Optional[SpatialHashGrid[Organism]] = None,
    ) -> Tuple[float, float]:
        """Calcula as forças direcionais aplicadas ao organismo no ciclo atual."""
        # 1. Recém-nascidos são imóveis no ninho familiar
        if getattr(organism, "life_stage", None) == Organism.STAGE_NEWBORN:
            organism.vx = 0.0
            organism.vy = 0.0
            return 0.0, 0.0

        # 1. Atualização de cooldown territorial e alvo de migração
        if getattr(organism, "territory_cooldown", 0) > 0:
            organism.territory_cooldown -= 1

        target_mig = getattr(organism, "target_migration_zone", None)
        if target_mig is not None:
            dist_mig = math.hypot(organism.x - target_mig[0], organism.y - target_mig[1])
            if dist_mig <= 35.0:
                organism.target_migration_zone = None
                target_mig = None

        # 2. Filhotes em desenvolvimento mantêm proximidade física com o ninho
        if getattr(organism, "life_stage", None) == Organism.STAGE_DEVELOPING:
            if getattr(organism, "memory", None) and organism.memory.safe_haven is not None:
                hx, hy = organism.memory.safe_haven
                dist_h = math.hypot(organism.x - hx, organism.y - hy)
                if dist_h > 26.0:
                    steer_x, steer_y = self._seek(organism, hx, hy)
                    wall_x, wall_y = self._boundary_repulsion(organism)
                    return steer_x + wall_x, steer_y + wall_y

        is_vranco = getattr(organism, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO
        current_state = getattr(organism, "current_state", Organism.STATE_FORAGING)
        steer_x, steer_y = 0.0, 0.0
        special_behavior_active = False

        # Avaliação de vizinhança biológica via spatial grid
        nearby_predators: List[Tuple[Organism, float]] = []
        nearby_vrancos: List[Tuple[Organism, float]] = []
        if organism_grid is not None:
            vision_r = organism.traits.vision_radius
            nearby_entities = organism_grid.query_radius(organism.x, organism.y, vision_r)
            for other, d in nearby_entities:
                if other.id == organism.id or not other.alive:
                    continue
                if getattr(other, "species", Organism.SPECIES_PREDATOR) == Organism.SPECIES_VRANCO:
                    nearby_vrancos.append((other, d))
                else:
                    nearby_predators.append((other, d))

        # -------------------------------------------------------------
        # COMPORTAMENTO ESPECÍFICO DOS VRANCOS (Fuga, Coesão e Periferia)
        # -------------------------------------------------------------
        if is_vranco:
            if nearby_predators:
                # 1. Identifica o predador mais próximo e avalia o perigo
                closest_pred, pred_dist = min(nearby_predators, key=lambda p: p[1])

                # Avalia estado físico: Vranco cansado ou ferido perde capacidade de aceleração máxima
                fatigue_factor = max(0.40, min(1.0, (organism.energy / 75.0) * (organism.saude / organism.max_saude)))

                # Influência da Memória e Cautela: Vranco que sobreviveu a ataque anterior ou presenciou morte reage com maior agilidade e urgência
                alert_boost = 1.0
                if getattr(organism, "memory", None):
                    trauma_intensity = sum(
                        ep.intensity * ep.relevance for ep in organism.memory.episodes
                        if ep.event_type in ("ATTACKED_BY", "WITNESSED_DEATH")
                    )
                    if trauma_intensity > 0.15:
                        cautela_val = getattr(organism.personality, "cautela", 0.5)
                        alert_boost = 1.0 + min(0.50, trauma_intensity * 0.45 * (0.6 + 0.8 * cautela_val))

                # Conta indivíduos capazes de cooperação defensiva em raio próximo (85px)
                capable_group = [
                    v for v, d in nearby_vrancos
                    if d <= 85.0 and getattr(v, "life_stage", None) == Organism.STAGE_ADULT and v.energy >= 35.0 and v.saude >= v.max_saude * 0.40
                ]
                flock_size = len(capable_group) + 1  # Inclui a si mesmo

                # Cálculo de Força Coletiva do Grupo com Retornos Decrescentes e Coordenação Tática
                collective_power = 0.0
                all_capable = capable_group + [organism]
                for idx, v_cap in enumerate(all_capable, start=1):
                    diminishing_factor = 1.0 / math.sqrt(idx)
                    v_pwr = v_cap.genome.forca * (v_cap.energy / 100.0) * (v_cap.saude / v_cap.max_saude)
                    # Coordenação de mobbing aprendida aumenta eficácia da cooperação defensiva
                    mob_skill = v_cap.knowledge.tactical_skills.mobbing_coordination if getattr(v_cap, "knowledge", None) else 0.15
                    collective_power += v_pwr * (1.0 + mob_skill * 0.5) * diminishing_factor

                pred_power = closest_pred.genome.forca * (closest_pred.energy / 100.0) * (closest_pred.saude / closest_pred.genome.max_saude)

                # Se a força coletiva do grupo for suficiente (flock_size >= 4 e poder > limiar adaptado):
                # Mantêm formação defensiva coletiva / mobbing
                coragem_val = getattr(organism.personality, "coragem", 0.4)
                my_mob_skill = organism.knowledge.tactical_skills.mobbing_coordination if getattr(organism, "knowledge", None) else 0.15
                mob_threshold = pred_power * (1.25 - coragem_val * 0.20 - my_mob_skill * 0.20)
                if flock_size >= 4 and collective_power >= mob_threshold:
                    organism.current_state = Organism.STATE_DEFENDING
                    # Aproximação cautelosa para cercar e pressionar o predador
                    app_x, app_y = self._seek(organism, closest_pred.x, closest_pred.y)
                    steer_x = app_x * (0.35 + my_mob_skill * 0.15)
                    steer_y = app_y * (0.35 + my_mob_skill * 0.15)
                    special_behavior_active = True
                else:
                    # Risco individual elevado: Dispara FUGA IMEDIATA e avisa parceiros próximos!
                    organism.current_state = Organism.STATE_FLEEING
                    for v_near, _ in nearby_vrancos:
                        if getattr(v_near, "memory", None):
                            v_near.memory.add_danger_zone(closest_pred.x, closest_pred.y, 0)

                    # Vetor de evasão oposto ao predador
                    fdir_x = (organism.x - closest_pred.x) / max(0.1, pred_dist)
                    fdir_y = (organism.y - closest_pred.y) / max(0.1, pred_dist)

                    # Se houver outros Vrancos por perto, fogem coalescendo juntos em direção ao grupo
                    if nearby_vrancos:
                        avg_vx = sum(v.x for v, _ in nearby_vrancos) / len(nearby_vrancos)
                        avg_vy = sum(v.y for v, _ in nearby_vrancos) / len(nearby_vrancos)
                        dist_flock = math.hypot(avg_vx - organism.x, avg_vy - organism.y)
                        if dist_flock > 10.0:
                            fdir_x = fdir_x * 0.70 + ((avg_vx - organism.x) / dist_flock) * 0.30
                            fdir_y = fdir_y * 0.70 + ((avg_vy - organism.y) / dist_flock) * 0.30

                    # Conhecimento empírico de perigo específico deste predador
                    known_threat = organism.knowledge.get_threat(closest_pred.id) if getattr(organism, "knowledge", None) else None
                    threat_boost = 1.0 + (known_threat.threat_score * 0.25) if known_threat else 1.0

                    # Habilidade tática aprendida: Evasão e fuga refinada
                    evasion_skill = organism.knowledge.tactical_skills.evasion_proficiency if getattr(organism, "knowledge", None) else 0.15
                    evasion_boost = 1.0 + (evasion_skill * 0.35)

                    # Velocidade de fuga proporcional ao fator físico de cansaço, alerta, ameaça conhecida e perícia tática
                    des_vx = fdir_x * (organism.traits.max_speed * fatigue_factor * alert_boost * threat_boost * evasion_boost)
                    des_vy = fdir_y * (organism.traits.max_speed * fatigue_factor * alert_boost * threat_boost * evasion_boost)

                    # Fuga consome energia (custo metabólico da adrenalina e arrancada)
                    organism.energy = max(0.0, organism.energy - 0.035)

                    fx = des_vx - organism.vx
                    fy = des_vy - organism.vy
                    steer_x, steer_y = self._clamp_vector(fx, fy, organism.traits.max_force * (1.6 * alert_boost * evasion_boost))
                    special_behavior_active = True
            else:
                # Quando a ameaça cessa, retorno gradual às atividades
                if current_state == Organism.STATE_FLEEING:
                    organism.current_state = Organism.STATE_RESTING if organism.energy < 40.0 else Organism.STATE_FORAGING

        # -------------------------------------------------------------
        # COMPORTAMENTO DOS PREDADORES (Avaliação Estratégica e Memória de Rivalidades)
        # -------------------------------------------------------------
        elif not is_vranco:
            # A. Avaliação de Agressões, Medo, Hostilidade e Rivalidades entre Predadores
            feared_rivals = []
            if nearby_predators:
                for p, d in nearby_predators:
                    grudge = organism.memory.get_grudge_score(p.id) if getattr(organism, "memory", None) else 0.0
                    rel = organism.relationships.get(p.id) if hasattr(organism, "relationships") else None
                    fear_val = rel.fear if rel else 0.0
                    host_val = rel.hostility if rel else 0.0
                    rival_val = rel.rivalry if rel else 0.0
                    threat_level = max(grudge, fear_val, host_val * 0.75, rival_val * 0.65)
                    if threat_level >= 0.35:
                        feared_rivals.append((p, d, threat_level))

            if feared_rivals:
                feared_p, d_feared, threat_val = min(feared_rivals, key=lambda item: item[1])
                cautela_val = getattr(organism.personality, "cautela", 0.5)
                coragem_val = getattr(organism.personality, "coragem", 0.5)
                # Predador cauteloso, ferido ou com medo expressivo evita enfrentar o adversário
                if cautela_val >= coragem_val * 0.85 or organism.saude < organism.max_saude * 0.70 or threat_val >= 0.60:
                    organism.current_state = Organism.STATE_FLEEING
                    fdir_x = (organism.x - feared_p.x) / max(0.1, d_feared)
                    fdir_y = (organism.y - feared_p.y) / max(0.1, d_feared)
                    avoid_vx = fdir_x * organism.traits.max_speed * 0.85
                    avoid_vy = fdir_y * organism.traits.max_speed * 0.85
                    steer_x, steer_y = self._clamp_vector(avoid_vx - organism.vx, avoid_vy - organism.vy, organism.traits.max_force * 1.3)
                    special_behavior_active = True

            # B. Caça a Vrancos (se não estiver fugindo de um rival temido)
            if not special_behavior_active and nearby_vrancos:
                capable_vrancos = [
                    v for v, d in nearby_vrancos
                    if getattr(v, "life_stage", None) == Organism.STAGE_ADULT and v.energy >= 35.0 and v.saude >= v.max_saude * 0.40
                ]
                if len(capable_vrancos) >= 4 and organism.energy > 35.0:
                    # Grupo organizado representa risco: Predador recua suavemente
                    avg_vx = sum(v.x for v in capable_vrancos) / len(capable_vrancos)
                    avg_vy = sum(v.y for v in capable_vrancos) / len(capable_vrancos)
                    d_flock = math.hypot(avg_vx - organism.x, avg_vy - organism.y)
                    if d_flock < 70.0 and d_flock > 1e-4:
                        avoid_vx = ((organism.x - avg_vx) / d_flock) * organism.traits.max_speed * 0.6
                        avoid_vy = ((organism.y - avg_vy) / d_flock) * organism.traits.max_speed * 0.6
                        steer_x, steer_y = self._clamp_vector(avoid_vx - organism.vx, avoid_vy - organism.vy, organism.traits.max_force)
                        special_behavior_active = True
                elif organism.energy < 70.0 or getattr(organism.personality, "agressividade", 0.5) > 0.40:
                    weakest_vranco, dist_target = min(nearby_vrancos, key=lambda vd: (vd[0].saude + vd[0].energy + vd[1] * 0.5))
                    if dist_target < 90.0:
                        organism.current_state = Organism.STATE_HUNTING
                        hunt_x, hunt_y = self._seek(organism, weakest_vranco.x, weakest_vranco.y)
                        hunt_skill = organism.knowledge.tactical_skills.hunting_proficiency if getattr(organism, "knowledge", None) else 0.15
                        steer_x = hunt_x * (0.8 + 0.35 * hunt_skill)
                        steer_y = hunt_y * (0.8 + 0.35 * hunt_skill)
                        special_behavior_active = True

        # 3. Comportamento padrão guiado por Migração Territorial, Conhecimento, Personalidade e Relações Sociais
        if not special_behavior_active:
            if target_mig is not None and (target_food is None or organism.energy > 35.0):
                # Deslocamento coordenado e intencional para o novo território selecionado
                steer_x, steer_y = self._seek(organism, target_mig[0], target_mig[1])
            elif current_state == Organism.STATE_DELIVERING_FOOD and getattr(organism, "memory", None) and organism.memory.safe_haven:
                steer_x, steer_y = self._seek(organism, organism.memory.safe_haven[0], organism.memory.safe_haven[1])
            elif target_food is not None:
                steer_x, steer_y = self._seek(organism, target_food.x, target_food.y)
                # Persistência e eficiência de forrageamento aprendida
                persistencia_val = getattr(organism.personality, "persistencia", 0.5)
                foraging_skill = organism.knowledge.tactical_skills.foraging_efficiency if getattr(organism, "knowledge", None) else 0.15
                efficiency_mult = (0.85 + persistencia_val * 0.30) * (1.0 + foraging_skill * 0.20)
                steer_x *= efficiency_mult
                steer_y *= efficiency_mult
            elif getattr(organism, "knowledge", None) and organism.knowledge.food_hotspots and any(h.confidence >= 0.25 for h in organism.knowledge.food_hotspots):
                # Conhecimento empírico consolidado: navega para hotspot conhecido com maior utilidade esperada
                valid_spots = [h for h in organism.knowledge.food_hotspots if h.confidence >= 0.25]
                best_spot = max(valid_spots, key=lambda h: h.confidence / (1.0 + math.hypot(organism.x - h.x, organism.y - h.y) * 0.008))
                steer_x, steer_y = self._seek(organism, best_spot.x, best_spot.y)
                foraging_skill = organism.knowledge.tactical_skills.foraging_efficiency
                steer_x *= (0.9 + foraging_skill * 0.25)
                steer_y *= (0.9 + foraging_skill * 0.25)
            elif getattr(organism, "energy", 100.0) < 55.0 and getattr(organism, "memory", None) and (organism.memory.known_food_sources or [ep for ep in organism.memory.episodes if ep.event_type == "FOUND_FOOD"]):
                # Memória episódica de onde encontrou alimento anteriormente (fallback)
                if organism.memory.known_food_sources:
                    kx, ky, _ = organism.memory.known_food_sources[0]
                else:
                    food_ep = [ep for ep in organism.memory.episodes if ep.event_type == "FOUND_FOOD"][0]
                    kx, ky = food_ep.x, food_ep.y
                steer_x, steer_y = self._seek(organism, kx, ky)
            else:
                steer_x, steer_y = self._wander(organism, prng)

            # Mentoria e Aprendizado Social: Jovens acompanham adultos experientes ou mentores
            mentor_followed = False
            cohort = nearby_vrancos if is_vranco else nearby_predators
            if getattr(organism, "knowledge", None) and organism.knowledge.mentor_id is not None and target_food is None:
                for friend, d_friend in cohort:
                    if friend.id == organism.knowledge.mentor_id and 15.0 < d_friend <= 80.0:
                        m_x, m_y = self._seek(organism, friend.x, friend.y)
                        steer_x = steer_x * 0.65 + m_x * 0.35
                        steer_y = steer_y * 0.65 + m_y * 0.35
                        mentor_followed = True
                        break

            # Se jovem sem mentor fixo, acompanha o adulto mais experiente nas proximidades
            if not mentor_followed and getattr(organism, "life_stage", None) in (Organism.STAGE_JUVENILE, Organism.STAGE_DEVELOPING) and target_food is None:
                experienced_adults = [
                    (adult, d) for adult, d in cohort
                    if getattr(adult, "life_stage", None) == Organism.STAGE_ADULT and getattr(adult, "knowledge", None) and adult.knowledge.experience_points >= 25.0 and 20.0 < d <= 75.0
                ]
                if experienced_adults:
                    best_adult, _ = max(experienced_adults, key=lambda ad: getattr(ad[0].knowledge, "experience_points", 0.0))
                    a_x, a_y = self._seek(organism, best_adult.x, best_adult.y)
                    steer_x = steer_x * 0.70 + a_x * 0.30
                    steer_y = steer_y * 0.70 + a_y * 0.30

            # Afinidade Social, Confiança e Gratidão em relação a quem prestou socorro / parentes / aliados
            if getattr(organism, "personality", None) and target_food is None:
                for friend, d_friend in cohort:
                    if d_friend > 25.0:
                        gratitude = organism.memory.get_gratitude_score(friend.id) if getattr(organism, "memory", None) else 0.0
                        rel = organism.relationships.get(friend.id) if hasattr(organism, "relationships") else None
                        rel_pull = 0.0
                        if rel:
                            coop_bonus = min(0.30, rel.cooperation_count * 0.05)
                            rel_pull = max(0.0, (rel.affinity * 0.5 + rel.trust * 0.5 + coop_bonus))
                        total_social_pull = max(gratitude, rel_pull)
                        if total_social_pull > 0.25:
                            soc = getattr(organism.personality, "sociabilidade", 0.5)
                            fr_x, fr_y = self._seek(organism, friend.x, friend.y)
                            pull = min(0.35, total_social_pull * 0.20 * soc)
                            steer_x = steer_x * (1.0 - pull) + fr_x * pull
                            steer_y = steer_y * (1.0 - pull) + fr_y * pull
                            break

            # Para Vrancos: Coesão Social e Preferência Territorial Periférica
            if is_vranco:
                if nearby_vrancos and len(nearby_vrancos) <= 8 and target_food is None:
                    soc_factor = getattr(organism.personality, "sociabilidade", 0.8)
                    avg_fx = sum(v.x for v, _ in nearby_vrancos) / len(nearby_vrancos)
                    avg_fy = sum(v.y for v, _ in nearby_vrancos) / len(nearby_vrancos)
                    cohesion_x, cohesion_y = self._seek(organism, avg_fx, avg_fy)
                    steer_x = steer_x * (1.0 - 0.22 * soc_factor) + cohesion_x * (0.22 * soc_factor)
                    steer_y = steer_y * (1.0 - 0.22 * soc_factor) + cohesion_y * (0.22 * soc_factor)

                p_fx, p_fy = self._seek_periphery(organism)
                steer_x += p_fx
                steer_y += p_fy

        # 4. Evasão inteligente de Zonas e Hotspots de Perigo (Memória Episódica + Conhecimento de Rotas Seguras)
        danger_fx, danger_fy = 0.0, 0.0
        cautela = getattr(organism.personality, "cautela", 0.5) if getattr(organism, "personality", None) else 0.5
        if cautela > 0.25:
            # A. Episódios recentes de perigo na memória episódica
            if getattr(organism, "memory", None) and organism.memory.danger_zones:
                for zx, zy, _ in organism.memory.danger_zones:
                    dz_dist = math.hypot(organism.x - zx, organism.y - zy)
                    if 0.1 < dz_dist < 55.0:
                        repel_mag = (1.0 - (dz_dist / 55.0)) * cautela * 0.35
                        danger_fx += ((organism.x - zx) / dz_dist) * repel_mag
                        danger_fy += ((organism.y - zy) / dz_dist) * repel_mag

            # B. Conhecimento consolidado de Hotspots de Perigo (Rotas Mais Seguras)
            if getattr(organism, "knowledge", None) and organism.knowledge.danger_hotspots:
                for dspot in organism.knowledge.danger_hotspots:
                    if dspot.danger_level >= 0.20:
                        dh_dist = math.hypot(organism.x - dspot.x, organism.y - dspot.y)
                        r = getattr(dspot, "radius", 55.0)
                        if 0.1 < dh_dist < r:
                            repel_mag = (1.0 - (dh_dist / r)) * dspot.danger_level * (0.45 + 0.5 * cautela)
                            danger_fx += ((organism.x - dspot.x) / dh_dist) * repel_mag
                            danger_fy += ((organism.y - dspot.y) / dh_dist) * repel_mag

        # 5. Adiciona força de repulsão suave das paredes
        wall_x, wall_y = self._boundary_repulsion(organism)

        total_fx = steer_x + danger_fx + wall_x
        total_fy = steer_y + danger_fy + wall_y
        return total_fx, total_fy

    def _seek(self, organism: Organism, target_x: float, target_y: float) -> Tuple[float, float]:
        """Calcula força de aceleração em direção a um alvo com clamp em max_force."""
        dx = target_x - organism.x
        dy = target_y - organism.y
        dist = math.hypot(dx, dy)

        if dist < 1e-5:
            return 0.0, 0.0

        # Velocidade desejada com magnitude máxima
        desired_vx = (dx / dist) * organism.traits.max_speed
        desired_vy = (dy / dist) * organism.traits.max_speed

        # Força de Reynolds: Desired - Velocity
        fx = desired_vx - organism.vx
        fy = desired_vy - organism.vy

        return self._clamp_vector(fx, fy, organism.traits.max_force)

    def _wander(self, organism: Organism, prng: PRNG) -> Tuple[float, float]:
        """Calcula aceleração de vagueio suave com coerência angular no tempo e modulação por curiosidade."""
        curiosidade = getattr(organism.personality, "curiosidade", 0.5)
        angle_spread = 0.20 + curiosidade * 0.30
        delta_angle = prng.uniform(-angle_spread, angle_spread)
        organism.wander_angle += delta_angle

        # Parâmetros do círculo imaginário à frente: maior curiosidade = exploração mais distante
        circle_dist = 25.0 + curiosidade * 25.0
        circle_radius = 15.0 + curiosidade * 12.0

        # Orientação atual do organismo (ou ângulo padrão se estiver parado)
        current_heading = organism.heading if organism.speed > 0.01 else organism.wander_angle

        # Centro do círculo à frente
        circle_center_x = organism.x + math.cos(current_heading) * circle_dist
        circle_center_y = organism.y + math.sin(current_heading) * circle_dist

        # Ponto alvo no perímetro do círculo
        target_angle = current_heading + organism.wander_angle
        target_x = circle_center_x + math.cos(target_angle) * circle_radius
        target_y = circle_center_y + math.sin(target_angle) * circle_radius

        return self._seek(organism, target_x, target_y)

    def _boundary_repulsion(self, organism: Organism) -> Tuple[float, float]:
        """Gera forças repulsivas contínuas quando o organismo se aproxima dos limites do mundo."""
        fx = 0.0
        fy = 0.0

        # Borda esquerda
        if organism.x < self.margin:
            penetration = (self.margin - organism.x) / self.margin
            fx += self.wall_force * penetration
        # Borda direita
        elif organism.x > self.width - self.margin:
            penetration = (organism.x - (self.width - self.margin)) / self.margin
            fx -= self.wall_force * penetration

        # Borda superior
        if organism.y < self.margin:
            penetration = (self.margin - organism.y) / self.margin
            fy += self.wall_force * penetration
        # Borda inferior
        elif organism.y > self.height - self.margin:
            penetration = (organism.y - (self.height - self.margin)) / self.margin
            fy -= self.wall_force * penetration

        return fx, fy

    def _seek_periphery(self, organism: Organism) -> Tuple[float, float]:
        """Calcula força suave de migração radial em direção à periferia habitável para Vrancos."""
        if getattr(organism, "species", Organism.SPECIES_PREDATOR) != Organism.SPECIES_VRANCO:
            return 0.0, 0.0
        # Tendência flexível: se estiver com fome aguda (< 38.0) ou com destino migratório ativo,
        # a preferência periférica cede passagem para alimentação no interior ou viagem
        if organism.energy < 38.0 or getattr(organism, "target_migration_zone", None) is not None:
            return 0.0, 0.0
        cx = self.width / 2.0
        cy = self.height / 2.0
        dist_center = math.hypot(organism.x - cx, organism.y - cy)
        center_radius = min(self.width, self.height) * 0.38
        if dist_center < center_radius:
            outward_mag = (1.0 - (dist_center / center_radius)) * 0.12
            if dist_center < 1e-3:
                return outward_mag, 0.0
            periph_fx = ((organism.x - cx) / dist_center) * outward_mag
            periph_fy = ((organism.y - cy) / dist_center) * outward_mag
            return periph_fx, periph_fy
        return 0.0, 0.0

    def update_physics(
        self,
        organism: Organism,
        force_x: float,
        force_y: float,
        dt: float = 1.0,
    ) -> None:
        """Aplica as forças, atualiza velocidade e posição com integração de Euler."""
        # Massa aproximada proporcional ao volume celular (r^2)
        mass = max(0.5, (organism.traits.size / 5.0) ** 2)
        ax = force_x / mass
        ay = force_y / mass

        # Integração de velocidade
        new_vx = organism.vx + ax * dt
        new_vy = organism.vy + ay * dt

        # Clamp de velocidade por max_speed
        organism.vx, organism.vy = self._clamp_vector(new_vx, new_vy, organism.traits.max_speed)

        # Integração de posição
        organism.x += organism.vx * dt
        organism.y += organism.vy * dt

        # Barreira física de salvaguarda (clamp estrito nos limites)
        radius = organism.traits.size
        if organism.x < radius:
            organism.x = radius
            organism.vx = abs(organism.vx) * 0.5
        elif organism.x > self.width - radius:
            organism.x = self.width - radius
            organism.vx = -abs(organism.vx) * 0.5

        if organism.y < radius:
            organism.y = radius
            organism.vy = abs(organism.vy) * 0.5
        elif organism.y > self.height - radius:
            organism.y = self.height - radius
            organism.vy = -abs(organism.vy) * 0.5

    @staticmethod
    def _clamp_vector(vx: float, vy: float, max_mag: float) -> Tuple[float, float]:
        """Trunca a magnitude euclidiana de um vetor bidimensional."""
        mag = math.hypot(vx, vy)
        if mag > max_mag and mag > 1e-6:
            factor = max_mag / mag
            return vx * factor, vy * factor
        return vx, vy

    def resolve_organism_collisions(
        self,
        organisms: Dict[int, Organism],
        spatial_grid: SpatialHashGrid[Organism],
    ) -> None:
        """Resolve colisões e impede sobreposição física entre organismos."""
        processed_pairs: Set[Tuple[int, int]] = set()

        for org in sorted(organisms.values(), key=lambda o: o.id):
            if not org.alive:
                continue

            query_radius = org.traits.size * 2.5
            nearby = spatial_grid.query_radius(org.x, org.y, query_radius)

            for other, dist in nearby:
                if other.id == org.id or not other.alive:
                    continue

                pair_key = (min(org.id, other.id), max(org.id, other.id))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                min_dist = org.traits.size + other.traits.size

                if dist < min_dist:
                    overlap = min_dist - dist
                    if dist > 1e-4:
                        nx = (org.x - other.x) / dist
                        ny = (org.y - other.y) / dist
                    else:
                        nx = 1.0
                        ny = 0.0

                    m1 = max(0.5, (org.traits.size / 5.0) ** 2)
                    m2 = max(0.5, (other.traits.size / 5.0) ** 2)
                    total_mass = m1 + m2

                    ratio1 = m2 / total_mass
                    ratio2 = m1 / total_mass

                    org.x += nx * overlap * ratio1
                    org.y += ny * overlap * ratio1
                    other.x -= nx * overlap * ratio2
                    other.y -= ny * overlap * ratio2

                    # Resposta de velocidade elástica com amortecimento
                    rvx = org.vx - other.vx
                    rvy = org.vy - other.vy
                    vel_along_normal = rvx * nx + rvy * ny

                    if vel_along_normal < 0:
                        restitution = 0.55
                        impulse_mag = -(1.0 + restitution) * vel_along_normal / (1.0 / m1 + 1.0 / m2)
                        org.vx += (impulse_mag / m1) * nx
                        org.vy += (impulse_mag / m1) * ny
                        other.vx -= (impulse_mag / m2) * nx
                        other.vy -= (impulse_mag / m2) * ny
