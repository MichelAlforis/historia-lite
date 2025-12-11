// Historia Lite - TypeScript Types

export interface Personality {
  aggression: number;
  expansionism: number;
  diplomacy: number;
  risk_tolerance: number;
}

export interface Country {
  id: string;
  name: string;
  name_fr: string;
  tier: number;

  population: number;
  economy: number;
  military: number;
  nuclear: number;
  technology: number;
  stability: number;
  soft_power: number;
  resources: number;

  personality: Personality;
  regime: string;
  blocs: string[];
  relations: Record<string, number>;
  sanctions_on: string[];
  at_war: string[];
  allies: string[];
  rivals: string[];
  sphere_of_influence: string[];
  under_influence_of: Record<string, number>;
  is_player: boolean;
  power_score: number;
}

export interface InfluenceZone {
  id: string;
  name: string;
  name_fr: string;
  dominant_power: string | null;
  contested_by: string[];
  countries_in_zone: string[];
  influence_type: string;
  strength: number;
  influence_levels: Record<string, number>;
  // Advanced influence fields
  influence_breakdown: Record<string, InfluenceBreakdown>;
  dominant_religion: string | null;
  dominant_culture: string | null;
  dominant_language: string | null;
  has_oil: boolean;
  has_strategic_resources: boolean;
  former_colonial_power: string | null;
}

// Influence breakdown by type
export interface InfluenceBreakdown {
  military: number;
  economic: number;
  monetary: number;
  cultural: number;
  religious: number;
  petro: number;
  colonial: number;
  diplomatic: number;
}

// Military base
export interface MilitaryBase {
  id: string;
  name: string;
  name_fr: string;
  owner: string;
  host_country: string;
  zone: string;
  type: string;
  personnel: number;
  strategic_value: number;
}

// Influence rankings
export interface InfluenceRanking {
  rank: number;
  power_id: string;
  name: string;
  name_fr: string;
  tier: number;
  total_influence: number;
  zones_dominated: number;
  zones_contested: number;
}

// Power global influence
export interface PowerGlobalInfluence {
  country_id: string;
  country_name: string;
  country_name_fr: string;
  tier: number;
  total_influence: number;
  average_influence: number;
  zones_dominated: number;
  zones_contested: number;
  military_bases: number;
  total_personnel_abroad: number;
  zone_details: Record<string, ZoneInfluenceDetail>;
  global_breakdown?: InfluenceBreakdown;
  top_zones?: Array<{
    zone_id: string;
    zone_name_fr: string;
    influence: number;
    is_dominant: boolean;
  }>;
}

export interface ZoneInfluenceDetail {
  name: string;
  name_fr: string;
  total: number;
  breakdown: InfluenceBreakdown;
  is_dominant: boolean;
  is_contesting: boolean;
}

export interface GameEvent {
  id: string;
  year: number;
  type: string;
  title: string;
  title_fr: string;
  description: string;
  description_fr: string;
  country_id: string | null;
  target_id: string | null;
}

export interface Conflict {
  id: string;
  type: string;
  attackers: string[];
  defenders: string[];
  region: string | null;
  intensity: number;
  duration: number;
  nuclear_risk: number;
}

export interface WorldState {
  year: number;
  seed: number;
  oil_price: number;
  global_tension: number;

  countries: Country[];
  influence_zones: InfluenceZone[];
  active_conflicts: Conflict[];
  recent_events: GameEvent[];

  total_countries: number;
  nuclear_powers: number;
  active_wars: number;

  // Tier counts
  tier4_count: number;
  tier4_in_crisis: number;
  tier5_count: number;
  tier5_in_crisis: number;
  tier6_count: number;

  // Game state (victory/defeat system)
  defcon_level: number;
  game_ended: boolean;
  game_end_reason: string | null;
  game_end_message: string;
  game_end_message_fr: string;
  final_score: number;
}

// Tier 4 Country (simplified model)
export interface Tier4Country {
  id: string;
  name: string;
  name_fr: string;
  flag: string;
  tier: 4;
  region: string;

  // Simplified stats
  economy: number;
  stability: number;
  population: number;
  military: number;

  // Alignment (-100 to +100)
  alignment: number;
  alignment_target: string;
  alignment_label: string;

  // Resources
  strategic_resource: string | null;

  // Relations with major powers
  relations: Record<string, number>;

  // Status
  in_crisis: boolean;
  crisis_type: string | null;
  under_influence_of: string | null;

  power_score: number;
}

export interface Tier4Summary {
  total: number;
  by_region: Record<string, number>;
  by_alignment: Record<string, number>;
  in_crisis: number;
  pro_west: number;
  pro_east: number;
  neutral: number;
}

// Tier 5 Country (small nations - minimal stats)
export interface Tier5Country {
  id: string;
  name: string;
  name_fr: string;
  flag: string;
  tier: 5;
  region: string;

  // Minimal stats (no military)
  economy: number;
  stability: number;
  population: number;
  alignment: number;
  alignment_label: string;

  // Protection and influence
  protector: string | null;
  influence_zone: string | null;

  // Status
  in_crisis: boolean;
  crisis_type: string | null;

  // Neighbors
  neighbors: string[];

  power_score: number;
}

export interface Tier5Summary {
  total: number;
  by_region: Record<string, number>;
  by_alignment: Record<string, number>;
  by_protector: Record<string, number>;
  in_crisis: number;
  pro_west: number;
  pro_east: number;
  neutral: number;
}

// Tier 6 Country (micro-nations - ultra-minimal)
export interface Tier6Country {
  id: string;
  name: string;
  name_fr: string;
  flag: string;
  tier: 6;
  region: string;

  // Ultra-minimal stats
  economy: number;
  stability: number;
  population: number;  // Always small (0-10)

  // Protection (required)
  protector: string;
  influence_zone: string;

  // Special status
  is_territory: boolean;
  special_status: string | null;

  power_score: number;
}

export interface Tier6Summary {
  total: number;
  by_region: Record<string, number>;
  by_protector: Record<string, number>;
  by_special_status: Record<string, number>;
  territories: number;
  sovereign: number;
}

export interface TickResponse {
  year: number;
  events: GameEvent[];
  summary: string;
  summary_fr: string;

  // Game end state (if game ended this tick)
  game_ended: boolean;
  game_end_reason: string | null;
  game_end_message: string;
  game_end_message_fr: string;
  is_victory: boolean;
  final_score: number;
  defcon_level: number;
}

// Regime display names
export const REGIME_NAMES: Record<string, string> = {
  democracy: 'Democratie liberale',
  single_party: 'Parti unique',
  autocracy: 'Autocratie',
  constitutional_monarchy: 'Monarchie constitutionnelle',
  absolute_monarchy: 'Monarchie absolue',
  illiberal_democracy: 'Democratie illiberale',
  hybrid: 'Regime hybride',
  theocracy: 'Theocratie',
};

// Tier display names
export const TIER_NAMES: Record<number, string> = {
  1: 'Superpuissance',
  2: 'Puissance majeure',
  3: 'Puissance regionale',
  4: 'Nation active',
  5: 'Petit pays',
  6: 'Micro-nation',
};

// Region display names
export const REGION_NAMES: Record<string, string> = {
  africa: 'Afrique',
  asia: 'Asie',
  middle_east: 'Moyen-Orient',
  latam: 'Amerique latine',
  europe: 'Europe',
  oceania: 'Oceanie',
  caribbean: 'Caraibes',
  pacific: 'Pacifique',
  indian_ocean: 'Ocean Indien',
};

// Alignment labels
export const ALIGNMENT_NAMES: Record<string, string> = {
  pro_west: 'Pro-Occident',
  west_leaning: 'Tendance Ouest',
  neutral: 'Neutre',
  east_leaning: 'Tendance Est',
  pro_east: 'Pro-Est',
};

// Alignment colors
export const ALIGNMENT_COLORS: Record<string, string> = {
  pro_west: 'bg-blue-500',
  west_leaning: 'bg-blue-300',
  neutral: 'bg-gray-400',
  east_leaning: 'bg-red-300',
  pro_east: 'bg-red-500',
};

// Event type colors
export const EVENT_COLORS: Record<string, string> = {
  crisis: 'bg-red-500',
  positive: 'bg-green-500',
  decision: 'bg-blue-500',
  ai_decision: 'bg-cyan-500',
  sanctions: 'bg-orange-500',
  diplomacy: 'bg-purple-500',
  military: 'bg-gray-600',
  peace: 'bg-emerald-500',
  tier4_development: 'bg-teal-500',
  tier4_alignment: 'bg-violet-500',
  tier4_crisis: 'bg-amber-600',
  tier5_crisis: 'bg-orange-500',
};

// Tier 6 special status display names
export const SPECIAL_STATUS_NAMES: Record<string, string> = {
  tax_haven: 'Paradis fiscal',
  tourism: 'Tourisme',
  strategic_base: 'Base strategique',
};

// AI Settings
export interface GameSettings {
  ai_mode: 'algorithmic' | 'ollama';
  ollama_url: string;
  ollama_model: string;
  ollama_tiers: number[];
  ollama_available: boolean;
}

export interface OllamaStatus {
  connected: boolean;
  url: string;
  current_model: string;
  available_models: string[];
}

// =============================================================================
// COMMAND SYSTEM
// =============================================================================

export interface CommandInterpretation {
  category: string;
  action: string;
  target_country_id: string | null;
  target_project_id: string | null;
  parameters: Record<string, unknown>;
  confidence: number;
}

export interface CommandCost {
  economy: number;
  military: number;
  stability: number;
  soft_power: number;
  technology: number;
}

export interface CommandResponse {
  command_id: string;
  original_command: string;
  interpreted_as: string;
  interpretation: CommandInterpretation;
  feasible: boolean;
  feasibility_reason: string | null;
  cost: CommandCost;
  requires_confirmation: boolean;
  confirmation_message: string;
  confirmation_message_fr: string;
  executed: boolean;
  events: GameEvent[];
}

// =============================================================================
// PROJECT SYSTEM
// =============================================================================

export type ProjectType = 'space' | 'nuclear' | 'military' | 'economic' | 'infrastructure' | 'technology' | 'social';

export interface ProjectMilestone {
  at_progress: number;
  event_type: string;
  title: string;
  title_fr: string;
  description: string;
  description_fr: string;
}

export interface ProjectTemplate {
  id: string;
  name: string;
  name_fr: string;
  type: ProjectType;
  total_years: number;
  economy_cost_per_year: number;
  technology_required: number;
  completion_effects: Record<string, number>;
  milestones: ProjectMilestone[];
  description: string;
  description_fr: string;
}

export interface ActiveProject {
  id: string;
  template_id: string;
  name: string;
  name_fr: string;
  type: ProjectType;
  country_id: string;
  progress: number;
  years_active: number;
  total_years: number;
  economy_cost_per_year: number;
  total_invested: number;
  status: string;
  sabotaged: boolean;
  accelerated: boolean;
  milestones_reached: number[];
  completion_effects: Record<string, number>;
}

export interface ProjectListResponse {
  country_id: string;
  active_projects: ActiveProject[];
  available_projects: ProjectTemplate[];
}

export interface ProjectResponse {
  project: ActiveProject;
  next_milestone: ProjectMilestone | null;
  years_remaining: number;
  completion_year: number;
}

// =============================================================================
// DILEMMA SYSTEM
// =============================================================================

export type DilemmaType =
  | 'economic_crisis'
  | 'budget_shortage'
  | 'war_declaration'
  | 'ally_attacked'
  | 'nuclear_threat'
  | 'revolution_risk'
  | 'coup_attempt'
  | 'ultimatum_received'
  | 'alliance_request'
  | 'sanctions_imposed'
  | 'project_milestone'
  | 'project_sabotage';

export interface DilemmaChoice {
  id: number;
  label: string;
  label_fr: string;
  description: string;
  description_fr: string;
  effects: Record<string, number>;
  relation_effects: Record<string, number>;
  triggers_event: string | null;
  starts_project: string | null;
  ends_war: boolean;
  declares_war: string | null;
}

export interface ActiveDilemma {
  id: string;
  template_id: string;
  type: DilemmaType;
  title: string;
  title_fr: string;
  description: string;
  description_fr: string;
  country_id: string;
  year_triggered: number;
  trigger_data: Record<string, unknown>;
  related_country_id: string | null;
  related_project_id: string | null;
  choices: DilemmaChoice[];
  expires_at_year: number | null;
  auto_choice: number | null;
  status: string;
  chosen_option: number | null;
}

export interface DilemmaResolveResponse {
  dilemma_id: string;
  choice_made: DilemmaChoice;
  effects_applied: Record<string, number>;
  relation_changes: Record<string, number>;
  events_triggered: Record<string, unknown>[];
  message: string;
  message_fr: string;
}

export interface PendingDilemmasResponse {
  country_id: string;
  pending_dilemmas: ActiveDilemma[];
  count: number;
}

// Dilemma type colors
export const DILEMMA_COLORS: Record<DilemmaType, string> = {
  economic_crisis: 'bg-yellow-500',
  budget_shortage: 'bg-orange-400',
  war_declaration: 'bg-red-600',
  ally_attacked: 'bg-red-500',
  nuclear_threat: 'bg-purple-600',
  revolution_risk: 'bg-amber-500',
  coup_attempt: 'bg-gray-700',
  ultimatum_received: 'bg-red-400',
  alliance_request: 'bg-blue-400',
  sanctions_imposed: 'bg-orange-500',
  project_milestone: 'bg-teal-500',
  project_sabotage: 'bg-pink-500',
};

// Project type colors
export const PROJECT_COLORS: Record<ProjectType, string> = {
  space: 'bg-indigo-500',
  nuclear: 'bg-yellow-500',
  military: 'bg-gray-600',
  economic: 'bg-green-500',
  infrastructure: 'bg-orange-400',
  technology: 'bg-cyan-500',
  social: 'bg-pink-400',
};

// =============================================================================
// INFLUENCE SYSTEM
// =============================================================================

// Influence type colors (Tailwind classes)
export const INFLUENCE_TYPE_COLORS: Record<string, string> = {
  military: 'bg-red-500',
  economic: 'bg-green-500',
  monetary: 'bg-yellow-500',
  cultural: 'bg-purple-500',
  religious: 'bg-orange-500',
  petro: 'bg-gray-800',
  colonial: 'bg-gray-500',
  diplomatic: 'bg-blue-500',
};

// Influence type colors (hex for charts)
export const INFLUENCE_TYPE_HEX: Record<string, string> = {
  military: '#ef4444',
  economic: '#22c55e',
  monetary: '#eab308',
  cultural: '#8b5cf6',
  religious: '#f97316',
  petro: '#171717',
  colonial: '#6b7280',
  diplomatic: '#3b82f6',
};

// Influence type names (French)
export const INFLUENCE_TYPE_NAMES: Record<string, string> = {
  military: 'Militaire',
  economic: 'Economique',
  monetary: 'Monetaire',
  cultural: 'Culturel',
  religious: 'Religieux',
  petro: 'Petrolier',
  colonial: 'Colonial',
  diplomatic: 'Diplomatique',
};

// Religion names (French)
export const RELIGION_NAMES: Record<string, string> = {
  christian_catholic: 'Catholique',
  christian_protestant: 'Protestant',
  christian_orthodox: 'Orthodoxe',
  muslim_sunni: 'Sunnite',
  muslim_shia: 'Chiite',
  buddhist: 'Bouddhiste',
  hindu: 'Hindou',
  jewish: 'Juif',
  confucian: 'Confuceen',
  shinto: 'Shinto',
  secular: 'Laique',
  animist: 'Animiste',
};

// Culture names (French)
export const CULTURE_NAMES: Record<string, string> = {
  anglo: 'Anglo-saxonne',
  franco: 'Francophone',
  hispano: 'Hispanique',
  lusophone: 'Lusophone',
  germanic: 'Germanique',
  slav_east: 'Slave orientale',
  slav_west: 'Slave occidentale',
  slav_south: 'Slave meridionale',
  arab: 'Arabe',
  persian: 'Persane',
  turkic: 'Turque',
  sino: 'Sinosphere',
  japanese: 'Japonaise',
  korean: 'Coreenne',
  indian: 'Indienne',
  southeast_asian: 'Asie du Sud-Est',
  african_west: 'Ouest-africaine',
  african_east: 'Est-africaine',
  african_south: 'Afrique australe',
  latin: 'Latine',
};

// Language names (French)
export const LANGUAGE_NAMES: Record<string, string> = {
  english: 'Anglais',
  french: 'Francais',
  spanish: 'Espagnol',
  portuguese: 'Portugais',
  german: 'Allemand',
  russian: 'Russe',
  arabic: 'Arabe',
  mandarin: 'Mandarin',
  hindi: 'Hindi',
  japanese: 'Japonais',
  korean: 'Coreen',
  turkish: 'Turc',
  farsi: 'Farsi',
  swahili: 'Swahili',
  indonesian: 'Indonesien',
  polish: 'Polonais',
  serbian: 'Serbe',
  swedish: 'Suedois',
};

// Influence zone type names
export const ZONE_TYPE_NAMES: Record<string, string> = {
  hegemonic: 'Hegemonique',
  economic: 'Economique',
  military: 'Militaire',
  alliance: 'Alliance',
  territorial: 'Territoriale',
  mixed: 'Mixte',
};

// Military base type names
export const BASE_TYPE_NAMES: Record<string, string> = {
  air_base: 'Base aerienne',
  naval_base: 'Base navale',
  army_base: 'Base terrestre',
  drone_base: 'Base drones',
  listening_post: 'Poste ecoute',
  paramilitary: 'Paramilitaire',
};

// Country flag emoji (for quick display)
export const COUNTRY_FLAGS: Record<string, string> = {
  // Tier 1 - Superpowers
  USA: '🇺🇸',
  CHN: '🇨🇳',
  RUS: '🇷🇺',
  // Tier 2 - Major Powers
  FRA: '🇫🇷',
  GBR: '🇬🇧',
  DEU: '🇩🇪',
  JPN: '🇯🇵',
  IND: '🇮🇳',
  BRA: '🇧🇷',
  SAU: '🇸🇦',
  TUR: '🇹🇷',
  IRN: '🇮🇷',
  ISR: '🇮🇱',
  EGY: '🇪🇬',
  PAK: '🇵🇰',
  IDN: '🇮🇩',
  KOR: '🇰🇷',
  AUS: '🇦🇺',
  ITA: '🇮🇹',
  ESP: '🇪🇸',
  // Tier 3 - Regional Powers
  CAN: '🇨🇦',
  MEX: '🇲🇽',
  ARG: '🇦🇷',
  NLD: '🇳🇱',
  BEL: '🇧🇪',
  PRT: '🇵🇹',
  AUT: '🇦🇹',
  POL: '🇵🇱',
  SWE: '🇸🇪',
  NOR: '🇳🇴',
  DNK: '🇩🇰',
  FIN: '🇫🇮',
  CHE: '🇨🇭',
  GRC: '🇬🇷',
  CZE: '🇨🇿',
  UKR: '🇺🇦',
  ZAF: '🇿🇦',
  NGA: '🇳🇬',
  KEN: '🇰🇪',
  ETH: '🇪🇹',
  MAR: '🇲🇦',
  DZA: '🇩🇿',
  ARE: '🇦🇪',
  QAT: '🇶🇦',
  KWT: '🇰🇼',
  IRQ: '🇮🇶',
  SYR: '🇸🇾',
  LBN: '🇱🇧',
  JOR: '🇯🇴',
  VNM: '🇻🇳',
  THA: '🇹🇭',
  MYS: '🇲🇾',
  SGP: '🇸🇬',
  PHL: '🇵🇭',
  TWN: '🇹🇼',
  PRK: '🇰🇵',
  MMR: '🇲🇲',
  BGD: '🇧🇩',
  AFG: '🇦🇫',
  KAZ: '🇰🇿',
  UZB: '🇺🇿',
  COL: '🇨🇴',
  VEN: '🇻🇪',
  CHL: '🇨🇱',
  PER: '🇵🇪',
  CUB: '🇨🇺',
  NZL: '🇳🇿',
  IRL: '🇮🇪',
  HUN: '🇭🇺',
  ROU: '🇷🇴',
  BGR: '🇧🇬',
  SRB: '🇷🇸',
  HRV: '🇭🇷',
  SVK: '🇸🇰',
  SVN: '🇸🇮',
  LTU: '🇱🇹',
  LVA: '🇱🇻',
  EST: '🇪🇪',
  BLR: '🇧🇾',
  GEO: '🇬🇪',
  ARM: '🇦🇲',
  AZE: '🇦🇿',
  // Tier 4 - Additional
  TKM: '🇹🇲',
  TJK: '🇹🇯',
  KGZ: '🇰🇬',
  MNG: '🇲🇳',
  LKA: '🇱🇰',
  NPL: '🇳🇵',
  KHM: '🇰🇭',
  LAO: '🇱🇦',
  TUN: '🇹🇳',
  LBY: '🇱🇾',
  SDN: '🇸🇩',
  TZA: '🇹🇿',
  GHA: '🇬🇭',
  CIV: '🇨🇮',
  SEN: '🇸🇳',
  CMR: '🇨🇲',
  ECU: '🇪🇨',
  DOM: '🇩🇴',
  OMN: '🇴🇲',
  BHR: '🇧🇭',
  YEM: '🇾🇪',
  // Tier 5 - Small countries
  AGO: '🇦🇴',
  MOZ: '🇲🇿',
  ZMB: '🇿🇲',
  ZWE: '🇿🇼',
  BWA: '🇧🇼',
  NAM: '🇳🇦',
  UGA: '🇺🇬',
  RWA: '🇷🇼',
  BDI: '🇧🇮',
  MWI: '🇲🇼',
  MDG: '🇲🇬',
  MLI: '🇲🇱',
  BFA: '🇧🇫',
  NER: '🇳🇪',
  TCD: '🇹🇩',
  CAF: '🇨🇫',
  COD: '🇨🇩',
  COG: '🇨🇬',
  GAB: '🇬🇦',
  GNQ: '🇬🇶',
  BEN: '🇧🇯',
  TGO: '🇹🇬',
  GIN: '🇬🇳',
  SLE: '🇸🇱',
  LBR: '🇱🇷',
  GMB: '🇬🇲',
  GNB: '🇬🇼',
  MRT: '🇲🇷',
  DJI: '🇩🇯',
  ERI: '🇪🇷',
  SOM: '🇸🇴',
  SSD: '🇸🇸',
  LSO: '🇱🇸',
  SWZ: '🇸🇿',
  BTN: '🇧🇹',
  TLS: '🇹🇱',
  MDV: '🇲🇻',
  BOL: '🇧🇴',
  PRY: '🇵🇾',
  URY: '🇺🇾',
  PAN: '🇵🇦',
  CRI: '🇨🇷',
  GTM: '🇬🇹',
  HND: '🇭🇳',
  SLV: '🇸🇻',
  NIC: '🇳🇮',
  HTI: '🇭🇹',
  JAM: '🇯🇲',
  TTO: '🇹🇹',
  GUY: '🇬🇾',
  SUR: '🇸🇷',
  BLZ: '🇧🇿',
  BHS: '🇧🇸',
  BRB: '🇧🇧',
  PNG: '🇵🇬',
  FJI: '🇫🇯',
  SLB: '🇸🇧',
  VUT: '🇻🇺',
  NCL: '🇳🇨',
  MKD: '🇲🇰',
  MNE: '🇲🇪',
  BIH: '🇧🇦',
  ALB: '🇦🇱',
  MDA: '🇲🇩',
  CYP: '🇨🇾',
  ISL: '🇮🇸',
  LUX: '🇱🇺',
  MLT: '🇲🇹',
  // Tier 6 - Micro-nations
  MCO: '🇲🇨',
  LIE: '🇱🇮',
  SMR: '🇸🇲',
  AND: '🇦🇩',
  VAT: '🇻🇦',
  GIB: '🇬🇮',
  IMN: '🇮🇲',
  GGY: '🇬🇬',
  JEY: '🇯🇪',
  ATG: '🇦🇬',
  DMA: '🇩🇲',
  GRD: '🇬🇩',
  KNA: '🇰🇳',
  LCA: '🇱🇨',
  VCT: '🇻🇨',
  ABW: '🇦🇼',
  CUW: '🇨🇼',
  SXM: '🇸🇽',
  AIA: '🇦🇮',
  MSR: '🇲🇸',
  VGB: '🇻🇬',
  CYM: '🇰🇾',
  TCA: '🇹🇨',
  BMU: '🇧🇲',
  KIR: '🇰🇮',
  MHL: '🇲🇭',
  PLW: '🇵🇼',
  FSM: '🇫🇲',
  TON: '🇹🇴',
  WSM: '🇼🇸',
  TUV: '🇹🇻',
  NRU: '🇳🇷',
  COK: '🇨🇰',
  PYF: '🇵🇫',
  GUM: '🇬🇺',
  ASM: '🇦🇸',
  SYC: '🇸🇨',
  MUS: '🇲🇺',
  COM: '🇰🇲',
  STP: '🇸🇹',
  CPV: '🇨🇻',
  REU: '🇷🇪',
  MYT: '🇾🇹',
  HKG: '🇭🇰',
  MAC: '🇲🇴',
  PSE: '🇵🇸',
  ESH: '🇪🇭',
  GRL: '🇬🇱',
  FLK: '🇫🇰',
  SHN: '🇸🇭',
  BRN: '🇧🇳',
};

// =============================================================================
// DIPLOMATIC NEGOTIATIONS SYSTEM
// =============================================================================

export type AgreementType =
  | 'peace_treaty'
  | 'trade_agreement'
  | 'defensive_alliance'
  | 'oil_agreement'
  | 'development_program'
  | 'non_aggression_pact'
  | 'technology_transfer'
  | 'military_access';

export type NegotiationStatus = 'drafting' | 'proposed' | 'counter_offer' | 'accepted' | 'rejected' | 'expired';

export interface AgreementCondition {
  id: string;
  type: 'demand' | 'offer';
  category: 'economic' | 'military' | 'diplomatic' | 'resource' | 'territorial';
  label: string;
  label_fr: string;
  value: number;
  icon: string;
}

export interface DiplomaticAgreement {
  id: string;
  type: AgreementType;
  initiator: string;
  target: string;
  status: NegotiationStatus;
  year_proposed: number;
  year_expires?: number;
  conditions_offered: AgreementCondition[];
  conditions_demanded: AgreementCondition[];
  counter_conditions?: AgreementCondition[];
  acceptance_probability: number;
  rejection_reason?: string;
}

export interface NegotiationHistory {
  id: string;
  year: number;
  action: 'proposed' | 'accepted' | 'rejected' | 'counter' | 'expired' | 'cancelled';
  actor: string;
  details: string;
  details_fr: string;
}

// Agreement type display names (French)
export const AGREEMENT_TYPE_NAMES: Record<AgreementType, string> = {
  peace_treaty: 'Traite de paix',
  trade_agreement: 'Accord commercial',
  defensive_alliance: 'Alliance defensive',
  oil_agreement: 'Accord petrolier',
  development_program: 'Programme de developpement',
  non_aggression_pact: 'Pacte de non-agression',
  technology_transfer: 'Transfert technologique',
  military_access: 'Acces militaire',
};

// Agreement type colors
export const AGREEMENT_TYPE_COLORS: Record<AgreementType, string> = {
  peace_treaty: 'bg-emerald-500',
  trade_agreement: 'bg-blue-500',
  defensive_alliance: 'bg-purple-500',
  oil_agreement: 'bg-gray-800',
  development_program: 'bg-amber-500',
  non_aggression_pact: 'bg-gray-500',
  technology_transfer: 'bg-cyan-500',
  military_access: 'bg-red-500',
};

// =============================================================================
// SCENARIOS & OBJECTIVES SYSTEM
// =============================================================================

export type ScenarioDifficulty = 'easy' | 'normal' | 'hard' | 'extreme' | 'custom';

export interface ScenarioSummary {
  id: string;
  name: string;
  name_fr: string;
  description: string;
  start_year: number;
  difficulty: ScenarioDifficulty;
  duration: number | null;
  icon: string;
  tags: string[];
}

export interface ScenarioDetail extends ScenarioSummary {
  initial_state: Record<string, unknown>;
  objectives: Record<string, string[]>;
  active_conflicts: Array<{
    attacker: string;
    defender: string;
    type: string;
    intensity: string;
  }>;
  modified_countries: Record<string, Record<string, unknown>>;
  recommended_countries: string[];
  customizable: boolean;
}

export interface ObjectiveSummary {
  id: string;
  name: string;
  description: string;
  type: string;
  difficulty: string;
  points: number;
}

export interface ObjectiveProgress {
  objective_id: string;
  name: string;
  description: string;
  progress: number;
  completed: boolean;
  points: number;
}

export interface ScenarioInitData {
  scenario_id: string;
  scenario_name: string;
  start_year: number;
  difficulty: string;
  difficulty_modifiers: Record<string, number>;
  initial_state: Record<string, unknown>;
  active_conflicts: Array<Record<string, unknown>>;
  modified_countries: Record<string, Record<string, unknown>>;
  player_country: string | null;
  objectives: string[];
  duration: number | null;
}

// Scenario difficulty colors
export const DIFFICULTY_COLORS: Record<ScenarioDifficulty, string> = {
  easy: 'bg-green-500',
  normal: 'bg-blue-500',
  hard: 'bg-orange-500',
  extreme: 'bg-red-600',
  custom: 'bg-purple-500',
};

// Scenario difficulty names (French)
export const DIFFICULTY_NAMES: Record<ScenarioDifficulty, string> = {
  easy: 'Facile',
  normal: 'Normal',
  hard: 'Difficile',
  extreme: 'Extreme',
  custom: 'Personnalise',
};

// Objective type icons
export const OBJECTIVE_TYPE_ICONS: Record<string, string> = {
  alliance: '\ud83e\udd1d',
  influence: '\ud83c\udf0d',
  territorial: '\ud83d\uddfa\ufe0f',
  economic: '\ud83d\udcb0',
  military: '\u2694\ufe0f',
  technology: '\ud83d\ude80',
  survival: '\ud83d\udee1\ufe0f',
  ideology: '\u2728',
  prestige: '\ud83c\udfc6',
  power: '\ud83d\udc51',
  defense: '\ud83d\udee1\ufe0f',
};

// =============================================================================
// REPLAY SYSTEM
// =============================================================================

export interface ReplayMetadata {
  id: string;
  name: string;
  created_at: string;
  start_year: number;
  end_year: number;
  frames_count: number;
  player_country: string | null;
  duration_turns: number;
  description: string | null;
}

export interface ReplayFrame {
  turn: number;
  year: number;
  timestamp: string;
  events: GameEvent[];
  countries_snapshot: Record<string, CountrySnapshot>;
  global_tension: number;
  active_conflicts: string[];
  dominant_powers: Record<string, string>;
}

export interface CountrySnapshot {
  power_score: number;
  economy: number;
  military: number;
  stability: number;
  relations: Record<string, number>;
  at_war_with: string[];
}

export interface ReplayDetail {
  metadata: ReplayMetadata;
  frames: ReplayFrame[];
}

export interface ReplaySummary {
  metadata: ReplayMetadata;
  summary: {
    total_events: number;
    event_counts: Record<string, number>;
    power_changes: Record<string, { start: number; end: number; change: number }>;
    tension_stats: {
      min: number;
      max: number;
      average: number;
      start: number;
      end: number;
    };
    years_covered: number;
  };
}

export interface RecordingStatus {
  is_recording: boolean;
  name?: string;
  start_year?: number;
  frames_count?: number;
  started_at?: string;
}

// =============================================================================
// SCORING SYSTEM
// =============================================================================

export interface CategoryScore {
  score: number;
  breakdown: Record<string, number>;
}

export interface CountryScores {
  country_id: string;
  country_name: string;
  country_name_fr: string;
  tier: number;
  military: CategoryScore;
  economic: CategoryScore;
  stability: CategoryScore;
  influence: CategoryScore;
  intelligence: CategoryScore;
  resources: CategoryScore;
  leadership: CategoryScore;
  global_score: number;
  world_rank: number;
  is_intelligence_hidden: boolean;  // True if intel data is estimated
  intelligence_confidence: number;  // 0-100, confidence in intel data
}

export interface RankingEntry {
  rank: number;
  country_id: string;
  country_name: string;
  country_name_fr: string;
  flag: string;
  tier: number;
  global_score: number;
  military: number;
  economic: number;
  stability: number;
  influence: number;
  intelligence: number;
  resources: number;
  leadership: number;
}

export interface CategoryRankingEntry {
  rank: number;
  country_id: string;
  country_name: string;
  country_name_fr: string;
  score: number;
  breakdown: Record<string, number>;
}

export interface ScoringCategory {
  id: string;
  name: string;
  name_fr: string;
  description: string;
  weight: number;
  factors: string[];
}

export interface ScoringSummary {
  year: number;
  total_countries: number;
  top5_global: Array<{
    rank: number;
    country_id: string;
    global_score: number;
  }>;
  category_leaders: Record<string, {
    country_id: string;
    score: number;
  }>;
  average_global_score: number;
  score_distribution: {
    excellent: number;
    good: number;
    average: number;
    weak: number;
    failing: number;
  };
}

export interface CountryComparison {
  country1: {
    id: string;
    name: string;
    name_fr: string;
    global_score: number;
  };
  country2: {
    id: string;
    name: string;
    name_fr: string;
    global_score: number;
  };
  categories: Record<string, {
    country1_score: number;
    country2_score: number;
    difference: number;
    winner: string;
  }>;
  winner: string;
}

// Scoring category colors
export const SCORING_CATEGORY_COLORS: Record<string, string> = {
  military: 'bg-red-500',
  economic: 'bg-green-500',
  stability: 'bg-blue-500',
  influence: 'bg-purple-500',
  intelligence: 'bg-gray-600',
  resources: 'bg-amber-500',
  leadership: 'bg-cyan-500',
};

// Scoring category hex colors (for charts)
export const SCORING_CATEGORY_HEX: Record<string, string> = {
  military: '#ef4444',
  economic: '#22c55e',
  stability: '#3b82f6',
  influence: '#a855f7',
  intelligence: '#4b5563',
  resources: '#f59e0b',
  leadership: '#06b6d4',
};

// Scoring category names (French)
export const SCORING_CATEGORY_NAMES: Record<string, string> = {
  military: 'Militaire',
  economic: 'Economique',
  stability: 'Stabilite',
  influence: 'Influence',
  intelligence: 'Renseignement',
  resources: 'Ressources',
  leadership: 'Leadership',
};

// =============================================================================
// POWER SCORE COLOR SYSTEM
// =============================================================================

/**
 * Get color for a power score using continuous gradient
 * Red (powerful) -> Orange -> Yellow -> Green -> Blue -> Gray (weak)
 */
export function getPowerScoreColor(powerScore: number): string {
  // Clamp to 0-100
  const score = Math.max(0, Math.min(100, powerScore));

  if (score >= 80) {
    // Red to Orange (80-100)
    const t = (score - 80) / 20;
    return interpolateColor('#FF8800', '#FF4444', t);
  }
  if (score >= 60) {
    // Orange to Yellow (60-80)
    const t = (score - 60) / 20;
    return interpolateColor('#FFCC00', '#FF8800', t);
  }
  if (score >= 40) {
    // Yellow to Green (40-60)
    const t = (score - 40) / 20;
    return interpolateColor('#88CC44', '#FFCC00', t);
  }
  if (score >= 20) {
    // Green to Blue (20-40)
    const t = (score - 20) / 20;
    return interpolateColor('#4499BB', '#88CC44', t);
  }
  // Blue to Gray (0-20)
  const t = score / 20;
  return interpolateColor('#AABBCC', '#4499BB', t);
}

/**
 * Get Tailwind-compatible color class for power score
 * Returns a bg-* class for use in Tailwind
 */
export function getPowerScoreTailwindClass(powerScore: number): string {
  if (powerScore >= 80) return 'bg-red-500';
  if (powerScore >= 65) return 'bg-orange-500';
  if (powerScore >= 50) return 'bg-yellow-500';
  if (powerScore >= 35) return 'bg-lime-500';
  if (powerScore >= 20) return 'bg-cyan-500';
  return 'bg-slate-400';
}

/**
 * Get text color class for power score (for contrast)
 */
export function getPowerScoreTextClass(powerScore: number): string {
  if (powerScore >= 50) return 'text-white';
  return 'text-slate-800';
}

/**
 * Interpolate between two hex colors
 */
function interpolateColor(color1: string, color2: string, t: number): string {
  const r1 = parseInt(color1.slice(1, 3), 16);
  const g1 = parseInt(color1.slice(3, 5), 16);
  const b1 = parseInt(color1.slice(5, 7), 16);

  const r2 = parseInt(color2.slice(1, 3), 16);
  const g2 = parseInt(color2.slice(3, 5), 16);
  const b2 = parseInt(color2.slice(5, 7), 16);

  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * Get alignment color (West-East spectrum)
 * Blue (pro-West) -> Gray (neutral) -> Red (pro-East)
 */
export function getAlignmentColor(alignment: number): string {
  if (alignment <= -50) return '#4488FF';      // Bleu vif (pro-West fort)
  if (alignment <= -20) return '#77AAFF';      // Bleu clair
  if (alignment <= 20) return '#AAAAAA';       // Gris (neutre)
  if (alignment <= 50) return '#FFAA77';       // Orange clair
  return '#FF6644';                            // Rouge (pro-East fort)
}

/**
 * Get alignment Tailwind class
 */
export function getAlignmentTailwindClass(alignment: number): string {
  if (alignment <= -50) return 'bg-blue-500';
  if (alignment <= -20) return 'bg-blue-300';
  if (alignment <= 20) return 'bg-gray-400';
  if (alignment <= 50) return 'bg-orange-300';
  return 'bg-red-500';
}

// Influence colors for major powers (hex for map overlays)
export const INFLUENCE_POWER_COLORS: Record<string, string> = {
  USA: 'rgba(65, 105, 225, 0.3)',   // Royal blue
  CHN: 'rgba(220, 20, 60, 0.3)',    // Crimson
  RUS: 'rgba(138, 43, 226, 0.3)',   // Purple
  FRA: 'rgba(0, 85, 164, 0.25)',    // France blue
  GBR: 'rgba(1, 33, 105, 0.25)',    // UK navy
  DEU: 'rgba(255, 206, 0, 0.2)',    // German gold
  IND: 'rgba(255, 153, 51, 0.25)',  // India orange
  BRA: 'rgba(0, 151, 57, 0.25)',    // Brazil green
  AUS: 'rgba(0, 132, 61, 0.25)',    // Australia green
  SAU: 'rgba(0, 108, 53, 0.25)',    // Saudi green
};

// =============================================================================
// SUBNATIONAL REGIONS
// =============================================================================

export interface SubnationalRegion {
  id: string;
  country_id: string;
  name: string;
  name_fr: string;
  region_type: string;
  power_score: number;
  strategic_value: number;
  population_share: number;
  economic_share: number;
  military_presence: number;
  is_capital_region: boolean;
  is_border_region: boolean;
  is_coastal: boolean;
  has_oil: boolean;
  has_strategic_resources: boolean;
  resource_type: string | null;
  attack_difficulty: number;
  strategic_importance: number;
}

export interface RegionsSummary {
  total: number;
  by_country: Record<string, number>;
  by_region_type: Record<string, number>;
  capital_regions: number;
  coastal_regions: number;
  resource_regions: number;
}

export interface AttackType {
  type: string;
  name: string;
  name_fr: string;
  risk: string;
  description: string;
}

export interface AttackInfo {
  region_id: string;
  region_name: string;
  country_id: string;
  attack_difficulty: number;
  strategic_importance: number;
  population_share: number;
  economic_share: number;
  is_capital_region: boolean;
  is_coastal: boolean;
  has_resources: boolean;
  attack_types: AttackType[];
  potential_consequences: string[];
}

// Attack result after executing an attack
export interface RegionAttackResult {
  success: boolean;
  damage_dealt: number;
  casualties_attacker: number;
  casualties_defender: number;
  region_damage: number;
  message: string;
  message_fr: string;
  consequences: string[];
  region_status: SubnationalRegion;
}

// Region type labels
export const REGION_TYPE_NAMES: Record<string, string> = {
  census_region: 'Region de recensement',
  economic_zone: 'Zone economique',
  federal_district: 'District federal',
  geographic_zone: 'Zone geographique',
  administrative_region: 'Region administrative',
  constituent_country: 'Nation constitutive',
  geographic_region: 'Region geographique',
  ibge_region: 'Region IBGE',
  laender_group: 'Groupe de Lander',
  state: 'Etat',
  autonomous_region: 'Region autonome',
  overseas: 'Outre-mer',
};

// Resource type labels
export const RESOURCE_TYPE_NAMES: Record<string, string> = {
  oil: 'Petrole',
  minerals: 'Mineraux',
  tech: 'Technologie',
  agriculture: 'Agriculture',
};

// Attack risk labels
export const ATTACK_RISK_NAMES: Record<string, string> = {
  faible: 'Faible',
  modere: 'Modere',
  eleve: 'Eleve',
};

// ============================================================================
// STRATEGIC ADVICE TYPES
// ============================================================================

export interface StrategicThreat {
  id: string;
  name_fr: string;
  type: 'war' | 'rival' | 'systemic' | 'unknown';
  level: 'critical' | 'high' | 'medium' | 'low' | 'none';
  power_diff: number;
  relation?: number;
}

export interface StrategicOpportunity {
  type: 'alliance' | 'economic_growth' | 'nuclear_program' | 'influence_expansion';
  priority: 'high' | 'medium' | 'low';
  target_id?: string;
  target_name_fr?: string;
  relation?: number;
  potential?: number;
  current?: number;
  soft_power?: number;
  description_fr?: string;
}

export interface StrategicRecommendation {
  action: string;
  action_fr: string;
  target?: string;
  target_name_fr?: string;
  priority: number;
  reason_fr: string;
  command: string;
}

export interface DiplomaticSummary {
  allies_count: number;
  rivals_count: number;
  at_war: boolean;
  wars_count: number;
  sanctions_active: number;
  blocs: string[];
  superpower_relations: Record<string, number>;
}

export interface StrategicAdvice {
  country_id: string;
  strategic_goal: string;
  strategic_goal_fr: string;
  power_rank: number;
  total_countries: number;
  threats: StrategicThreat[];
  opportunities: StrategicOpportunity[];
  recommendations: StrategicRecommendation[];
  diplomatic_summary: DiplomaticSummary;
  ollama_advice?: string;
  ollama_available: boolean;
}

// =============================================================================
// TIMELINE SYSTEM
// =============================================================================

export interface GameDate {
  year: number;
  month: number;
  day: number;
  display: string;        // "February 15, 2025"
  display_fr: string;     // "15 Fevrier 2025"
}

export type TimelineEventType =
  | 'war'
  | 'diplomatic'
  | 'economic'
  | 'political'
  | 'military'
  | 'internal'
  | 'technology'
  | 'cultural'
  | 'crisis'
  | 'player_action';

export type TimelineEventSource =
  | 'historical'
  | 'procedural'
  | 'player'
  | 'ai_generated'
  | 'system';

export type EventFamily =
  | 'structural'   // Long-term shifts (elections, treaties)
  | 'tactical'     // Short-term actions (sanctions, deployments)
  | 'opportunity'  // Windows of action (summits, crises)
  | 'escalation'   // Rising tensions (military buildups)
  | 'narrative'    // Story-driven events (AI-generated arcs)
  | 'player';      // Player decisions

export interface CausalLink {
  event_id: string;
  title: string;
  title_fr: string;
  date: GameDate;
  link_type: 'direct' | 'indirect' | 'probable';
  strength: number;  // 0.0 - 1.0
}

export interface TimelineEvent {
  id: string;
  date: GameDate;
  actor_country: string;
  target_countries: string[];
  title: string;
  title_fr: string;
  description: string;
  description_fr: string;
  type: TimelineEventType;
  source: TimelineEventSource;
  importance: number;  // 1-5 (5 = critical)
  family: EventFamily;
  read: boolean;
  caused_by: string | null;
  triggers: string[];
  // Causal chain visualization
  caused_by_chain: CausalLink[];  // Previous causes (up to 3)
  effects_chain: CausalLink[];    // Probable effects (up to 3)
  // Ripple effects
  ripple_weight: number;
  ripple_targets: string[];
}

export interface TimelineEventBrief {
  id: string;
  date: string;
  actor_country: string;
  title_fr: string;
  type: string;
  importance: number;
}

export interface MonthlyTickResponse {
  year: number;
  month: number;
  date_display: string;
  date_display_fr: string;
  events: GameEvent[];
  timeline_events: TimelineEventBrief[];
  summary: string;
  summary_fr: string;
  game_ended: boolean;
  game_end_reason: string | null;
  game_end_message: string;
  game_end_message_fr: string;
  is_victory: boolean;
  final_score: number;
  defcon_level: number;
  unread_events: number;
}

export interface TimelineSummary {
  total_events: number;
  unread_count: number;
  pending_effects: number;
  current_date: GameDate;
  recent_events: TimelineEvent[];
}

// Extended WorldState with timeline fields
export interface WorldStateWithTimeline extends WorldState {
  month: number;
  date_display: string;
  unread_events: number;
  timeline_total: number;
}

// Timeline event type colors
export const TIMELINE_EVENT_COLORS: Record<TimelineEventType, string> = {
  war: 'bg-red-600',
  diplomatic: 'bg-blue-500',
  economic: 'bg-green-500',
  political: 'bg-purple-500',
  military: 'bg-gray-600',
  internal: 'bg-amber-500',
  technology: 'bg-cyan-500',
  cultural: 'bg-pink-500',
  crisis: 'bg-red-500',
  player_action: 'bg-indigo-500',
};

// Timeline event type names (French)
export const TIMELINE_EVENT_TYPE_NAMES: Record<TimelineEventType, string> = {
  war: 'Guerre',
  diplomatic: 'Diplomatique',
  economic: 'Economique',
  political: 'Politique',
  military: 'Militaire',
  internal: 'Interne',
  technology: 'Technologie',
  cultural: 'Culturel',
  crisis: 'Crise',
  player_action: 'Action joueur',
};

// Timeline source names (French)
export const TIMELINE_SOURCE_NAMES: Record<TimelineEventSource, string> = {
  historical: 'Historique',
  procedural: 'Procedural',
  player: 'Joueur',
  ai_generated: 'IA',
  system: 'Systeme',
};

// Month names for display
export const MONTH_NAMES_FR = [
  'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
];

export const MONTH_NAMES_EN = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

/**
 * Format a game date for display
 */
export function formatGameDate(date: GameDate, lang: 'fr' | 'en' = 'fr'): string {
  const months = lang === 'fr' ? MONTH_NAMES_FR : MONTH_NAMES_EN;
  if (lang === 'fr') {
    return `${date.day} ${months[date.month - 1]} ${date.year}`;
  }
  return `${months[date.month - 1]} ${date.day}, ${date.year}`;
}

/**
 * Format month/year for display (header)
 */
export function formatMonthYear(year: number, month: number, lang: 'fr' | 'en' = 'fr'): string {
  const months = lang === 'fr' ? MONTH_NAMES_FR : MONTH_NAMES_EN;
  return `${months[month - 1]} ${year}`;
}

/**
 * Get importance badge color
 */
export function getImportanceColor(importance: number): string {
  switch (importance) {
    case 5: return 'bg-red-600';
    case 4: return 'bg-orange-500';
    case 3: return 'bg-yellow-500';
    case 2: return 'bg-blue-400';
    default: return 'bg-gray-400';
  }
}

/**
 * Get importance label (French)
 */
export function getImportanceLabel(importance: number): string {
  switch (importance) {
    case 5: return 'Critique';
    case 4: return 'Important';
    case 3: return 'Notable';
    case 2: return 'Mineur';
    default: return 'Anecdotique';
  }
}
