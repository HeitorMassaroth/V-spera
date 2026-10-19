/**
 * Tipos e interfaces TypeScript para o VÉSPERA.
 * Simulação de Vida Artificial, Hereditariedade, Genética e Dinâmica Familiar Avançada.
 */

export interface CompactOrganism {
  id: number;
  nm: string;  // Nome gerado
  x: number;
  y: number;
  vx: number;
  vy: number;
  e: number;   // Energia [0 - 100]
  s: number;   // Saúde atual [0 - ms]
  ms?: number; // Saúde máxima suportada
  a?: number;  // Idade em ticks
  sz: number;  // Tamanho/Raio físico
  h: number;   // Hue de cor HSL
  r?: string;  // Papel: 'F' (Rosa/Fêmea), 'M' (Verde/Macho), 'C' (Roxo/Filhote)
  sx?: string; // Sexo: 'F' ou 'M'
  st?: string; // Estágio: 'N' (Recém-nascido), 'D' (Desenvolvimento), 'J' (Jovem), 'I' (Independente), 'A' (Adulto)
  act?: string;// Ação/Estado atual
  fam?: number | null; // ID da família a que pertence
  prt?: number | null; // ID do parceiro vitalício exclusivo
  cf?: number; // Biomassa de alimento sendo transportada para o ninho
  cln?: number | null; // ID do Clã a que pertence
  clr?: string | null; // Papel no clã: 'A' (Alpha), 'B' (Beta), 'M' (Membro)
  gen?: number;// Geração do indivíduo
  f?: number;  // Força genética
  v?: number;  // Velocidade genética
  res?: number;// Resistência genética
  i?: number;  // Inteligência genética
}

export type CompactFood = [id: number, x: number, y: number];

export interface NestInfo {
  id: number;
  family_id: number;
  x: number;
  y: number;
  materials: number;
  food_storage: number;
  level: number;
  created_tick: number;
  is_active: boolean;
}

export interface ClanPriority {
  type?: string;
  priority_type?: string;
  title?: string;
  urgency?: number;
  priority_level?: number;
  description: string;
  target_cluster_id?: number | null;
  target_clan_id?: number | null;
  created_tick?: number;
  is_active?: boolean;
}

export interface ClanInfo {
  id: number;
  name: string;
  stage: 'INDEPENDENT' | 'OCCASIONAL_COOP' | 'RECURRENT_COOP' | 'ESTABLISHED_CLAN';
  family_ids: number[];
  families_count: number;
  member_organism_ids?: number[];
  alpha_id: number | null;
  beta_id: number | null;
  alpha_score: number;
  beta_score: number;
  communal_food: number;
  total_food_contributed: number;
  total_food_consumed: number;
  territory: {
    x: number;
    y: number;
    radius: number;
  };
  territory_center?: [number, number];
  territory_radius?: number;
  priorities: ClanPriority[];
  active_objectives: Array<{
    id: string;
    type: string;
    assigned_count?: number;
    assigned_members?: number[];
    progress: number;
    is_completed: boolean;
    is_failed: boolean;
  }>;
  diplomacy: Record<string, 'NEUTRAL' | 'COOPERATION' | 'ALLIANCE' | 'COMPETITION' | 'HOSTILE' | 'WAR' | 'TRUCE'>;
  relations?: Record<string, string>;
  history_log: Array<
    | {
        type?: string;
        desc?: string;
        tick?: number;
      }
    | string
  >;
  founded_tick: number;
  is_active: boolean;
}

export interface AttributeStat {
  avg: number;
  min: number;
  max: number;
}

export interface AttributeStats {
  forca: AttributeStat;
  velocidade: AttributeStat;
  resistencia: AttributeStat;
  inteligencia: AttributeStat;
  saude: AttributeStat;
}

export interface StageStats {
  newborn: number;
  developing: number;
  juvenile: number;
  independent: number;
  adult: number;
}

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
  females_count?: number;
  males_count?: number;
  children_count?: number;
  families_count?: number;
  family_homes_count?: number;
  bonded_pairs_count?: number;
  nests_count?: number;
  clans_count?: number;
  established_clans_count?: number;
  total_communal_food?: number;
  wars_count?: number;
  stage_stats?: StageStats;
  max_generation?: number;
  total_mutations?: number;
  attr_stats?: AttributeStats;
}

export interface WorldEvent {
  type:
    | 'combat'
    | 'flee'
    | 'care'
    | 'birth'
    | 'family_founded'
    | 'maturation'
    | 'pair_bonded'
    | 'nest_created'
    | 'partner_lost'
    | 'predation_attempt'
    | 'predation_kill'
    | 'mother_defense'
    | 'orphan_adopted'
    | 'patriarch_joined'
    | 'matriarch_joined'
    | 'clan_extinct'
    | 'clan_formed'
    | 'clan_stage_changed'
    | 'alpha_elected'
    | 'beta_elected'
    | 'alpha_succession'
    | 'clan_priority_changed'
    | 'family_expelled'
    | 'clan_war_declared'
    | 'clan_truce_agreed'
    | 'clan_expanded'
    | 'communal_aid';
  macho_name?: string;
  target_name?: string;
  damage?: number;
  parent_name?: string;
  child_name?: string;
  organism_name?: string;
  clan_name?: string;
  female_name?: string;
  male_name?: string;
  family_id?: number;
  nest_id?: number;
  survivor_name?: string;
  lost_partner?: string;
  predator_name?: string;
  mother_name?: string;
  pup_name?: string;
  role?: string;
  name?: string;
  gen?: number;
  x?: number;
  y?: number;
  leader_id?: number;
  leader_name?: string;
  beta_id?: number;
  beta_name?: string;
  score?: number;
  stage?: string;
  priority?: string;
  urgency?: number;
  clan1_name?: string;
  clan2_name?: string;
  reason?: string;
  message?: string;
  tick: number;
}

export const CLAN_NAMES = [
  'Clã Solaris', 'Clã Apex', 'Clã Ignis', 'Clã Sylva', 'Clã Terra',
  'Clã Umbra', 'Clã Astra', 'Clã Zephyr', 'Clã Boreas', 'Clã Titan',
  'Clã Vulcan', 'Clã Orion', 'Clã Chronos', 'Clã Fenrir', 'Clã Chimera'
];

export function getClanName(familyId: number | null | undefined): string {
  if (!familyId) return 'Nômade';
  return CLAN_NAMES[(familyId - 1) % CLAN_NAMES.length];
}

export interface FamilyInfo {
  id: number;
  clan_name: string;
  home_cluster_id?: number | null;
  patriarch_id?: number | null;
  matriarch_id?: number | null;
  nest_id?: number | null;
  children_count: number;
  founded_tick: number;
  is_active: boolean;
}

export interface SimulationStateMessage {
  t: number;
  orgs: CompactOrganism[];
  foods: CompactFood[];
  clusters?: [number, number][];
  cluster_homes?: Record<number, number>; // cluster_idx -> family_id
  families?: FamilyInfo[];
  nests?: NestInfo[];
  clans?: ClanInfo[];
  metrics: WorldMetrics;
  events?: WorldEvent[];
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

export interface MutationRecord {
  attribute: string;
  category: 'PEQUENA' | 'SIGNIFICATIVA' | 'EXCEPCIONAL';
  direction?: 'POSITIVA' | 'NEGATIVA';
  delta: number;
  expected_value?: number;
  resulting_value?: number;
  intensity_pct?: number;
}

export interface GeneticHistoryItem {
  attribute: string;
  father_val?: number;
  mother_val?: number;
  parents_avg?: number;
  expected_val?: number;
  final_val?: number;
  deviation_from_parents?: number;
  had_mutation?: boolean;
}

export interface AnimalPersonality {
  agressividade: number;
  sociabilidade: number;
  cautela: number;
  curiosidade: number;
  instinto_protecao: number;
  eficiencia_coleta: number;
  exploracao: number;
  fertilidade: number;
}

export interface AnimalMemory {
  known_food_sources: [number, number, number][];
  danger_zones: [number, number, number][];
  lost_relatives: { name: string; tick: number; cause: string }[];
  safe_haven?: [number, number] | null;
}

export interface AnimalRecord {
  id: number;
  name: string;
  role: string;
  sex?: string;
  life_stage?: string;
  generation: number;
  birth_tick: number;
  death_tick?: number | null;
  cause_of_death?: string | null;
  father_id?: number | null;
  mother_id?: number | null;
  partner_id?: number | null;
  partner_bond_duration?: number;
  children_ids: number[];
  family_id?: number | null;
  genome: {
    forca: number;
    velocidade: number;
    resistencia: number;
    inteligencia: number;
    max_saude: number;
  };
  personality?: AnimalPersonality;
  mutations: MutationRecord[];
  genetic_history: GeneticHistoryItem[];
}

export interface FamilyTreeData {
  animal: AnimalRecord;
  partner?: AnimalRecord | null;
  father?: AnimalRecord | null;
  mother?: AnimalRecord | null;
  grandparents: {
    paternal_grandfather?: AnimalRecord | null;
    paternal_grandmother?: AnimalRecord | null;
    maternal_grandfather?: AnimalRecord | null;
    maternal_grandmother?: AnimalRecord | null;
  };
  children: AnimalRecord[];
}

export interface OrganismDetailResponse {
  family_tree: FamilyTreeData;
  is_alive: boolean;
  current_stats?: {
    age: number;
    saude: number;
    energy: number;
    hunger?: number;
    x: number;
    y: number;
    role: string;
    sex?: string;
    life_stage?: string;
    life_expectancy?: number;
    current_state?: string;
    carried_food?: number;
    partner_id?: number | null;
    partner_bond_duration?: number;
    mourning_ticks?: number;
    personality?: AnimalPersonality;
    memory?: AnimalMemory;
    nest?: NestInfo | null;
    cause_of_death?: string | null;
    clan_id?: number | null;
    clan_role?: string | null;
    leadership_score?: number;
  } | null;
  population_averages?: AttributeStats;
}
