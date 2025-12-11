// Historia Lite - Game State Store (Zustand)
import { create } from 'zustand';
import {
  WorldState,
  Country,
  GameEvent,
  TickResponse,
  GameSettings,
  Tier4Country,
  Tier5Country,
  Tier6Country,
  Tier4Summary,
  Tier5Summary,
  Tier6Summary,
  SubnationalRegion,
  RegionsSummary,
  RegionAttackResult,
  CommandResponse,
  ActiveDilemma,
  TimelineEvent,
  GameDate,
  MonthlyTickResponse,
} from '@/lib/types';
import * as api from '@/lib/api';

interface GameStore {
  // State
  world: WorldState | null;
  selectedCountry: Country | null;
  isLoading: boolean;
  error: string | null;
  autoPlay: boolean;
  speed: number; // 1 = normal, 2 = fast, 3 = ultra

  // Timeline State (NEW)
  year: number;
  month: number;
  day: number;
  dateDisplay: string;
  dateDisplayFr: string;
  timeline: TimelineEvent[];
  timelineLoading: boolean;
  viewingDate: GameDate | null;  // Date being viewed in timeline modal (null = current)
  unreadEventCount: number;
  timelineModalOpen: boolean;

  // Tier 4/5/6 Countries
  tier4Countries: Tier4Country[];
  tier5Countries: Tier5Country[];
  tier6Countries: Tier6Country[];
  tier4Summary: Tier4Summary | null;
  tier5Summary: Tier5Summary | null;
  tier6Summary: Tier6Summary | null;

  // Subnational Regions
  regions: SubnationalRegion[];
  regionsSummary: RegionsSummary | null;
  selectedRegionId: string | null;

  // AI Settings
  settings: GameSettings | null;
  ollamaConnected: boolean;

  // Player State
  playerCountryId: string | null;
  pendingCommand: CommandResponse | null;
  pendingDilemmas: ActiveDilemma[];

  // Events State
  recentTickEvents: GameEvent[];
  eventHistory: GameEvent[];
  showEventToast: boolean;

  // Actions
  fetchWorldState: () => Promise<void>;
  selectCountry: (countryId: string | null) => void;
  advanceTick: () => Promise<TickResponse | null>;
  advanceMultipleTicks: (years: number) => Promise<void>;
  resetWorld: (seed?: number) => Promise<void>;
  setAutoPlay: (autoPlay: boolean) => void;
  setSpeed: (speed: number) => void;
  clearError: () => void;

  // Timeline Actions (NEW)
  advanceMonth: () => Promise<MonthlyTickResponse | null>;
  fetchTimeline: (params?: { year?: number; month?: number }) => Promise<void>;
  fetchTimelineForMonth: (year: number, month: number) => Promise<TimelineEvent[]>;
  setViewingDate: (date: GameDate | null) => void;
  goToPreviousMonth: () => void;
  goToNextMonth: () => Promise<void>;
  markEventsAsRead: (eventIds?: string[]) => Promise<void>;
  openTimelineModal: () => void;
  closeTimelineModal: () => void;
  getEventsForViewingMonth: () => TimelineEvent[];
  canGoBack: () => boolean;
  canGoForward: () => boolean;

  // Tier 4/5/6 Actions
  fetchTier4Countries: () => Promise<void>;
  fetchTier5Countries: () => Promise<void>;
  fetchTier6Countries: () => Promise<void>;
  fetchAllTiers: () => Promise<void>;

  // Region Actions
  fetchRegions: () => Promise<void>;
  fetchRegionsByCountry: (countryId: string) => Promise<void>;
  selectRegion: (regionId: string | null) => void;
  executeRegionAttack: (regionId: string, attackType: string, attackerId: string) => Promise<RegionAttackResult | null>;
  lastAttackResult: RegionAttackResult | null;

  // AI Actions
  fetchSettings: () => Promise<void>;
  setAiMode: (mode: 'algorithmic' | 'ollama') => Promise<void>;
  setOllamaModel: (model: string) => Promise<void>;

  // Player Actions
  selectPlayerCountry: (countryId: string) => Promise<void>;
  checkPlayerCountry: () => Promise<void>;
  sendPlayerCommand: (text: string) => Promise<CommandResponse | null>;
  confirmPlayerCommand: (cmdId: string) => Promise<void>;
  cancelPlayerCommand: () => void;
  fetchPendingDilemmas: () => Promise<void>;
  resolvePlayerDilemma: (dilemmaId: string, choiceId: number) => Promise<void>;
  advanceToNextEvent: () => Promise<void>;

  // Event Actions
  dismissEventToast: () => void;
  fetchEventHistory: (count?: number) => Promise<void>;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  world: null,
  selectedCountry: null,
  isLoading: false,
  error: null,
  autoPlay: false,
  speed: 1,

  // Tier 4/5/6 Countries
  tier4Countries: [],
  tier5Countries: [],
  tier6Countries: [],
  tier4Summary: null,
  tier5Summary: null,
  tier6Summary: null,

  // Subnational Regions
  regions: [],
  regionsSummary: null,
  selectedRegionId: null,
  lastAttackResult: null,

  // AI Settings
  settings: null,
  ollamaConnected: false,

  // Player State
  playerCountryId: null,
  pendingCommand: null,
  pendingDilemmas: [],

  // Events State
  recentTickEvents: [],
  eventHistory: [],
  showEventToast: false,

  // Fetch world state from API
  fetchWorldState: async () => {
    set({ isLoading: true, error: null });
    try {
      const world = await api.getWorldState();
      set({ world, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur de connexion au serveur',
        isLoading: false
      });
    }
  },

  // Select a country to view details
  selectCountry: (countryId: string | null) => {
    const { world } = get();
    if (!countryId || !world) {
      set({ selectedCountry: null });
      return;
    }
    const country = world.countries.find(c => c.id === countryId) || null;
    set({ selectedCountry: country });
  },

  // Advance simulation by one year
  advanceTick: async () => {
    const { settings, eventHistory } = get();
    set({ isLoading: true, error: null });
    try {
      // Use Ollama or algorithmic based on settings
      const result = settings?.ai_mode === 'ollama' && settings?.ollama_available
        ? await api.advanceTickWithOllama()
        : await api.advanceTick();

      // Store events from this tick
      const newEvents = result?.events || [];
      if (newEvents.length > 0) {
        set({
          recentTickEvents: newEvents,
          showEventToast: true,
          eventHistory: [...newEvents, ...eventHistory].slice(0, 100), // Keep last 100 events
        });
      }

      await get().fetchWorldState();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false
      });
      return null;
    }
  },

  // Advance simulation by multiple years
  advanceMultipleTicks: async (years: number) => {
    set({ isLoading: true, error: null });
    try {
      await api.advanceMultipleTicks(years);
      await get().fetchWorldState();
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false
      });
    }
  },

  // Reset world to initial state
  resetWorld: async (seed = 42) => {
    set({ isLoading: true, error: null, selectedCountry: null });
    try {
      await api.resetWorld(seed);
      await get().fetchWorldState();
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors du reset',
        isLoading: false
      });
    }
  },

  // Toggle auto-play mode
  setAutoPlay: (autoPlay: boolean) => set({ autoPlay }),

  // Set simulation speed
  setSpeed: (speed: number) => set({ speed }),

  // Clear error message
  clearError: () => set({ error: null }),

  // Fetch Tier 4 countries
  fetchTier4Countries: async () => {
    try {
      const [countries, summary] = await Promise.all([
        api.getTier4Countries(),
        api.getTier4Summary(),
      ]);
      set({ tier4Countries: countries, tier4Summary: summary });
    } catch (error) {
      // Silent fail - tier 4 data is optional
    }
  },

  // Fetch Tier 5 countries
  fetchTier5Countries: async () => {
    try {
      const [countries, summary] = await Promise.all([
        api.getTier5Countries(),
        api.getTier5Summary(),
      ]);
      set({ tier5Countries: countries, tier5Summary: summary });
    } catch (error) {
      // Silent fail - tier 5 data is optional
    }
  },

  // Fetch Tier 6 countries
  fetchTier6Countries: async () => {
    try {
      const [countries, summary] = await Promise.all([
        api.getTier6Countries(),
        api.getTier6Summary(),
      ]);
      set({ tier6Countries: countries, tier6Summary: summary });
    } catch (error) {
      // Silent fail - tier 6 data is optional
    }
  },

  // Fetch all tier data
  fetchAllTiers: async () => {
    const { fetchTier4Countries, fetchTier5Countries, fetchTier6Countries } = get();
    await Promise.all([
      fetchTier4Countries(),
      fetchTier5Countries(),
      fetchTier6Countries(),
    ]);
  },

  // Fetch all regions
  fetchRegions: async () => {
    try {
      const [regions, summary] = await Promise.all([
        api.getRegions(),
        api.getRegionsSummary(),
      ]);
      set({ regions, regionsSummary: summary });
    } catch (error) {
      // Silent fail - regions are optional
    }
  },

  // Fetch regions for a specific country
  fetchRegionsByCountry: async (countryId: string) => {
    try {
      const regions = await api.getRegionsByCountry(countryId);
      set({ regions });
    } catch (error) {
      // Silent fail
    }
  },

  // Select a region
  selectRegion: (regionId: string | null) => set({ selectedRegionId: regionId }),

  // Execute attack on a region
  executeRegionAttack: async (regionId: string, attackType: string, attackerId: string) => {
    set({ isLoading: true, error: null, lastAttackResult: null });
    try {
      const result = await api.executeRegionAttack(regionId, attackerId, attackType);
      set({ lastAttackResult: result, isLoading: false });
      // Refresh world state and regions after attack
      await get().fetchWorldState();
      await get().fetchRegions();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de l\'attaque',
        isLoading: false,
      });
      return null;
    }
  },

  // Fetch AI settings
  fetchSettings: async () => {
    try {
      const settings = await api.getSettings();
      set({ settings, ollamaConnected: settings.ollama_available });
    } catch (error) {
      // Silently fail - settings are optional
      set({ settings: null, ollamaConnected: false });
    }
  },

  // Set AI mode (algorithmic or ollama)
  setAiMode: async (mode: 'algorithmic' | 'ollama') => {
    try {
      const settings = await api.updateSettings({ ai_mode: mode });
      set({ settings, ollamaConnected: settings.ollama_available });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors du changement de mode IA'
      });
    }
  },

  // Set Ollama model
  setOllamaModel: async (model: string) => {
    try {
      const settings = await api.updateSettings({ ollama_model: model });
      set({ settings });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors du changement de modele'
      });
    }
  },

  // Select player country at game start
  selectPlayerCountry: async (countryId: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.selectPlayerCountry(countryId);
      set({ playerCountryId: countryId, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la selection du pays',
        isLoading: false
      });
    }
  },

  // Check if player has already selected a country
  checkPlayerCountry: async () => {
    try {
      const result = await api.getPlayerCountry();
      if (result.player_country_id) {
        set({ playerCountryId: result.player_country_id });
      }
    } catch (error) {
      // Silent fail - player may not have selected yet
    }
  },

  // Send a command in natural language
  sendPlayerCommand: async (text: string) => {
    const { playerCountryId } = get();
    if (!playerCountryId) return null;

    set({ isLoading: true, error: null });
    try {
      const result = await api.sendCommand(text, playerCountryId);
      set({ pendingCommand: result, isLoading: false });
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de l\'envoi de la commande',
        isLoading: false
      });
      return null;
    }
  },

  // Confirm pending command
  confirmPlayerCommand: async (cmdId: string) => {
    const { playerCountryId } = get();
    if (!playerCountryId) return;

    set({ isLoading: true, error: null });
    try {
      await api.confirmCommand(cmdId, playerCountryId);
      set({ pendingCommand: null, isLoading: false });
      await get().fetchWorldState();
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la confirmation',
        isLoading: false
      });
    }
  },

  // Cancel pending command
  cancelPlayerCommand: () => {
    set({ pendingCommand: null });
  },

  // Fetch pending dilemmas for player
  fetchPendingDilemmas: async () => {
    const { playerCountryId } = get();
    if (!playerCountryId) return;

    try {
      const result = await api.getPendingDilemmas(playerCountryId);
      set({ pendingDilemmas: result.pending_dilemmas || [] });
    } catch (error) {
      // Silent fail
    }
  },

  // Resolve a dilemma
  resolvePlayerDilemma: async (dilemmaId: string, choiceId: number) => {
    const { playerCountryId } = get();
    if (!playerCountryId) return;

    set({ isLoading: true, error: null });
    try {
      await api.resolveDilemma(dilemmaId, choiceId, playerCountryId);
      set({ isLoading: false });
      await get().fetchPendingDilemmas();
      await get().fetchWorldState();
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la resolution',
        isLoading: false
      });
    }
  },

  // Advance to next important event (not just 1 year)
  advanceToNextEvent: async () => {
    const { fetchPendingDilemmas, advanceTick } = get();
    set({ isLoading: true, error: null });

    try {
      // Advance tick by tick until an event occurs
      let hasEvent = false;
      let iterations = 0;
      const maxIterations = 10; // Safety limit

      while (!hasEvent && iterations < maxIterations) {
        const result = await advanceTick();
        iterations++;

        // Check if something interesting happened
        if (result && result.events && result.events.length > 0) {
          hasEvent = true;
        }

        // Also check for dilemmas
        await fetchPendingDilemmas();
        const { pendingDilemmas } = get();
        if (pendingDilemmas.length > 0) {
          hasEvent = true;
        }
      }

      set({ isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de l\'avance',
        isLoading: false
      });
    }
  },

  // Dismiss event toast
  dismissEventToast: () => {
    set({ showEventToast: false, recentTickEvents: [] });
  },

  // Fetch event history from API
  fetchEventHistory: async (count = 50) => {
    try {
      const events = await api.getEvents(count);
      set({ eventHistory: events });
    } catch (error) {
      // Silent fail - history is optional
    }
  },
}));
