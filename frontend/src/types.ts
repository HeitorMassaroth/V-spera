/**
 * Tipos e interfaces TypeScript para o VÉSPERA.
 * Simulação de Vida Artificial, Hereditariedade, Genética e Dinâmica Familiar Avançada.
 */

export interface CompactOrganism {
  id: number;
  nm: string;  // Nome gerado
  sp?: 'V' | 'P'; // Raça: 'V' (Vranco), 'P' (Predador)
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
  alpha_approval_rating?: number;
  has_legitimacy_crisis?: boolean;
  crisis_ticks?: number;
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
  vrancos_count?: number;
  predators_count?: number;
  vranco_avg_group_size?: number;
  vrancos_periphery_pct?: number;
  predators_periphery_pct?: number;
  flee_count?: number;
  combat_count?: number;
  collective_defenses_count?: number;
  predation_attempts?: number;
  predation_kills?: number;
  predators_defeated?: number;
  hunting_success_rate?: number;
  families_count?: number;
  family_homes_count?: number;
  bonded_pairs_count?: number;
  nests_count?: number;
  clans_count?: number;
  established_clans_count?: number;
  total_communal_food?: number;
  wars_count?: number;
  settled_territories_count?: number;
  contested_territories_count?: number;
  degraded_territories_count?: number;
  avg_territory_quality?: number;
  stage_stats?: StageStats;
  max_generation?: number;
  total_mutations?: number;
  attr_stats?: AttributeStats;
  season?: SeasonInfo;
  ecology?: EcologyMetrics;
  evolution?: EvolutionMetrics;
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
    | 'predator_defeated'
    | 'vranco_collective_defense'
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
    | 'communal_aid'
    | 'season_changed';
  macho_name?: string;
  target_name?: string;
  damage?: number;
  participants_count?: number;
  collective_power?: number;
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
  season?: string;
  season_name?: string;
  icon?: string;
  year?: number;
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

export interface TerritoryEventLog {
  type: string;
  description: string;
  tick: number;
}

export interface TerritoryZoneInfo {
  id: number;
  name: string;
  x: number;
  y: number;
  radius: number;
  is_peripheral: boolean;
  food_count: number;
  biomass: number;
  base_fertility: number;
  current_fertility: number;
  depletion_ticks: number;
  recovery_ticks: number;
  predator_count: number;
  vranco_count: number;
  shelter_count: number;
  carrying_capacity: number;
  occupants_count: number;
  occupant_ids?: number[];
  food_availability_score: number;
  safety_score: number;
  population_density: number;
  competition_pressure: number;
  quality_score: number;
  controller_type: 'NONE' | 'FAMILY' | 'CLAN';
  controlling_clan_id: number | null;
  controlling_family_id: number | null;
  status: 'UNCLAIMED' | 'SETTLED' | 'CONTESTED' | 'DEGRADED' | 'ABANDONED';
  dispute_ticks: number;
  abandoned_cooldown: number;
  history_log: TerritoryEventLog[];
}

export interface SeasonInfo {
  tick: number;
  year: number;
  season: 'SPRING' | 'SUMMER' | 'AUTUMN' | 'WINTER';
  season_name: string;
  season_icon: string;
  season_desc: string;
  season_tick: number;
  season_duration: number;
  season_progress: number;
  temperature: number;
  food_spawn_multiplier: number;
  metabolic_cost_multiplier: number;
  reproduction_cost_multiplier: number;
  movement_cost_multiplier: number;
  environmental_stress: number;
  births_this_season: number;
  deaths_this_season: number;
  vrancos_births_season: number;
  vrancos_deaths_season: number;
  predators_births_season: number;
  predators_deaths_season: number;
  food_consumed_season: number;
  food_spawned_season: number;
  season_history?: Array<{
    year: number;
    season: string;
    season_name: string;
    births: number;
    deaths: number;
    vrancos_births: number;
    vrancos_deaths: number;
    predators_births: number;
    predators_deaths: number;
    food_consumed: number;
    food_spawned: number;
  }>;
}

export interface EcologyMetrics {
  total_biomass: number;
  food_biomass: number;
  animal_biomass: number;
  carrying_capacity: number;
  carrying_capacity_ratio: number;
  is_overpopulated: boolean;
  consumption_rate: number;
  regeneration_rate: number;
  biomass_balance: number;
  critical_regions_count: number;
  predator_prey_ratio: number;
  seasonal_growth_rate: number;
  vrancos_count: number;
  predators_count: number;
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
  territories?: TerritoryZoneInfo[];
  season?: SeasonInfo;
  ecology?: EcologyMetrics;
  metrics: WorldMetrics;
  events?: WorldEvent[];
  chronicle?: ChronicleEvent[];
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  tps: number;
}

export interface SimulationConfig {
  seed: number | null;
  width: number;
  height: number;
  initial_organisms?: number | null;
  initial_predator_females?: number | null;
  initial_predator_males?: number | null;
  initial_vranco_females?: number | null;
  initial_vranco_males?: number | null;
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
  coragem?: number;
  agressividade: number;
  sociabilidade: number;
  curiosidade: number;
  cautela: number;
  protecao?: number;
  instinto_protecao?: number;
  persistencia?: number;
  eficiencia_coleta?: number;
  exploracao?: number;
  fertilidade?: number;
}

export interface EpisodicMemory {
  event_type: string;
  description: string;
  tick: number;
  x: number;
  y: number;
  intensity: number;
  relevance: number;
  involved_id?: number | null;
  involved_name?: string | null;
}

export interface AnimalMemory {
  episodes?: EpisodicMemory[];
  max_episodes?: number;
  known_food_sources: [number, number, number][];
  danger_zones: [number, number, number][];
  lost_relatives: { name: string; tick: number; cause: string }[];
  safe_haven?: [number, number] | null;
}

export interface TacticalSkillsInfo {
  foraging_efficiency: number;
  hunting_proficiency: number;
  evasion_proficiency: number;
  mobbing_coordination: number;
  experience: number;
}

export interface FoodHotspotInfo {
  x: number;
  y: number;
  discovery_tick: number;
  last_harvest_tick: number;
  harvest_count: number;
  reliability: number;
  is_active: boolean;
}

export interface DangerHotspotInfo {
  x: number;
  y: number;
  source: string;
  first_seen_tick: number;
  last_seen_tick: number;
  threat_level: number;
  encounter_count: number;
  is_active: boolean;
}

export interface ThreatProfileInfo {
  target_id: number;
  target_name: string;
  threat_score: number;
  encounters: number;
  last_tick: number;
}

export interface AnimalKnowledgeInfo {
  experience_points: number;
  tactical_skills: TacticalSkillsInfo;
  food_hotspots: FoodHotspotInfo[];
  danger_hotspots: DangerHotspotInfo[];
  known_threats: ThreatProfileInfo[];
}

export interface AnimalRecord {
  id: number;
  name: string;
  species?: string;
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

export interface AllelePairInfo {
  maternal: number;
  paternal: number;
  value: number;
  heterozygosity: number;
}

export interface GenotypeInfo {
  pairs: Record<string, AllelePairInfo>;
  inbreeding_coefficient: number;
  lineage_id: string | number;
  lineage_name: string;
  average_heterozygosity: number;
}

export interface PhenotypeInfo {
  forca: number;
  velocidade: number;
  resistencia: number;
  eficiencia_metabolica: number;
  eficiencia_coleta: number;
  deteccao_ameacas: number;
  resistencia_doencas: number;
  fertilidade: number;
  longevidade_potencial: number;
  adaptabilidade: number;
  sociabilidade: number;
  agressividade: number;
  cautela: number;
  instinto_protecao: number;
  max_saude: number;
  ontogeny_factor: number;
  health_factor: number;
  inbreeding_penalty: number;
}

export interface EvolutionMetrics {
  active_population_count: number;
  total_records: number;
  genetic_diversity: {
    average_heterozygosity: number;
    average_inbreeding_coefficient: number;
    effective_population_size: number;
    unique_lineages: number;
  };
  generations: Record<string, {
    generation: number;
    total_born: number;
    alive: number;
    avg_forca: number;
    avg_velocidade: number;
    avg_resistencia: number;
    avg_coleta: number;
    avg_deteccao: number;
    avg_inbreeding: number;
  }>;
  lineages: Array<{
    id: string | number;
    name: string;
    active_members: number;
    avg_generation: number;
    avg_heterozygosity: number;
  }>;
  mortality_by_cause: Record<string, number>;
  trait_survival_correlation: {
    surviving_adults_avg_forca?: number;
    deceased_avg_forca?: number;
    surviving_adults_avg_velocidade?: number;
    deceased_avg_velocidade?: number;
  };
  clan_differences: Array<{
    clan_id: number;
    clan_name: string;
    member_count: number;
    avg_forca: number;
    avg_velocidade: number;
    avg_sociabilidade: number;
    avg_inbreeding: number;
  }>;
}

export interface OrganismDetailResponse {
  family_tree: FamilyTreeData;
  is_alive: boolean;
  current_stats?: {
    species?: string;
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
    knowledge?: AnimalKnowledgeInfo;
    nest?: NestInfo | null;
    cause_of_death?: string | null;
    clan_id?: number | null;
    clan_role?: string | null;
    territory_id?: number | null;
    leadership_score?: number;
    genotype?: GenotypeInfo | Record<string, any>;
    phenotype?: PhenotypeInfo | Record<string, any>;
    current_state_info?: Record<string, any>;
    inbreeding_coefficient?: number;
    lineage_id?: string | number;
    lineage_name?: string;
    relationships?: SocialRelationshipInfo[];
  } | null;
  population_averages?: AttributeStats;
  evolution?: EvolutionMetrics;
  chronicle?: ChronicleEvent[];
}

export interface SocialRelationshipInfo {
  target_id: number;
  target_name: string;
  target_species: string;
  trust: number;
  affinity: number;
  fear: number;
  rivalry: number;
  hostility: number;
  cooperation_count: number;
  last_interaction_tick: number;
  status_label: string;
}

export interface ChronicleEvent {
  id: number;
  tick: number;
  year: number;
  event_type: string;
  title: string;
  description: string;
  cause: string;
  result: string;
  importance: number;
  location?: [number, number] | null;
  zone_id?: number | null;
  zone_name?: string | null;
  primary_organism_id?: number | null;
  primary_organism_name?: string | null;
  secondary_organism_id?: number | null;
  secondary_organism_name?: string | null;
  involved_organism_ids?: number[];
  clan_id?: number | null;
  clan_name?: string | null;
  secondary_clan_id?: number | null;
  secondary_clan_name?: string | null;
  species?: string | null;
  related_event_ids?: number[];
  metadata?: Record<string, any>;
}

export interface ChronicleTimelineResponse {
  total: number;
  limit: number;
  offset: number;
  events: ChronicleEvent[];
}

export interface ChronicleEventDetailResponse {
  event: ChronicleEvent;
  related_events: ChronicleEvent[];
}

