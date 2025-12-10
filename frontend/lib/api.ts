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
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE,
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
  const response = await api.get<PendingDilemmasResponse>(
    `/dilemmas/${countryId}/pending`
  );
  return response.data;
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
