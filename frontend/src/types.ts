/**
 * Tipos e interfaces TypeScript para o VÉSPERA.
 */

export interface CompactOrganism {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  e: number;   // Energia
  sz: number;  // Tamanho/Raio físico
  h: number;   // Hue de cor HSL
}

export type CompactFood = [id: number, x: number, y: number];

export interface WorldMetrics {
  tick: number;
  population: number;
  food_count: number;
  avg_energy: number;
  avg_speed: number;
  avg_age: number;
  max_age: number;
  total_births: number;
  total_deaths: number;
  total_food_consumed: number;
  is_extinct: boolean;
}

export interface SimulationStateMessage {
  t: number;
  orgs: CompactOrganism[];
  foods: CompactFood[];
  clusters?: [number, number][];
  metrics: WorldMetrics;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  tps: number;
}

export interface SimulationConfig {
  seed: number | null;
  width: number;
  height: number;
  initial_organisms: number;
  initial_food: number;
  food_spawn_rate: number;
  max_food: number;
}
