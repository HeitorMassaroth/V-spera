"""Sistema de cinemática e steering behaviors para organismos autônomos."""

from __future__ import annotations
import math
from typing import Tuple, Optional
from ..entities.organism import Organism
from ..entities.food import Food
from ..prng import PRNG


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
        if target_food is not None:
            steer_x, steer_y = self._seek(organism, target_food.x, target_food.y)
        else:
            steer_x, steer_y = self._wander(organism, prng)

        # Adiciona força de repulsão das paredes
        wall_x, wall_y = self._boundary_repulsion(organism)

        total_fx = steer_x + wall_x
        total_fy = steer_y + wall_y
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
