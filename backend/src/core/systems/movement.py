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
    ) -> Tuple[float, float]:
        """Calcula as forças direcionais aplicadas ao organismo no ciclo atual."""
        # 1. Recém-nascidos são imóveis no ninho familiar
        if getattr(organism, "life_stage", None) == Organism.STAGE_NEWBORN:
            organism.vx = 0.0
            organism.vy = 0.0
            return 0.0, 0.0

        # 2. Filhotes em desenvolvimento mantêm proximidade física com o ninho
        if getattr(organism, "life_stage", None) == Organism.STAGE_DEVELOPING:
            if getattr(organism, "memory", None) and organism.memory.safe_haven is not None:
                hx, hy = organism.memory.safe_haven
                dist_h = math.hypot(organism.x - hx, organism.y - hy)
                if dist_h > 26.0:
                    steer_x, steer_y = self._seek(organism, hx, hy)
                    wall_x, wall_y = self._boundary_repulsion(organism)
                    return steer_x + wall_x, steer_y + wall_y

        # 3. Steering baseado no estado comportamental atual
        current_state = getattr(organism, "current_state", Organism.STATE_FORAGING)

        if current_state == Organism.STATE_DELIVERING_FOOD and getattr(organism, "memory", None) and organism.memory.safe_haven:
            steer_x, steer_y = self._seek(organism, organism.memory.safe_haven[0], organism.memory.safe_haven[1])
        elif target_food is not None:
            steer_x, steer_y = self._seek(organism, target_food.x, target_food.y)
        elif getattr(organism, "energy", 100.0) < 45.0 and getattr(organism, "memory", None) and organism.memory.known_food_sources:
            kx, ky, _ = organism.memory.known_food_sources[0]
            steer_x, steer_y = self._seek(organism, kx, ky)
        else:
            steer_x, steer_y = self._wander(organism, prng)

        # 4. Evasão inteligente de Zonas de Perigo (Memória e Cautela)
        danger_fx, danger_fy = 0.0, 0.0
        if getattr(organism, "memory", None) and getattr(organism, "personality", None):
            cautela = organism.personality.cautela
            if cautela > 0.35 and organism.memory.danger_zones:
                for zx, zy, _ in organism.memory.danger_zones:
                    dz_dist = math.hypot(organism.x - zx, organism.y - zy)
                    if 0.1 < dz_dist < 55.0:
                        repel_mag = (1.0 - (dz_dist / 55.0)) * cautela * 0.35
                        danger_fx += ((organism.x - zx) / dz_dist) * repel_mag
                        danger_fy += ((organism.y - zy) / dz_dist) * repel_mag

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
        """Calcula aceleração de vagueio suave com coerência angular no tempo."""
        # Perturbação estocástica suave do ângulo
        delta_angle = prng.uniform(-0.35, 0.35)
        organism.wander_angle += delta_angle

        # Parâmetros do círculo imaginário à frente
        circle_dist = 35.0
        circle_radius = 20.0

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
