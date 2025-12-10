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

  // Tier 4 summary
  tier4_count: number;
  tier4_in_crisis: number;
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

export interface TickResponse {
  year: number;
  events: GameEvent[];
  summary: string;
  summary_fr: string;
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
  4: 'Etat secondaire',
};

// Region display names
export const REGION_NAMES: Record<string, string> = {
  africa: 'Afrique',
  asia: 'Asie',
  middle_east: 'Moyen-Orient',
  latam: 'Amerique latine',
  europe: 'Europe',
  oceania: 'Oceanie',
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
  USA: '\ud83c\uddfa\ud83c\uddf8',
  CHN: '\ud83c\udde8\ud83c\uddf3',
  RUS: '\ud83c\uddf7\ud83c\uddfa',
  FRA: '\ud83c\uddeb\ud83c\uddf7',
  GBR: '\ud83c\uddec\ud83c\udde7',
  DEU: '\ud83c\udde9\ud83c\uddea',
  JPN: '\ud83c\uddef\ud83c\uddf5',
  IND: '\ud83c\uddee\ud83c\uddf3',
  BRA: '\ud83c\udde7\ud83c\uddf7',
  SAU: '\ud83c\uddf8\ud83c\udde6',
  TUR: '\ud83c\uddf9\ud83c\uddf7',
  IRN: '\ud83c\uddee\ud83c\uddf7',
  ISR: '\ud83c\uddee\ud83c\uddf1',
  EGY: '\ud83c\uddea\ud83c\uddec',
  PAK: '\ud83c\uddf5\ud83c\uddf0',
  IDN: '\ud83c\uddee\ud83c\udde9',
  KOR: '\ud83c\uddf0\ud83c\uddf7',
  AUS: '\ud83c\udde6\ud83c\uddfa',
  ITA: '\ud83c\uddee\ud83c\uddf9',
  ESP: '\ud83c\uddea\ud83c\uddf8',
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
