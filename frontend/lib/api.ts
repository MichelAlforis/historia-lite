// Historia Lite - API Client
import axios from 'axios';
import {
  WorldState,
  Country,
  TickResponse,
  GameEvent,
  InfluenceZone,
  GameSettings,
  OllamaStatus,
  Tier4Country,
  Tier4Summary,
  Tier5Country,
  Tier5Summary,
  Tier6Country,
  Tier6Summary,
  CommandResponse,
  ProjectListResponse,
  ProjectResponse,
  PendingDilemmasResponse,
  DilemmaResolveResponse,
  ActiveDilemma,
  MilitaryBase,
  InfluenceRanking,
  PowerGlobalInfluence,
  ScenarioSummary,
  ScenarioDetail,
  ObjectiveSummary,
  ScenarioInitData,
  Leader,
} from './types';

// Historia Lite specific API URL - use dedicated env var to avoid CRM conflicts
const API_BASE = process.env.NEXT_PUBLIC_HISTORIA_API_URL || 'http://localhost:8001/api';
const API_ROOT = process.env.NEXT_PUBLIC_HISTORIA_API_URL?.replace('/api', '') || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Root API instance (for routes not under /api)
const apiRoot = axios.create({
  baseURL: API_ROOT,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getWorldState(): Promise<WorldState> {
  const response = await api.get<WorldState>('/state');
  return response.data;
}

export async function getCountry(countryId: string): Promise<Country> {
  const response = await api.get<Country>(`/country/${countryId}`);
  return response.data;
}

export async function advanceTick(): Promise<TickResponse> {
  const response = await api.post<TickResponse>('/tick');
  return response.data;
}

export async function advanceMultipleTicks(years: number): Promise<TickResponse[]> {
  const response = await api.post<TickResponse[]>(`/tick/${years}`);
  return response.data;
}

export async function resetWorld(seed: number = 42): Promise<{ status: string; year: number; seed: number }> {
  const response = await api.post('/reset', null, { params: { seed } });
  return response.data;
}

export async function getEvents(count: number = 50): Promise<GameEvent[]> {
  const response = await api.get<GameEvent[]>('/events', { params: { count } });
  return response.data;
}

export async function getInfluenceZones(): Promise<InfluenceZone[]> {
  const response = await api.get<InfluenceZone[]>('/influence-zones');
  return response.data;
}

export async function getSuperpowers(): Promise<Country[]> {
  const response = await api.get<Country[]>('/superpowers');
  return response.data;
}

export async function getNuclearPowers(): Promise<Country[]> {
  const response = await api.get<Country[]>('/nuclear-powers');
  return response.data;
}

export async function getBlocMembers(blocName: string): Promise<Country[]> {
  const response = await api.get<Country[]>(`/bloc/${blocName}`);
  return response.data;
}

// ============================================================================
// AI / OLLAMA ENDPOINTS
// ============================================================================

export async function getSettings(): Promise<GameSettings> {
  const response = await api.get<GameSettings>('/settings');
  return response.data;
}

export async function updateSettings(settings: Partial<GameSettings>): Promise<GameSettings> {
  const response = await api.post<GameSettings>('/settings', settings);
  return response.data;
}

export async function getOllamaStatus(): Promise<OllamaStatus> {
  const response = await api.get<OllamaStatus>('/ollama/status');
  return response.data;
}

export async function advanceTickWithOllama(): Promise<TickResponse> {
  const response = await api.post<TickResponse>('/tick/ollama');
  return response.data;
}

// ============================================================================
// TIER 4 ENDPOINTS
// ============================================================================

export async function getTier4Countries(params?: {
  region?: string;
  alignment?: string;
  in_crisis?: boolean;
}): Promise<Tier4Country[]> {
  const response = await api.get<Tier4Country[]>('/tier4', { params });
  return response.data;
}

export async function getTier4Summary(): Promise<Tier4Summary> {
  const response = await api.get<Tier4Summary>('/tier4/summary');
  return response.data;
}

export async function getTier4Country(countryId: string): Promise<Tier4Country> {
  const response = await api.get<Tier4Country>(`/tier4/${countryId}`);
  return response.data;
}

export async function getTier4ByRegion(region: string): Promise<Tier4Country[]> {
  const response = await api.get<Tier4Country[]>(`/tier4/region/${region}`);
  return response.data;
}

// ============================================================================
// TIER 5 ENDPOINTS
// ============================================================================

export async function getTier5Countries(params?: {
  region?: string;
  alignment?: string;
  protector?: string;
  in_crisis?: boolean;
}): Promise<Tier5Country[]> {
  const response = await api.get<Tier5Country[]>('/tier5', { params });
  return response.data;
}

export async function getTier5Summary(): Promise<Tier5Summary> {
  const response = await api.get<Tier5Summary>('/tier5/summary');
  return response.data;
}

export async function getTier5Country(countryId: string): Promise<Tier5Country> {
  const response = await api.get<Tier5Country>(`/tier5/${countryId}`);
  return response.data;
}

export async function getTier5ByRegion(region: string): Promise<Tier5Country[]> {
  const response = await api.get<Tier5Country[]>(`/tier5/region/${region}`);
  return response.data;
}

export async function getTier5ByProtector(protectorId: string): Promise<Tier5Country[]> {
  const response = await api.get<Tier5Country[]>(`/tier5/protector/${protectorId}`);
  return response.data;
}

// ============================================================================
// TIER 6 ENDPOINTS
// ============================================================================

export async function getTier6Countries(params?: {
  region?: string;
  protector?: string;
  is_territory?: boolean;
  special_status?: string;
}): Promise<Tier6Country[]> {
  const response = await api.get<Tier6Country[]>('/tier6', { params });
  return response.data;
}

export async function getTier6Summary(): Promise<Tier6Summary> {
  const response = await api.get<Tier6Summary>('/tier6/summary');
  return response.data;
}

export async function getTier6Country(countryId: string): Promise<Tier6Country> {
  const response = await api.get<Tier6Country>(`/tier6/${countryId}`);
  return response.data;
}

export async function getTier6ByProtector(protectorId: string): Promise<Tier6Country[]> {
  const response = await api.get<Tier6Country[]>(`/tier6/protector/${protectorId}`);
  return response.data;
}

export async function getTier6Influence(countryId: string): Promise<{
  country_id: string;
  protector: string;
  influence_zone: string;
  protector_stats: {
    id: string;
    name: string;
    power_score: number;
    tier: number;
  };
  consequences_if_attacked: string[];
}> {
  const response = await api.get(`/tier6/${countryId}/influence`);
  return response.data;
}

// ============================================================================
// SUBNATIONAL REGIONS ENDPOINTS
// ============================================================================

import {
  SubnationalRegion,
  RegionsSummary,
  AttackInfo,
  RegionAttackResult,
} from './types';

export async function getRegions(params?: {
  country_id?: string;
  region_type?: string;
  has_resources?: boolean;
  is_coastal?: boolean;
}): Promise<SubnationalRegion[]> {
  const response = await apiRoot.get<SubnationalRegion[]>('/regions', { params });
  return response.data;
}

export async function getRegionsSummary(): Promise<RegionsSummary> {
  const response = await apiRoot.get<RegionsSummary>('/regions/summary');
  return response.data;
}

export async function getRegionsByCountry(countryId: string): Promise<SubnationalRegion[]> {
  const response = await apiRoot.get<SubnationalRegion[]>(`/regions/country/${countryId}`);
  return response.data;
}

export async function getRegion(regionId: string): Promise<SubnationalRegion> {
  const response = await apiRoot.get<SubnationalRegion>(`/regions/${regionId}`);
  return response.data;
}

export async function getRegionAttackInfo(regionId: string): Promise<AttackInfo> {
  const response = await apiRoot.get<AttackInfo>(`/regions/${regionId}/attack-info`);
  return response.data;
}

export async function executeRegionAttack(
  regionId: string,
  attackerId: string,
  attackType: string
): Promise<RegionAttackResult> {
  const response = await apiRoot.post<RegionAttackResult>(`/regions/${regionId}/attack`, {
    attacker_id: attackerId,
    attack_type: attackType,
  });
  return response.data;
}

// ============================================================================
// COMMAND SYSTEM
// ============================================================================

export async function sendCommand(
  command: string,
  playerCountryId: string
): Promise<CommandResponse> {
  const response = await api.post<CommandResponse>('/command', {
    command,
    player_country_id: playerCountryId,
  });
  return response.data;
}

export async function confirmCommand(
  commandId: string,
  playerCountryId: string
): Promise<CommandResponse> {
  const response = await api.post<CommandResponse>('/command/confirm', {
    command_id: commandId,
    player_country_id: playerCountryId,
  });
  return response.data;
}

// ============================================================================
// PROJECT SYSTEM
// ============================================================================

export async function getProjects(countryId: string): Promise<ProjectListResponse> {
  const response = await api.get<ProjectListResponse>(`/projects/${countryId}`);
  return response.data;
}

export async function startProject(
  countryId: string,
  projectId: string
): Promise<ProjectResponse> {
  const response = await api.post<ProjectResponse>(
    `/projects/${countryId}/start/${projectId}`
  );
  return response.data;
}

export async function cancelProject(
  countryId: string,
  projectId: string
): Promise<{ status: string; project_id: string }> {
  const response = await api.post(`/projects/${countryId}/cancel/${projectId}`);
  return response.data;
}

export async function accelerateProject(
  countryId: string,
  projectId: string
): Promise<{ status: string; project_id: string }> {
  const response = await api.post(`/projects/${countryId}/accelerate/${projectId}`);
  return response.data;
}

// ============================================================================
// DILEMMA SYSTEM
// ============================================================================

export async function getPendingDilemmas(
  countryId: string
): Promise<PendingDilemmasResponse> {
  try {
    const response = await api.get<PendingDilemmasResponse>(
      `/dilemmas/${countryId}/pending`
    );
    return response.data;
  } catch {
    // Endpoint may not exist yet - return empty dilemmas
    return { country_id: countryId, pending_dilemmas: [], count: 0 };
  }
}

export async function resolveDilemma(
  dilemmaId: string,
  choiceId: number,
  playerCountryId: string
): Promise<DilemmaResolveResponse> {
  const response = await api.post<DilemmaResolveResponse>('/dilemmas/resolve', {
    dilemma_id: dilemmaId,
    choice_id: choiceId,
    player_country_id: playerCountryId,
  });
  return response.data;
}

export async function getDilemmaHistory(
  countryId: string
): Promise<{ country_id: string; resolved_dilemmas: ActiveDilemma[]; total: number }> {
  const response = await api.get(`/dilemmas/${countryId}/history`);
  return response.data;
}

export async function detectDilemmas(
  countryId: string
): Promise<{ detected: number; dilemmas: { id: string; title: string; title_fr: string }[] }> {
  const response = await api.post(`/dilemmas/detect/${countryId}`);
  return response.data;
}

// ============================================================================
// PLAYER SELECTION
// ============================================================================

export async function selectPlayerCountry(
  countryId: string
): Promise<{ status: string; player_country_id: string; player_country_name: string; player_country_name_fr: string }> {
  const response = await api.post(`/player/select/${countryId}`);
  return response.data;
}

export async function getPlayerCountry(): Promise<{
  player_country_id: string | null;
  player_country_name?: string;
  player_country_name_fr?: string;
  message?: string;
}> {
  const response = await api.get('/player');
  return response.data;
}

// ============================================================================
// INFLUENCE SYSTEM
// ============================================================================

// Get all influence zones with detailed breakdown
export async function getInfluenceZonesAdvanced(): Promise<{ zones: InfluenceZone[]; total: number }> {
  const response = await api.get('/influence/zones');
  return response.data;
}

// Get single zone details
export async function getInfluenceZone(zoneId: string): Promise<{ zone: InfluenceZone; influence_levels: Record<string, number>; influence_breakdown: Record<string, Record<string, number>> }> {
  const response = await api.get(`/influence/zone/${zoneId}`);
  return response.data;
}

// Get detailed breakdown for a zone
export async function getZoneBreakdown(zoneId: string): Promise<{
  zone_id: string;
  zone_name_fr: string;
  dominant_power: string | null;
  contested_by: string[];
  strength: number;
  influence_breakdown: Record<string, Record<string, number>>;
  total_by_power: Record<string, number>;
  cultural_factors: {
    dominant_religion: string | null;
    dominant_culture: string | null;
    dominant_language: string | null;
  };
  resources: {
    has_oil: boolean;
    has_strategic_resources: boolean;
  };
  military_bases: MilitaryBase[];
}> {
  const response = await api.get(`/influence/zone/${zoneId}/breakdown`);
  return response.data;
}

// Get all military bases
export async function getMilitaryBases(): Promise<{ bases: MilitaryBase[]; total: number }> {
  const response = await api.get('/influence/military-bases');
  return response.data;
}

// Get bases by owner country
export async function getBasesByOwner(countryId: string): Promise<{
  owner: string;
  bases: MilitaryBase[];
  total: number;
  total_personnel: number;
}> {
  const response = await api.get(`/influence/military-bases/owner/${countryId}`);
  return response.data;
}

// Get bases in a zone
export async function getBasesInZone(zoneId: string): Promise<{
  zone_id: string;
  bases: MilitaryBase[];
  by_owner: Record<string, MilitaryBase[]>;
  total: number;
  military_presence: Record<string, number>;
}> {
  const response = await api.get(`/influence/military-bases/zone/${zoneId}`);
  return response.data;
}

// Establish a new military base
export async function establishBase(data: {
  owner_id: string;
  host_country_id: string;
  zone_id: string;
  base_type: string;
  personnel: number;
  base_name?: string;
}): Promise<{ success: boolean; message_fr: string; effects: Record<string, unknown> }> {
  const response = await api.post('/influence/military-base/establish', data);
  return response.data;
}

// Close a military base
export async function closeBase(baseId: string): Promise<{ success: boolean; message_fr: string; effects: Record<string, unknown> }> {
  const response = await api.post('/influence/military-base/close', { base_id: baseId });
  return response.data;
}

// Launch cultural program
export async function launchCulturalProgram(data: {
  power_id: string;
  zone_id: string;
  program_type: string;
  investment: number;
}): Promise<{ success: boolean; message_fr: string; effects: Record<string, unknown> }> {
  const response = await api.post('/influence/cultural-program', data);
  return response.data;
}

// Sign arms deal
export async function signArmsDeal(data: {
  seller_id: string;
  buyer_id: string;
  value: number;
  category?: string;
}): Promise<{ success: boolean; message_fr: string; effects: Record<string, unknown> }> {
  const response = await api.post('/influence/arms-deal', data);
  return response.data;
}

// Get influence rankings
export async function getInfluenceRankings(): Promise<{ rankings: InfluenceRanking[]; total_zones: number }> {
  const response = await api.get('/influence/rankings');
  return response.data;
}

// Get global influence for a power
export async function getPowerGlobalInfluence(countryId: string): Promise<PowerGlobalInfluence> {
  const response = await api.get(`/influence/power/${countryId}/global`);
  return response.data;
}

// Get religions reference data
export async function getReligions(): Promise<{ religions: Array<{ id: string; name: string; name_fr: string; influence_power: string | null }> }> {
  const response = await api.get('/influence/religions');
  return response.data;
}

// Get cultures reference data
export async function getCultures(): Promise<{ cultures: Array<{ id: string; name: string; name_fr: string; language: string | null; soft_power_bonus: number }> }> {
  const response = await api.get('/influence/cultures');
  return response.data;
}

// ============================================================================
// SAVE/LOAD SYSTEM
// ============================================================================

export interface SaveMetadata {
  id: string;
  name: string;
  created_at: string;
  year: number;
  player_country: string | null;
  countries_count: number;
  global_tension: number;
  description: string | null;
}

export interface SavesList {
  saves: SaveMetadata[];
  total: number;
}

export interface SaveGameResponse {
  success: boolean;
  message: string;
  save_id: string;
  metadata: SaveMetadata;
}

export interface LoadGameResponse {
  success: boolean;
  message: string;
  year: number;
  countries_count: number;
}

// List all saves
export async function listSaves(): Promise<SavesList> {
  const response = await api.get('/saves/list');
  return response.data;
}

// Save current game
export async function saveGame(name: string, description?: string): Promise<SaveGameResponse> {
  const response = await api.post('/saves/save', { name, description });
  return response.data;
}

// Load a saved game
export async function loadGame(saveId: string): Promise<LoadGameResponse> {
  const response = await api.post(`/saves/load/${saveId}`);
  return response.data;
}

// Delete a save
export async function deleteSave(saveId: string): Promise<{ success: boolean; message: string }> {
  const response = await api.delete(`/saves/${saveId}`);
  return response.data;
}

// Get save metadata
export async function getSaveMetadata(saveId: string): Promise<SaveMetadata> {
  const response = await api.get(`/saves/${saveId}`);
  return response.data;
}

// Export save as JSON
export async function exportSave(saveId: string): Promise<{
  metadata: SaveMetadata;
  world_state: Record<string, unknown>;
  settings: Record<string, unknown>;
}> {
  const response = await api.get(`/saves/${saveId}/export`);
  return response.data;
}

// Import save from JSON
export async function importSave(saveData: Record<string, unknown>): Promise<{
  success: boolean;
  message: string;
  save_id: string;
}> {
  const response = await api.post('/saves/import', saveData);
  return response.data;
}

// Create autosave
export async function createAutosave(): Promise<{ success: boolean; message: string }> {
  const response = await api.post('/saves/autosave');
  return response.data;
}

// ============================================================================
// DIPLOMATIC NEGOTIATIONS
// ============================================================================

export interface DiplomaticAgreementRequest {
  initiator_id: string;
  target_id: string;
  agreement_type: string;
  conditions_offered: Array<{
    type: string;
    category: string;
    label: string;
    label_fr: string;
    value: number;
  }>;
  conditions_demanded: Array<{
    type: string;
    category: string;
    label: string;
    label_fr: string;
    value: number;
  }>;
}

export interface DiplomaticAgreementResponse {
  id: string;
  type: string;
  initiator: string;
  target: string;
  status: string;
  year_proposed: number;
  year_expires: number;
  acceptance_probability: number;
  accepted: boolean;
  rejection_reason?: string;
  message_fr: string;
}

// Propose a diplomatic agreement
export async function proposeDiplomaticAgreement(
  data: DiplomaticAgreementRequest
): Promise<DiplomaticAgreementResponse> {
  const response = await api.post('/diplomacy/propose', data);
  return response.data;
}

// Get active agreements for a country
export async function getActiveAgreements(countryId: string): Promise<{
  country_id: string;
  agreements: DiplomaticAgreementResponse[];
  total: number;
}> {
  const response = await api.get(`/diplomacy/agreements/${countryId}`);
  return response.data;
}

// Get negotiation history
export async function getNegotiationHistory(countryId: string): Promise<{
  country_id: string;
  history: Array<{
    id: string;
    year: number;
    action: string;
    actor: string;
    details_fr: string;
  }>;
  total: number;
}> {
  const response = await api.get(`/diplomacy/history/${countryId}`);
  return response.data;
}

// Cancel/terminate an agreement
export async function terminateAgreement(agreementId: string): Promise<{
  success: boolean;
  message_fr: string;
  diplomatic_cost: number;
}> {
  const response = await api.post(`/diplomacy/terminate/${agreementId}`);
  return response.data;
}

// Get feasibility check for potential agreement
export async function checkAgreementFeasibility(
  initiatorId: string,
  targetId: string,
  agreementType: string
): Promise<{
  feasible: boolean;
  reason_fr: string;
  min_relation_required: number;
  current_relation: number;
  estimated_acceptance: number;
}> {
  const response = await api.get('/diplomacy/feasibility', {
    params: {
      initiator_id: initiatorId,
      target_id: targetId,
      agreement_type: agreementType,
    },
  });
  return response.data;
}

// ============================================================================
// SCENARIOS SYSTEM
// ============================================================================

// Get all available scenarios
export async function getScenarios(): Promise<{ scenarios: ScenarioSummary[]; total: number }> {
  const response = await api.get('/scenarios/');
  return response.data;
}

// Get scenario details
export async function getScenario(scenarioId: string): Promise<ScenarioDetail> {
  const response = await api.get(`/scenarios/${scenarioId}`);
  return response.data;
}

// Start a scenario
export async function startScenario(
  scenarioId: string,
  playerCountryId?: string
): Promise<ScenarioInitData> {
  const response = await api.post('/scenarios/start', {
    scenario_id: scenarioId,
    player_country_id: playerCountryId,
  });
  return response.data;
}

// Get objectives catalog
export async function getObjectivesCatalog(): Promise<{ objectives: ObjectiveSummary[]; total: number }> {
  const response = await api.get('/scenarios/objectives/catalog');
  return response.data;
}

// Get current scenario status
export interface ScenarioStatus {
  active: boolean;
  scenario_id: string | null;
  scenario_name: string | null;
  player_country: string | null;
  current_year: number;
  end_year: number | null;
  objectives: {
    id: string;
    name: string;
    description: string;
    type: string;
    points: number;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    progress: number;
  }[];
  total_score: number;
  max_possible_score: number;
  is_complete: boolean;
  is_failed: boolean;
}

export async function getScenarioStatus(): Promise<ScenarioStatus> {
  const response = await api.get('/scenarios/current/status');
  return response.data;
}

// Check objectives manually
export async function checkScenarioObjectives(): Promise<{
  checked: boolean;
  changes: string[];
  objectives: ScenarioStatus['objectives'];
  total_score: number;
  is_complete: boolean;
  is_failed: boolean;
}> {
  const response = await api.post('/scenarios/current/check-objectives');
  return response.data;
}

// End current scenario
export async function endScenario(): Promise<{
  ended: boolean;
  scenario_id: string;
  scenario_name: string;
  outcome: 'victory' | 'defeat' | 'incomplete';
  message: string;
  final_score: number;
  objectives: ScenarioStatus['objectives'];
  years_played: number;
}> {
  const response = await api.post('/scenarios/current/end');
  return response.data;
}

// ============================================================================
// REPLAY SYSTEM
// ============================================================================

import {
  ReplayMetadata,
  ReplayDetail,
  ReplaySummary,
  RecordingStatus,
} from './types';

// List all replays
export async function listReplays(): Promise<{ replays: ReplayMetadata[]; total: number }> {
  const response = await api.get('/replay/list');
  return response.data;
}

// Start recording
export async function startRecording(name: string, description?: string): Promise<{
  success: boolean;
  message: string;
  start_year: number;
}> {
  const response = await api.post('/replay/start', { name, description });
  return response.data;
}

// Stop recording and save replay
export async function stopRecording(): Promise<{
  success: boolean;
  message: string;
  replay_id: string;
  frames_count: number;
}> {
  const response = await api.post('/replay/stop');
  return response.data;
}

// Cancel recording without saving
export async function cancelRecording(): Promise<{
  success: boolean;
  message: string;
}> {
  const response = await api.post('/replay/cancel');
  return response.data;
}

// Get current recording status
export async function getRecordingStatus(): Promise<RecordingStatus> {
  const response = await api.get('/replay/status');
  return response.data;
}

// Get full replay with all frames
export async function getReplay(replayId: string): Promise<ReplayDetail> {
  const response = await api.get(`/replay/${replayId}`);
  return response.data;
}

// Get single frame
export async function getReplayFrame(replayId: string, frameIndex: number): Promise<{
  frame: Record<string, unknown>;
  total_frames: number;
  current_index: number;
}> {
  const response = await api.get(`/replay/${replayId}/frame/${frameIndex}`);
  return response.data;
}

// Delete replay
export async function deleteReplay(replayId: string): Promise<{
  success: boolean;
  message: string;
}> {
  const response = await api.delete(`/replay/${replayId}`);
  return response.data;
}

// Get replay summary
export async function getReplaySummary(replayId: string): Promise<ReplaySummary> {
  const response = await api.get(`/replay/${replayId}/summary`);
  return response.data;
}

// ============================================================================
// SCORING SYSTEM
// ============================================================================

import {
  CountryScores,
  RankingEntry,
  CategoryRankingEntry,
  ScoringCategory,
  ScoringSummary,
  CountryComparison,
} from './types';

// Get scores for a specific country (with fog of war for intelligence)
export async function getCountryScores(countryId: string, observerId?: string): Promise<CountryScores> {
  const params = observerId ? { observer: observerId } : {};
  const response = await api.get<CountryScores>(`/scoring/country/${countryId}`, { params });
  return response.data;
}

// Get intel quality between two countries
export async function getIntelQuality(observerId: string, targetId: string): Promise<{
  intel_score: number;
  intel_quality: string;
  visible_categories: Record<string, boolean>;
  nuclear_info: {
    status: string;
    display: string;
    display_fr: string;
    warheads: number | null;
    confidence: string;
  };
}> {
  const response = await api.get(`/scoring/intel/${observerId}/${targetId}`);
  return response.data;
}

// Get global rankings for all countries
export async function getGlobalRankings(): Promise<RankingEntry[]> {
  const response = await api.get<RankingEntry[]>('/scoring/rankings/global');
  return response.data;
}

// Get rankings for a specific category
export async function getCategoryRankings(category: string): Promise<CategoryRankingEntry[]> {
  const response = await api.get<CategoryRankingEntry[]>(`/scoring/rankings/${category}`);
  return response.data;
}

// Compare two countries
export async function compareCountries(
  countryId1: string,
  countryId2: string
): Promise<CountryComparison> {
  const response = await api.get<CountryComparison>(`/scoring/compare/${countryId1}/${countryId2}`);
  return response.data;
}

// Get world power summary
export async function getScoringSummary(): Promise<ScoringSummary> {
  const response = await api.get<ScoringSummary>('/scoring/summary');
  return response.data;
}

// Get information about all scoring categories
export async function getScoringCategories(): Promise<ScoringCategory[]> {
  const response = await api.get<ScoringCategory[]>('/scoring/categories');
  return response.data;
}

// ============================================================================
// STRATEGIC ADVICE
// ============================================================================

import {
  StrategicAdvice,
} from './types';

// Get strategic advice for a player country
export async function getStrategicAdvice(
  countryId: string,
  useOllama: boolean = true
): Promise<StrategicAdvice> {
  const response = await api.get<StrategicAdvice>(`/player/advice/${countryId}`, {
    params: { use_ollama: useOllama },
  });
  return response.data;
}

// Get comprehensive geopolitical analysis of the world
export async function getGeopoliticalAnalysis(): Promise<{
  year: number;
  global_tension: number;
  oil_price: number;
  power_distribution: Record<string, Array<{ id: string; name: string; power_score: number }>>;
  active_conflicts: Array<{ parties: string[]; power_balance: number }>;
  bloc_analysis: Record<string, { members: number; total_power: number; nuclear: boolean }>;
  hot_zones: Array<{ zone: string; dominant: string | null; contested_by: string[]; tension_factor: number }>;
  nuclear_powers: string[];
  defcon_level: number;
}> {
  const response = await api.get('/player/geopolitical');
  return response.data;
}

// ============================================================================
// AI ADVISOR SYSTEM
// ============================================================================

export interface AIStrategicAdvice {
  priority: string;
  category: string;
  title_fr: string;
  advice_fr: string;
  reasoning_fr: string;
  suggested_action?: string;
}

export interface AIDiplomaticDialogue {
  speaker_country: string;
  speaker_name: string;
  speaker_title: string;
  tone: string;
  message_fr: string;
  context: string;
}

export interface AIAnnualBriefing {
  year: number;
  executive_summary_fr: string;
  threats: Array<{ country: string; threat_level: string; description_fr: string }>;
  opportunities: Array<{ domain: string; description_fr: string }>;
  recommendations: string[];
}

export interface AIMediaComment {
  source: string;
  headline_fr: string;
  excerpt_fr: string;
  sentiment: string;
}

// Get AI strategic advice
export async function getAIStrategicAdvice(
  countryId: string,
  focus?: string
): Promise<{ success: boolean; advices: AIStrategicAdvice[]; error?: string }> {
  const response = await api.get(`/ai-advisor/advice/${countryId}`, {
    params: focus ? { focus } : {},
  });
  return response.data;
}

// Get AI diplomatic dialogue
export async function getAIDiplomaticDialogue(
  countryId: string,
  targetId: string,
  action: string = 'general',
  accepted?: boolean
): Promise<{ success: boolean; dialogue?: AIDiplomaticDialogue; error?: string }> {
  const response = await api.get(`/ai-advisor/dialogue/${countryId}/${targetId}`, {
    params: { action, ...(accepted !== undefined ? { accepted } : {}) },
  });
  return response.data;
}

// Get AI annual briefing
export async function getAIAnnualBriefing(
  countryId: string
): Promise<{ success: boolean; briefing?: AIAnnualBriefing; error?: string }> {
  const response = await api.get(`/ai-advisor/briefing/${countryId}`);
  return response.data;
}

// Get AI media comment
export async function getAIMediaComment(
  countryId: string
): Promise<{ success: boolean; comment?: AIMediaComment; error?: string }> {
  const response = await api.get(`/ai-advisor/media/${countryId}`);
  return response.data;
}

// Get AI opportunity event
export async function getAIOpportunityEvent(
  countryId: string
): Promise<{ success: boolean; event?: Record<string, unknown>; error?: string }> {
  const response = await api.get(`/ai-advisor/opportunity/${countryId}`);
  return response.data;
}

// Check AI advisor status
export async function getAIAdvisorStatus(): Promise<{
  available: boolean;
  model: string;
  url: string;
}> {
  const response = await api.get('/ai-advisor/status');
  return response.data;
}

// ============================================================================
// TIMELINE SYSTEM
// ============================================================================

import {
  GameDate,
  TimelineEvent,
  TimelineSummary,
  MonthlyTickResponse,
} from './types';

// Get current game date
export async function getCurrentDate(): Promise<{
  year: number;
  month: number;
  day: number;
  display: string;
  display_fr: string;
}> {
  const response = await api.get('/timeline/current-date');
  return response.data;
}

// Get timeline summary
export async function getTimelineSummary(): Promise<TimelineSummary> {
  const response = await api.get<TimelineSummary>('/timeline/summary');
  return response.data;
}

// Get timeline events with filters
export async function getTimelineEvents(params?: {
  start_year?: number;
  start_month?: number;
  end_year?: number;
  end_month?: number;
  types?: string[];
  importance_min?: number;
  limit?: number;
  offset?: number;
}): Promise<{ events: TimelineEvent[]; total: number }> {
  const response = await api.get('/timeline/events', { params });
  // Handle both array response (backend returns []) and object response
  const data = response.data;
  if (Array.isArray(data)) {
    return { events: data, total: data.length };
  }
  return data;
}

// Get events for a specific month
export async function getTimelineEventsByMonth(
  year: number,
  month: number
): Promise<{ events: TimelineEvent[]; year: number; month: number; count: number }> {
  const response = await api.get(`/timeline/events/month/${year}/${month}`);
  return response.data;
}

// Get events involving a specific country
export async function getTimelineEventsByCountry(
  countryId: string,
  limit?: number
): Promise<{ events: TimelineEvent[]; country_id: string; count: number }> {
  const response = await api.get(`/timeline/events/country/${countryId}`, {
    params: limit ? { limit } : {},
  });
  return response.data;
}

// Get a specific event by ID
export async function getTimelineEvent(eventId: string): Promise<TimelineEvent> {
  const response = await api.get<TimelineEvent>(`/timeline/event/${eventId}`);
  return response.data;
}

// Get event chain (cause and consequences)
export async function getEventChain(eventId: string): Promise<{
  event: TimelineEvent;
  caused_by: TimelineEvent | null;
  triggered: TimelineEvent[];
}> {
  const response = await api.get(`/timeline/event/${eventId}/chain`);
  return response.data;
}

// Get AI context from timeline
export async function getTimelineContext(lookbackMonths?: number): Promise<{
  current_date: string;
  recent_events: string;
  key_developments: string[];
  active_conflicts: string[];
  diplomatic_state: string;
}> {
  const response = await api.get('/timeline/context', {
    params: lookbackMonths ? { lookback_months: lookbackMonths } : {},
  });
  return response.data;
}

// Mark events as read
export async function markTimelineEventsRead(eventIds?: string[]): Promise<{
  marked_count: number;
  unread_remaining: number;
}> {
  const response = await api.post('/timeline/mark-read', {
    event_ids: eventIds,
  });
  return response.data;
}

// Get timeline statistics
export async function getTimelineStats(): Promise<{
  total_events: number;
  by_type: Record<string, number>;
  by_importance: Record<string, number>;
  by_source: Record<string, number>;
  unread_count: number;
  date_range: { start: string; end: string };
}> {
  const response = await api.get('/timeline/stats');
  return response.data;
}

// Advance one month (monthly tick)
export async function advanceMonth(): Promise<MonthlyTickResponse> {
  const response = await api.post<MonthlyTickResponse>('/tick');
  return response.data;
}

// Advance one full year (12 monthly ticks)
export async function advanceYear(): Promise<TickResponse> {
  const response = await api.post<TickResponse>('/tick/year');
  return response.data;
}

// ============================================================================
// Leaders API
// ============================================================================

// Get all world leaders
export async function getAllLeaders(): Promise<Record<string, Leader>> {
  const response = await api.get<{ leaders: Record<string, Leader> }>('/leaders');
  return response.data.leaders;
}

// Get leader for a specific country
export async function getLeader(countryId: string): Promise<Leader | null> {
  try {
    const response = await api.get<{ leader: Leader }>(`/leaders/${countryId}`);
    return response.data.leader;
  } catch {
    return null;
  }
}

// Get combined effects of leader's traits
export async function getLeaderTraitsEffects(countryId: string): Promise<Record<string, number>> {
  const response = await api.get<{ combined_effects: Record<string, number> }>(`/leaders/${countryId}/traits`);
  return response.data.combined_effects;
}

// Get leader's reaction to an event
export async function getLeaderReaction(countryId: string, eventType: string): Promise<string | null> {
  const response = await api.get<{ reaction: string | null }>(`/leaders/${countryId}/reaction/${eventType}`);
  return response.data.reaction;
}

// ============================================================================
// Stats History API
// ============================================================================

export interface HistoricalDataPoint {
  date: string;
  year: number;
  month: number;
  economy: number;
  military: number;
  technology: number;
  stability: number;
  soft_power: number;
  population: number;
  nuclear: number;
  resources: number;
  // World stats (when combined)
  global_tension?: number;
  reputation?: number;
  defcon_level?: number;
}

// Get historical stats for a country
export async function getCountryStatsHistory(countryId: string, limit?: number): Promise<HistoricalDataPoint[]> {
  const params = limit ? `?limit=${limit}` : '';
  const response = await api.get<{ history: HistoricalDataPoint[] }>(`/stats/history/${countryId}${params}`);
  return response.data.history;
}

// Get combined country + world stats history (for charts)
export async function getCombinedStatsHistory(countryId: string, limit?: number): Promise<HistoricalDataPoint[]> {
  const params = limit ? `?limit=${limit}` : '';
  const response = await api.get<{ history: HistoricalDataPoint[] }>(`/stats/history/${countryId}/combined${params}`);
  return response.data.history;
}

// Get world stats history
export async function getWorldStatsHistory(limit?: number): Promise<HistoricalDataPoint[]> {
  const params = limit ? `?limit=${limit}` : '';
  const response = await api.get<{ history: HistoricalDataPoint[] }>(`/stats/world${params}`);
  return response.data.history;
}

// Compare a metric across multiple countries
export async function compareCountriesStats(
  countryIds: string[],
  metric: string = 'economy',
  limit: number = 12
): Promise<{ metric: string; countries: Record<string, number[]>; dates: string[] }> {
  const response = await api.get<{ metric: string; countries: Record<string, number[]>; dates: string[] }>(
    `/stats/compare?countries=${countryIds.join(',')}&metric=${metric}&limit=${limit}`
  );
  return response.data;
}
