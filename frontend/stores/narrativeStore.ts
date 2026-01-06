/**
 * Zustand store for Historia Narrative mode (PaxHistoria-style)
 *
 * Manages:
 * - Game state (turn, phase, defcon, zones)
 * - Player state (political capital, stability, reputation)
 * - Parsed intentions and pending actions
 * - Turn resolution and events
 * - Adversary actions (visible ones)
 *
 * PaxHistoria additions:
 * - Action queue (accumulated before Jump Forward)
 * - Game phase: accumulating, jumping, playback
 * - Event playback with Save/Intervene
 */
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

// =============================================================================
// TYPES
// =============================================================================

export type TurnPhase =
  | "player_input"
  | "intent_review"
  | "action_confirm"
  | "diplomacy"
  | "adversary_turn"
  | "resolution"
  | "narrative";

// PaxHistoria game phases
export type GamePhase = "accumulating" | "jumping" | "playback";

// Queued action (PaxHistoria)
export interface QueuedAction {
  id: string;
  intention_type: string;
  intention_id: string;
  source_text: string;
  target_zone: string | null;
  target_actor: string | null;
  description_fr: string;
  description_en: string;
  political_cost: number;
  risk_level: string;
  predicted_effects: Record<string, number>;
  queued_at: string;
  priority: number;
  cancelled: boolean;
}

// Action queue summary
export interface QueueSummary {
  count: number;
  total_cost: number;
  remaining_capital: number;
  by_type: Record<string, number>;
  by_zone: Record<string, number>;
  risk_breakdown: Record<string, number>;
  has_high_risk: boolean;
}

// Narrative Scene - composee par le Chef d'Orchestre backend
export interface NarrativeSceneData {
  narrative: string;
  mood: string;  // neutral, tense, hopeful, dark, triumphant
  importance: string;  // minor, normal, major, critical

  // Elements optionnels - le Chef d'Orchestre decide
  leader_dialogue?: {
    speaker: string;
    title: string;
    tone: string;
    message: string;
    country?: string;
    portrait_style?: string;
  };
  press_headlines?: Array<{
    source: string;
    source_id: string;
    headline: string;
    excerpt: string;
    sentiment: string;
    bias: string;
    country: string;
    credibility: string;
  }>;
  intel_report?: {
    classification: string;
    content: string;
    reliability: string;
    source_type: string;
    analyst_note?: string;
  };
  causal_context?: {
    caused_by?: string;
    caused_by_date?: string;
    effects_preview?: string[];
    domino_zones?: string[];
  };
  consequence_teaser?: string;

  // Metadata
  year?: number;
  month?: number;
  zone?: string;
  zone_name_fr?: string;
  event_type?: string;

  // Flags
  is_player_caused?: boolean;
  is_crisis?: boolean;
  is_turning_point?: boolean;
}

// Jump event (for playback)
export interface JumpEvent {
  id: string;
  type: string;
  category: string;
  title_fr: string;
  description_fr: string;
  title_en: string;
  description_en: string;
  target_zone: string | null;
  target_actor: string | null;
  source: string;
  effects: Record<string, number | string>;
  importance: string;
  risk_level: string;
  caused_by: string | null;
  triggers: string[];

  // Scene narrative composee par le Chef d'Orchestre (optionnelle)
  narrative_scene?: NarrativeSceneData;
}

// Playback state
export interface PlaybackState {
  phase: string;
  total_events: number;
  current_index: number;
  current_event: JumpEvent | null;
  remaining: number;
  saved_at: number | null;
}

export interface Zone {
  id: string;
  name_fr: string;
  name_en: string;
  influence_us: number;
  influence_ussr: number;
  control_us: number;
  control_ussr_estimate: string;
  stability: number;
  strategic_value: number;
  dominant: "US" | "USSR" | "contested";
  instability_risk: string;
  has_crisis: boolean;
  crisis_type: string | null;
}

export interface PlayerState {
  political_capital: number;
  domestic_stability: number;
  international_reputation: number;
  intel_exposure: number;
  action_capacity: number;
}

export interface AdversaryVisible {
  known: boolean;
  economy_pressure?: string;
  doctrine_hint?: string;
  internal_pressure?: number;
}

export interface ParsedIntention {
  id: string;
  type: string;
  category: string;
  source_text: string;
  target_zone: string | null;
  target_country: string | null;
  topic: string | null;
  confidence: number;
  description_fr: string;
}

export interface PendingAction {
  id: string;
  intention_type: string;
  intention_id: string;
  target_zone: string | null;
  target_actor: string | null;
  description_fr: string;
  political_cost: number;
  risk_level: string;
  predicted_effects: Record<string, string>;
  confirmed: boolean;
}

export interface TurnResult {
  turn: number;
  date_display: string;
  player_actions_executed: Array<{
    id: string;
    type: string;
    result: string;
  }>;
  adversary_actions: Array<{
    type: string;
    target: string | null;
    visible: boolean;
    description_fr: string;
  }>;
  events: Array<{
    type: string;
    description_fr: string;
    zone?: string;
  }>;
  state_changes: Record<string, number | string>;
  narrative_summary_fr: string;
  game_over: boolean;
  victory: boolean | null;
  end_reason: string | null;
}

export interface DiplomacyResult {
  accepted: boolean;
  response_message_fr: string;
  effects: {
    trust: number;
    fear: number;
    respect: number;
    leverage: number;
  };
}

export interface NarrativeState {
  // Connection
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;

  // Game state
  year: number;
  month: number;
  turn: number;
  date_display: string;
  current_phase: TurnPhase;
  defcon: number;
  world_tension: number;

  // PaxHistoria: Game phase
  gamePhase: GamePhase;

  // Player
  player: PlayerState & { available_capital?: number };

  // Adversary (visible info only)
  adversary: AdversaryVisible;

  // Zones
  zones: Record<string, Zone>;

  // Current turn state (legacy)
  inputText: string;
  parsedIntentions: ParsedIntention[];
  pendingActions: PendingAction[];
  selectedIntentions: string[];
  selectedActions: string[];

  // PaxHistoria: Action queue
  actionQueue: QueuedAction[];
  queueSummary: QueueSummary | null;

  // PaxHistoria: Playback
  playbackState: PlaybackState | null;
  jumpEvents: JumpEvent[];
  currentEventIndex: number;

  // Turn results
  lastTurnResult: TurnResult | null;
  turnHistory: TurnResult[];

  // Events queue
  events: Array<{ type: string; description_fr: string }>;

  // Game end
  gameOver: boolean;
  victory: boolean | null;
  endReason: string | null;

  // Legacy actions
  setInputText: (text: string) => void;
  parseInput: () => Promise<void>;
  selectIntention: (id: string) => void;
  deselectIntention: (id: string) => void;
  generateActions: () => Promise<void>;
  selectAction: (id: string) => void;
  deselectAction: (id: string) => void;
  confirmActions: () => Promise<void>;
  sendDiplomacy: (
    target: string,
    message: string,
    tone: string
  ) => Promise<DiplomacyResult | null>;
  collectIntel: (target: string, depth: string) => Promise<void>;
  newGame: () => Promise<void>;
  loadState: () => Promise<void>;
  reset: () => void;

  // PaxHistoria actions
  queueAction: (action: Partial<QueuedAction>) => Promise<boolean>;
  removeFromQueue: (actionId: string) => Promise<boolean>;
  clearQueue: () => void;
  jumpForward: (duration: string) => Promise<boolean>;
  nextEvent: () => Promise<JumpEvent | null>;
  saveHere: () => Promise<void>;
  intervene: () => Promise<void>;
}

// =============================================================================
// API HELPERS
// =============================================================================

const API_BASE = "/api/narrative";

async function apiCall<T>(
  endpoint: string,
  method: string = "GET",
  body?: unknown
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `API error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// INITIAL STATE
// =============================================================================

const initialState = {
  isConnected: false,
  isLoading: false,
  error: null,

  year: 1962,
  month: 10,
  turn: 1,
  date_display: "Octobre 1962",
  current_phase: "player_input" as TurnPhase,
  defcon: 3,
  world_tension: 65,

  // PaxHistoria
  gamePhase: "accumulating" as GamePhase,

  player: {
    political_capital: 70,
    domestic_stability: 65,
    international_reputation: 70,
    intel_exposure: 20,
    action_capacity: 3,
    available_capital: 70,
  },

  adversary: {
    known: true,
  },

  zones: {},

  inputText: "",
  parsedIntentions: [],
  pendingActions: [],
  selectedIntentions: [],
  selectedActions: [],

  // PaxHistoria: Action queue
  actionQueue: [] as QueuedAction[],
  queueSummary: null as QueueSummary | null,

  // PaxHistoria: Playback
  playbackState: null as PlaybackState | null,
  jumpEvents: [] as JumpEvent[],
  currentEventIndex: 0,

  lastTurnResult: null,
  turnHistory: [],

  events: [],

  gameOver: false,
  victory: null,
  endReason: null,
};

// =============================================================================
// STORE
// =============================================================================

export const useNarrativeStore = create<NarrativeState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // ---------------------------------------------------------------------
        // INPUT
        // ---------------------------------------------------------------------

        setInputText: (text: string) => {
          set({ inputText: text });
        },

        // ---------------------------------------------------------------------
        // PARSE
        // ---------------------------------------------------------------------

        parseInput: async () => {
          const { inputText } = get();
          if (!inputText.trim()) return;

          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<{
              intentions: ParsedIntention[];
              unrecognized: string[];
              warnings: string[];
            }>("/parse", "POST", { text: inputText, use_ollama: true });

            set({
              parsedIntentions: response.intentions,
              selectedIntentions: response.intentions.map((i) => i.id),
              current_phase: "intent_review",
              isLoading: false,
            });

            if (response.warnings.length > 0) {
              console.warn("Parse warnings:", response.warnings);
            }
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Parse failed",
            });
          }
        },

        // ---------------------------------------------------------------------
        // INTENTIONS
        // ---------------------------------------------------------------------

        selectIntention: (id: string) => {
          const { selectedIntentions } = get();
          if (!selectedIntentions.includes(id)) {
            set({ selectedIntentions: [...selectedIntentions, id] });
          }
        },

        deselectIntention: (id: string) => {
          const { selectedIntentions } = get();
          set({
            selectedIntentions: selectedIntentions.filter((i) => i !== id),
          });
        },

        // ---------------------------------------------------------------------
        // ACTIONS
        // ---------------------------------------------------------------------

        generateActions: async () => {
          const { selectedIntentions, parsedIntentions, player } = get();
          if (selectedIntentions.length === 0) return;

          set({ isLoading: true, error: null });

          try {
            // Generate actions for selected intentions
            const actions: PendingAction[] = [];
            let totalCost = 0;

            for (const intentId of selectedIntentions) {
              const intent = parsedIntentions.find((i) => i.id === intentId);
              if (!intent) continue;

              // Create action from intention
              const action: PendingAction = {
                id: `action_${intentId}`,
                intention_type: intent.type,
                intention_id: intent.id,
                target_zone: intent.target_zone,
                target_actor: intent.target_country,
                description_fr: intent.description_fr,
                political_cost: getCostForType(intent.type),
                risk_level: getRiskForType(intent.type),
                predicted_effects: {},
                confirmed: false,
              };

              actions.push(action);
              totalCost += action.political_cost;
            }

            const warnings: string[] = [];
            if (totalCost > player.political_capital) {
              warnings.push(
                `Capital insuffisant: ${player.political_capital}/${totalCost}`
              );
            }

            set({
              pendingActions: actions,
              selectedActions: actions.map((a) => a.id),
              current_phase: "action_confirm",
              isLoading: false,
            });
          } catch (error) {
            set({
              isLoading: false,
              error:
                error instanceof Error ? error.message : "Generate actions failed",
            });
          }
        },

        selectAction: (id: string) => {
          const { selectedActions } = get();
          if (!selectedActions.includes(id)) {
            set({ selectedActions: [...selectedActions, id] });
          }
        },

        deselectAction: (id: string) => {
          const { selectedActions } = get();
          set({
            selectedActions: selectedActions.filter((a) => a !== id),
          });
        },

        // ---------------------------------------------------------------------
        // CONFIRM TURN
        // ---------------------------------------------------------------------

        confirmActions: async () => {
          const { selectedActions } = get();
          if (selectedActions.length === 0) return;

          set({ isLoading: true, error: null, current_phase: "adversary_turn" });

          try {
            const response = await apiCall<TurnResult>("/confirm", "POST", {
              action_ids: selectedActions,
            });

            // Update state from response
            set((state) => ({
              lastTurnResult: response,
              turnHistory: [...state.turnHistory, response],
              turn: response.turn,
              date_display: response.date_display,
              gameOver: response.game_over,
              victory: response.victory,
              endReason: response.end_reason,
              current_phase: response.game_over ? "narrative" : "player_input",
              isLoading: false,

              // Clear turn state
              inputText: "",
              parsedIntentions: [],
              pendingActions: [],
              selectedIntentions: [],
              selectedActions: [],
            }));

            // Reload full state
            await get().loadState();
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Confirm failed",
            });
          }
        },

        // ---------------------------------------------------------------------
        // DIPLOMACY
        // ---------------------------------------------------------------------

        sendDiplomacy: async (
          target: string,
          message: string,
          tone: string
        ): Promise<DiplomacyResult | null> => {
          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<DiplomacyResult>(
              "/diplomacy",
              "POST",
              {
                target,
                message,
                tone,
              }
            );

            set({ isLoading: false });
            return response;
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Diplomacy failed",
            });
            return null;
          }
        },

        // ---------------------------------------------------------------------
        // INTEL
        // ---------------------------------------------------------------------

        collectIntel: async (target: string, depth: string) => {
          set({ isLoading: true, error: null });

          try {
            await apiCall(`/intel/${target}?depth=${depth}`, "POST");
            await get().loadState();
            set({ isLoading: false });
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Intel failed",
            });
          }
        },

        // ---------------------------------------------------------------------
        // GAME MANAGEMENT
        // ---------------------------------------------------------------------

        newGame: async () => {
          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<{ state: NarrativeAPIState }>(
              "/new",
              "POST",
              {
                scenario: "cuban_missile_crisis",
                difficulty: "normal",
              }
            );

            updateFromAPIState(set, response.state);
            set({ isLoading: false, isConnected: true });
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "New game failed",
            });
          }
        },

        loadState: async () => {
          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<{ state: NarrativeAPIState }>(
              "/state"
            );
            updateFromAPIState(set, response.state);
            set({ isLoading: false, isConnected: true });
          } catch (error) {
            set({
              isLoading: false,
              isConnected: false,
              error: error instanceof Error ? error.message : "Load state failed",
            });
          }
        },

        reset: () => {
          set(initialState);
        },

        // ---------------------------------------------------------------------
        // PAXHISTORIA: ACTION QUEUE
        // ---------------------------------------------------------------------

        queueAction: async (action: Partial<QueuedAction>): Promise<boolean> => {
          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<{
              success: boolean;
              message: string;
              action_id: string | null;
              queue_summary: QueueSummary;
            }>("/queue-action", "POST", action);

            if (response.success) {
              // Reload state to get updated queue
              await get().loadState();
            }

            set({
              isLoading: false,
              queueSummary: response.queue_summary,
              error: response.success ? null : response.message,
            });

            return response.success;
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Queue action failed",
            });
            return false;
          }
        },

        removeFromQueue: async (actionId: string): Promise<boolean> => {
          set({ isLoading: true, error: null });

          try {
            const response = await apiCall<{
              success: boolean;
              message: string;
              queue_summary: QueueSummary;
            }>(`/queue-action/${actionId}`, "DELETE");

            if (response.success) {
              await get().loadState();
            }

            set({
              isLoading: false,
              queueSummary: response.queue_summary,
            });

            return response.success;
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Remove failed",
            });
            return false;
          }
        },

        clearQueue: () => {
          set({
            actionQueue: [],
            queueSummary: null,
          });
        },

        // ---------------------------------------------------------------------
        // PAXHISTORIA: JUMP FORWARD
        // ---------------------------------------------------------------------

        jumpForward: async (duration: string): Promise<boolean> => {
          set({ isLoading: true, error: null, gamePhase: "jumping" });

          try {
            const response = await apiCall<{
              success: boolean;
              events_count: number;
              first_event: JumpEvent | null;
              game_phase: string;
            }>("/jump-forward", "POST", { duration });

            if (response.success) {
              set({
                gamePhase: response.game_phase as GamePhase,
                isLoading: false,
              });

              // Load full state including events
              await get().loadState();
              return true;
            }

            set({ isLoading: false, gamePhase: "accumulating" });
            return false;
          } catch (error) {
            set({
              isLoading: false,
              gamePhase: "accumulating",
              error: error instanceof Error ? error.message : "Jump failed",
            });
            return false;
          }
        },

        // ---------------------------------------------------------------------
        // PAXHISTORIA: EVENT PLAYBACK
        // ---------------------------------------------------------------------

        nextEvent: async (): Promise<JumpEvent | null> => {
          try {
            const response = await apiCall<{
              event: JumpEvent | null;
              index: number;
              total: number;
              remaining: number;
              can_save: boolean;
              can_intervene: boolean;
            }>("/event/next", "POST");

            set({
              currentEventIndex: response.index,
              playbackState: {
                phase: "playback",
                total_events: response.total,
                current_index: response.index,
                current_event: response.event,
                remaining: response.remaining,
                saved_at: null,
              },
            });

            // If no more events, reload state
            if (!response.event) {
              await get().loadState();
            }

            return response.event;
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : "Next event failed",
            });
            return null;
          }
        },

        saveHere: async () => {
          try {
            await apiCall("/event/save", "POST");
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : "Save failed",
            });
          }
        },

        intervene: async () => {
          set({ isLoading: true });

          try {
            const response = await apiCall<{
              success: boolean;
              cancelled_events_count: number;
              game_phase: string;
            }>("/event/intervene", "POST");

            set({
              gamePhase: response.game_phase as GamePhase,
              isLoading: false,
            });

            // Reload state
            await get().loadState();
          } catch (error) {
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : "Intervene failed",
            });
          }
        },
      }),
      {
        name: "narrative-storage",
        partialize: (state) => ({
          turnHistory: state.turnHistory,
        }),
      }
    ),
    { name: "NarrativeStore" }
  )
);

// =============================================================================
// HELPERS
// =============================================================================

interface NarrativeAPIState {
  year: number;
  month: number;
  turn: number;
  date_display: string;
  current_phase: string;
  game_phase: string;
  defcon: number;
  world_tension: number;
  player: PlayerState & { available_capital?: number };
  adversary: AdversaryVisible;
  zones: Record<string, Zone>;
  pending_actions: PendingAction[];
  action_queue?: {
    actions: QueuedAction[];
    summary: QueueSummary;
  };
  playback?: PlaybackState | null;
  game_over: boolean;
  victory: boolean | null;
  end_reason: string | null;
}

function updateFromAPIState(
  set: (partial: Partial<NarrativeState>) => void,
  state: NarrativeAPIState
) {
  set({
    year: state.year,
    month: state.month,
    turn: state.turn,
    date_display: state.date_display,
    current_phase: state.current_phase as TurnPhase,
    gamePhase: (state.game_phase || "accumulating") as GamePhase,
    defcon: state.defcon,
    world_tension: state.world_tension,
    player: state.player,
    adversary: state.adversary,
    zones: state.zones,
    pendingActions: state.pending_actions || [],
    actionQueue: state.action_queue?.actions || [],
    queueSummary: state.action_queue?.summary || null,
    playbackState: state.playback || null,
    gameOver: state.game_over,
    victory: state.victory,
    endReason: state.end_reason,
  });
}

function getCostForType(type: string): number {
  const costs: Record<string, number> = {
    DIPLO_ALLIANCE: 10,
    DIPLO_THREAT: 15,
    DIPLO_NEGOTIATE: 5,
    DIPLO_CONCEDE: 20,
    DIPLO_SANCTION: 15,
    DIPLO_SUMMIT: 10,
    DIPLO_BACKCHANNEL: 5,
    MIL_REINFORCE: 20,
    MIL_WITHDRAW: 10,
    MIL_DEMO: 15,
    MIL_PROXY: 25,
    MIL_BLOCKADE: 30,
    MIL_BASE: 25,
    COV_DESTAB: 20,
    COV_COUP: 35,
    COV_SABOTAGE: 25,
    COV_ASSASSIN: 40,
    COV_PROPAGANDA: 10,
    INTEL_COLLECT: 10,
    INTEL_VERIFY: 5,
    INTEL_COUNTER: 15,
    INTEL_DISINFO: 15,
    ECO_AID: 15,
    ECO_TRADE: 10,
    ECO_EMBARGO: 20,
    ECO_INVEST: 20,
    DOM_SPEECH: 5,
    DOM_REFORM: 25,
    DOM_REPRESS: 15,
    DOM_ELECTION: 20,
  };
  return costs[type] || 10;
}

function getRiskForType(type: string): string {
  const risks: Record<string, string> = {
    DIPLO_ALLIANCE: "low",
    DIPLO_THREAT: "medium",
    DIPLO_NEGOTIATE: "low",
    DIPLO_CONCEDE: "low",
    DIPLO_SANCTION: "medium",
    DIPLO_SUMMIT: "low",
    DIPLO_BACKCHANNEL: "medium",
    MIL_REINFORCE: "medium",
    MIL_WITHDRAW: "low",
    MIL_DEMO: "medium",
    MIL_PROXY: "high",
    MIL_BLOCKADE: "high",
    MIL_BASE: "medium",
    COV_DESTAB: "high",
    COV_COUP: "extreme",
    COV_SABOTAGE: "high",
    COV_ASSASSIN: "extreme",
    COV_PROPAGANDA: "low",
    INTEL_COLLECT: "medium",
    INTEL_VERIFY: "low",
    INTEL_COUNTER: "low",
    INTEL_DISINFO: "medium",
    ECO_AID: "low",
    ECO_TRADE: "low",
    ECO_EMBARGO: "medium",
    ECO_INVEST: "low",
    DOM_SPEECH: "low",
    DOM_REFORM: "medium",
    DOM_REPRESS: "medium",
    DOM_ELECTION: "medium",
  };
  return risks[type] || "medium";
}

// =============================================================================
// SELECTORS
// =============================================================================

export const selectCanConfirm = (state: NarrativeState): boolean => {
  if (state.selectedActions.length === 0) return false;
  if (state.isLoading) return false;
  if (state.gameOver) return false;

  // Check cost
  const totalCost = state.pendingActions
    .filter((a) => state.selectedActions.includes(a.id))
    .reduce((sum, a) => sum + a.political_cost, 0);

  return totalCost <= state.player.political_capital;
};

export const selectTotalActionCost = (state: NarrativeState): number => {
  return state.pendingActions
    .filter((a) => state.selectedActions.includes(a.id))
    .reduce((sum, a) => sum + a.political_cost, 0);
};

export const selectDefconStatus = (
  state: NarrativeState
): { level: number; label: string; color: string } => {
  const statuses: Record<number, { label: string; color: string }> = {
    5: { label: "Paix relative", color: "green" },
    4: { label: "Tensions elevees", color: "yellow" },
    3: { label: "Crise majeure", color: "orange" },
    2: { label: "Confrontation imminente", color: "red" },
    1: { label: "Guerre imminente", color: "darkred" },
  };

  return {
    level: state.defcon,
    ...statuses[state.defcon],
  };
};

export const selectZonesByDominance = (
  state: NarrativeState
): { us: Zone[]; ussr: Zone[]; contested: Zone[] } => {
  const zones = Object.values(state.zones);
  return {
    us: zones.filter((z) => z.dominant === "US"),
    ussr: zones.filter((z) => z.dominant === "USSR"),
    contested: zones.filter((z) => z.dominant === "contested"),
  };
};
