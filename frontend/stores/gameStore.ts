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
  DailyTickResponse,
  AutoAdvanceConfig,
  AutoAdvanceResponse,
  PauseReason,
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

  // Timeline State (NEW - Daily progression)
  year: number;
  month: number;
  day: number;
  dateDisplay: string;         // "January 2025" (month only for compatibility)
  dateDisplayFr: string;       // "Janvier 2025"
  dateDisplayFull: string;     // "January 15, 2025" (full date)
  dateDisplayFullFr: string;   // "15 Janvier 2025"
  timeline: TimelineEvent[];
  timelineLoading: boolean;
  viewingDate: GameDate | null;  // Date being viewed in timeline modal (null = current)
  unreadEventCount: number;
  timelineModalOpen: boolean;

  // Auto-advance State
  autoAdvanceConfig: AutoAdvanceConfig;
  isAutoAdvancing: boolean;
  lastPauseReason: PauseReason | null;
  lastPauseMessage: string | null;

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

  // Breaking News State
  breakingNewsEvent: GameEvent | null;
  showBreakingNews: boolean;

  // Actions
  fetchWorldState: () => Promise<void>;
  selectCountry: (countryId: string | null) => void;
  advanceTick: () => Promise<TickResponse | null>;
  advanceMultipleTicks: (years: number) => Promise<void>;
  resetWorld: (seed?: number) => Promise<void>;
  setAutoPlay: (autoPlay: boolean) => void;
  setSpeed: (speed: number) => void;
  clearError: () => void;

  // Timeline Actions (NEW - Daily progression)
  advanceDay: () => Promise<DailyTickResponse | null>;
  advanceWeek: () => Promise<AutoAdvanceResponse | null>;
  advanceMonth: () => Promise<MonthlyTickResponse | null>;
  advanceMonthDays: () => Promise<AutoAdvanceResponse | null>;
  advanceToNextImportantEvent: () => Promise<AutoAdvanceResponse | null>;
  autoAdvance: (config?: Partial<AutoAdvanceConfig>) => Promise<AutoAdvanceResponse | null>;
  setAutoAdvanceConfig: (config: Partial<AutoAdvanceConfig>) => void;
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

  // Breaking News Actions
  dismissBreakingNews: () => void;
  triggerBreakingNews: (event: GameEvent) => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  world: null,
  selectedCountry: null,
  isLoading: false,
  error: null,
  autoPlay: false,
  speed: 1,

  // Timeline State (NEW - Daily progression)
  year: 2025,
  month: 1,
  day: 1,
  dateDisplay: 'January 2025',
  dateDisplayFr: 'Janvier 2025',
  dateDisplayFull: 'January 1, 2025',
  dateDisplayFullFr: '1 Janvier 2025',
  timeline: [],
  timelineLoading: false,
  viewingDate: null,
  unreadEventCount: 0,
  timelineModalOpen: false,

  // Auto-advance State
  autoAdvanceConfig: {
    pause_on_war: true,
    pause_on_crisis: true,
    pause_on_defcon_change: true,
    pause_on_nuclear: true,
    pause_on_player_attacked: true,
    pause_on_player_mentioned: true,
    min_event_importance: 4,
    watch_countries: [],
    days_per_batch: 7,
    max_days: 180,
  },
  isAutoAdvancing: false,
  lastPauseReason: null,
  lastPauseMessage: null,

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

  // Breaking News State
  breakingNewsEvent: null,
  showBreakingNews: false,

  // Fetch world state from API
  fetchWorldState: async () => {
    set({ isLoading: true, error: null });
    try {
      const world = await api.getWorldState();
      // Extract timeline data from world state
      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];
      const year = world.year || 2025;
      const month = (world as { month?: number }).month || 1;
      set({
        world,
        year,
        month,
        day: 1,
        dateDisplay: `${monthNames[month - 1]} ${year}`,
        dateDisplayFr: `${monthNamesFr[month - 1]} ${year}`,
        unreadEventCount: (world as { unread_events?: number }).unread_events || 0,
        isLoading: false
      });
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

  // =========================================================================
  // TIMELINE ACTIONS (NEW - Daily Progression)
  // =========================================================================

  // Helper to format full date
  _formatFullDate: (year: number, month: number, day: number, lang: 'en' | 'fr' = 'fr') => {
    const monthNamesEn = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const monthNamesFr = [
      'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
    ];
    if (lang === 'en') {
      return `${monthNamesEn[month - 1]} ${day}, ${year}`;
    }
    return `${day} ${monthNamesFr[month - 1]} ${year}`;
  },

  // Advance simulation by one day
  advanceDay: async () => {
    const { timeline, eventHistory, triggerBreakingNews } = get();
    set({ isLoading: true, error: null });
    try {
      const result = await api.advanceDay();

      // Check for breaking news worthy events
      const breakingNewsTypes = [
        'war', 'conflict', 'attack', 'nuclear', 'coup',
        'political_crisis', 'ally_under_attack', 'diplomatic_crisis',
        'defcon_change', 'bloc_change', 'major_sanctions', 'revolution'
      ];

      const criticalEvents = (result.events || []).filter((e: GameEvent) => {
        const typeLower = e.type.toLowerCase();
        return breakingNewsTypes.some(t => typeLower.includes(t));
      });

      if (criticalEvents.length > 0) {
        const priorityEvent = criticalEvents.find((e: GameEvent) =>
          e.type.toLowerCase().includes('war') ||
          e.type.toLowerCase().includes('nuclear') ||
          e.type.toLowerCase().includes('attack')
        ) || criticalEvents[0];
        triggerBreakingNews(priorityEvent);
      }

      // Update state with daily result
      const monthNamesEn = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: result.year,
        month: result.month,
        day: result.day,
        dateDisplay: `${monthNamesEn[result.month - 1]} ${result.year}`,
        dateDisplayFr: `${monthNamesFr[result.month - 1]} ${result.year}`,
        dateDisplayFull: result.date_display_full || `${monthNamesEn[result.month - 1]} ${result.day}, ${result.year}`,
        dateDisplayFullFr: result.date_display_full_fr || `${result.day} ${monthNamesFr[result.month - 1]} ${result.year}`,
        recentTickEvents: result.events || [],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...(result.events || []), ...eventHistory].slice(0, 100),
        isLoading: false,
      });

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

  // Advance simulation by one week (7 days)
  advanceWeek: async () => {
    const { timeline, eventHistory, triggerBreakingNews, autoAdvanceConfig } = get();
    set({ isLoading: true, isAutoAdvancing: true, error: null });
    try {
      const result = await api.advanceWeek();

      // Handle pause reason if any
      if (result.paused && result.pause_reason) {
        set({
          lastPauseReason: result.pause_reason as PauseReason,
          lastPauseMessage: result.pause_message_fr || result.pause_message || null,
        });

        // Trigger breaking news for pause events
        if (result.events && result.events.length > 0) {
          const lastEvent = result.events[result.events.length - 1];
          if (lastEvent) {
            triggerBreakingNews(lastEvent as GameEvent);
          }
        }
      }

      // Parse final date
      const [year, month, day] = (result.final_date || '2025-01-01').split('-').map(Number);
      const monthNamesEn = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: year || 2025,
        month: month || 1,
        day: day || 1,
        dateDisplay: `${monthNamesEn[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFr: `${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFull: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFullFr: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        recentTickEvents: (result.events || []) as GameEvent[],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...((result.events || []) as GameEvent[]), ...eventHistory].slice(0, 100),
        isLoading: false,
        isAutoAdvancing: false,
      });

      await get().fetchWorldState();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false,
        isAutoAdvancing: false,
      });
      return null;
    }
  },

  // Advance simulation by approximately one month (30 days) using daily system
  advanceMonthDays: async () => {
    const { eventHistory, triggerBreakingNews } = get();
    set({ isLoading: true, isAutoAdvancing: true, error: null });
    try {
      const result = await api.advanceMonthDays();

      // Handle pause
      if (result.paused && result.pause_reason) {
        set({
          lastPauseReason: result.pause_reason as PauseReason,
          lastPauseMessage: result.pause_message_fr || result.pause_message || null,
        });

        if (result.events && result.events.length > 0) {
          const lastEvent = result.events[result.events.length - 1];
          if (lastEvent) {
            triggerBreakingNews(lastEvent as GameEvent);
          }
        }
      }

      // Parse final date
      const [year, month, day] = (result.final_date || '2025-01-01').split('-').map(Number);
      const monthNamesEn = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: year || 2025,
        month: month || 1,
        day: day || 1,
        dateDisplay: `${monthNamesEn[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFr: `${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFull: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFullFr: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        recentTickEvents: (result.events || []) as GameEvent[],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...((result.events || []) as GameEvent[]), ...eventHistory].slice(0, 100),
        isLoading: false,
        isAutoAdvancing: false,
      });

      await get().fetchWorldState();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false,
        isAutoAdvancing: false,
      });
      return null;
    }
  },

  // Advance until next important event
  advanceToNextImportantEvent: async () => {
    const { eventHistory, triggerBreakingNews } = get();
    set({ isLoading: true, isAutoAdvancing: true, error: null });
    try {
      const result = await api.advanceToEvent();

      // Always handle pause for this mode
      if (result.pause_reason) {
        set({
          lastPauseReason: result.pause_reason as PauseReason,
          lastPauseMessage: result.pause_message_fr || result.pause_message || null,
        });
      }

      // Trigger breaking news
      if (result.events && result.events.length > 0) {
        const lastEvent = result.events[result.events.length - 1];
        if (lastEvent) {
          triggerBreakingNews(lastEvent as GameEvent);
        }
      }

      // Parse final date
      const [year, month, day] = (result.final_date || '2025-01-01').split('-').map(Number);
      const monthNamesEn = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: year || 2025,
        month: month || 1,
        day: day || 1,
        dateDisplay: `${monthNamesEn[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFr: `${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFull: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFullFr: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        recentTickEvents: (result.events || []) as GameEvent[],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...((result.events || []) as GameEvent[]), ...eventHistory].slice(0, 100),
        isLoading: false,
        isAutoAdvancing: false,
      });

      await get().fetchWorldState();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false,
        isAutoAdvancing: false,
      });
      return null;
    }
  },

  // Auto-advance with custom configuration
  autoAdvance: async (config?: Partial<AutoAdvanceConfig>) => {
    const { autoAdvanceConfig, eventHistory, triggerBreakingNews } = get();
    const finalConfig = { ...autoAdvanceConfig, ...config };
    set({ isLoading: true, isAutoAdvancing: true, error: null });
    try {
      const result = await api.autoAdvance(finalConfig);

      // Handle pause
      if (result.pause_reason) {
        set({
          lastPauseReason: result.pause_reason as PauseReason,
          lastPauseMessage: result.pause_message_fr || result.pause_message || null,
        });
      }

      // Trigger breaking news
      if (result.events && result.events.length > 0) {
        const lastEvent = result.events[result.events.length - 1];
        if (lastEvent) {
          triggerBreakingNews(lastEvent as GameEvent);
        }
      }

      // Parse final date
      const [year, month, day] = (result.final_date || '2025-01-01').split('-').map(Number);
      const monthNamesEn = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: year || 2025,
        month: month || 1,
        day: day || 1,
        dateDisplay: `${monthNamesEn[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFr: `${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFull: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        dateDisplayFullFr: result.final_date_fr || `${(day || 1)} ${monthNamesFr[(month || 1) - 1]} ${year || 2025}`,
        recentTickEvents: (result.events || []) as GameEvent[],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...((result.events || []) as GameEvent[]), ...eventHistory].slice(0, 100),
        isLoading: false,
        isAutoAdvancing: false,
      });

      await get().fetchWorldState();
      return result;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Erreur lors de la simulation',
        isLoading: false,
        isAutoAdvancing: false,
      });
      return null;
    }
  },

  // Update auto-advance configuration
  setAutoAdvanceConfig: (config: Partial<AutoAdvanceConfig>) => {
    const { autoAdvanceConfig } = get();
    set({ autoAdvanceConfig: { ...autoAdvanceConfig, ...config } });
  },

  // Advance simulation by one month (legacy - uses monthly tick)
  advanceMonth: async () => {
    const { timeline, eventHistory, triggerBreakingNews } = get();
    set({ isLoading: true, error: null });
    try {
      const result = await api.advanceMonth();

      // Check for breaking news worthy events
      const breakingNewsTypes = [
        'war', 'conflict', 'attack', 'nuclear', 'coup',
        'political_crisis', 'ally_under_attack', 'diplomatic_crisis',
        'defcon_change', 'bloc_change', 'major_sanctions', 'revolution'
      ];

      const criticalEvents = (result.events || []).filter((e: GameEvent) => {
        const typeLower = e.type.toLowerCase();
        return breakingNewsTypes.some(t => typeLower.includes(t));
      });

      // Trigger breaking news for the most critical event
      if (criticalEvents.length > 0) {
        // Prioritize war/nuclear/attack events
        const priorityEvent = criticalEvents.find((e: GameEvent) =>
          e.type.toLowerCase().includes('war') ||
          e.type.toLowerCase().includes('nuclear') ||
          e.type.toLowerCase().includes('attack')
        ) || criticalEvents[0];

        triggerBreakingNews(priorityEvent);
      }

      // Extract new timeline events
      const newTimelineEvents: TimelineEvent[] = (result.timeline_events || []).map((te: {
        id: string;
        date: string;
        actor_country: string;
        title_fr: string;
        type: string;
        importance: number;
      }) => ({
        id: te.id,
        date: {
          year: result.year,
          month: result.month,
          day: parseInt(te.date.split('-')[2]) || 1,
          display: te.date,
          display_fr: te.date,
        },
        actor_country: te.actor_country,
        target_countries: [],
        title: te.title_fr,
        title_fr: te.title_fr,
        description: '',
        description_fr: '',
        type: te.type as TimelineEvent['type'],
        source: 'procedural' as TimelineEvent['source'],
        importance: te.importance,
        family: 'tactical' as TimelineEvent['family'],
        read: false,
        caused_by: null,
        triggers: [],
        caused_by_chain: [],
        effects_chain: [],
        ripple_weight: 0,
        ripple_targets: [],
      }));

      // Add new events to timeline
      const updatedTimeline = [...timeline, ...newTimelineEvents];

      // Update month names
      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthNamesFr = [
        'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
      ];

      set({
        year: result.year,
        month: result.month,
        dateDisplay: `${monthNames[result.month - 1]} ${result.year}`,
        dateDisplayFr: `${monthNamesFr[result.month - 1]} ${result.year}`,
        timeline: updatedTimeline,
        unreadEventCount: result.unread_events || newTimelineEvents.length,
        recentTickEvents: result.events || [],
        showEventToast: (result.events || []).length > 0,
        eventHistory: [...(result.events || []), ...eventHistory].slice(0, 100),
      });

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

  // Fetch timeline events
  fetchTimeline: async (params?: { year?: number; month?: number }) => {
    set({ timelineLoading: true });
    try {
      const result = await api.getTimelineEvents({
        start_year: params?.year,
        start_month: params?.month,
        limit: 200,
      });
      set({
        timeline: result.events,
        timelineLoading: false,
      });
    } catch {
      set({ timelineLoading: false });
    }
  },

  // Fetch events for a specific month
  fetchTimelineForMonth: async (year: number, month: number): Promise<TimelineEvent[]> => {
    try {
      const result = await api.getTimelineEventsByMonth(year, month);
      return result.events;
    } catch {
      return [];
    }
  },

  // Set the date being viewed in the timeline modal
  setViewingDate: (date: GameDate | null) => {
    set({ viewingDate: date });
  },

  // Navigate to previous month in timeline
  goToPreviousMonth: () => {
    const { viewingDate, year, month } = get();
    const currentViewYear = viewingDate?.year ?? year;
    const currentViewMonth = viewingDate?.month ?? month;

    let newMonth = currentViewMonth - 1;
    let newYear = currentViewYear;
    if (newMonth < 1) {
      newMonth = 12;
      newYear -= 1;
    }

    // Don't go before game start (2025-01)
    if (newYear < 2025 || (newYear === 2025 && newMonth < 1)) {
      return;
    }

    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const monthNamesFr = [
      'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
    ];

    set({
      viewingDate: {
        year: newYear,
        month: newMonth,
        day: 1,
        display: `${monthNames[newMonth - 1]} ${newYear}`,
        display_fr: `${monthNamesFr[newMonth - 1]} ${newYear}`,
      },
    });
  },

  // Navigate to next month (or advance game if at current date)
  goToNextMonth: async () => {
    const { viewingDate, year, month, advanceMonth: advanceMonthAction } = get();
    const currentViewYear = viewingDate?.year ?? year;
    const currentViewMonth = viewingDate?.month ?? month;

    // If viewing current date, advance the game
    if (currentViewYear === year && currentViewMonth === month) {
      await advanceMonthAction();
      return;
    }

    // Otherwise, navigate forward in timeline
    let newMonth = currentViewMonth + 1;
    let newYear = currentViewYear;
    if (newMonth > 12) {
      newMonth = 1;
      newYear += 1;
    }

    // Don't go beyond current game date
    if (newYear > year || (newYear === year && newMonth > month)) {
      // Reset to current date
      set({ viewingDate: null });
      return;
    }

    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const monthNamesFr = [
      'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'
    ];

    set({
      viewingDate: {
        year: newYear,
        month: newMonth,
        day: 1,
        display: `${monthNames[newMonth - 1]} ${newYear}`,
        display_fr: `${monthNamesFr[newMonth - 1]} ${newYear}`,
      },
    });
  },

  // Mark events as read
  markEventsAsRead: async (eventIds?: string[]) => {
    try {
      const result = await api.markTimelineEventsRead(eventIds);
      set({ unreadEventCount: result.unread_remaining });

      // Update timeline events to mark as read
      if (eventIds) {
        const { timeline } = get();
        set({
          timeline: timeline.map(e =>
            eventIds.includes(e.id) ? { ...e, read: true } : e
          ),
        });
      } else {
        // Mark all as read
        const { timeline } = get();
        set({
          timeline: timeline.map(e => ({ ...e, read: true })),
        });
      }
    } catch {
      // Silent fail
    }
  },

  // Open timeline modal
  openTimelineModal: () => {
    set({ timelineModalOpen: true });
  },

  // Close timeline modal
  closeTimelineModal: () => {
    set({ timelineModalOpen: false, viewingDate: null });
  },

  // Get events for the currently viewing month
  getEventsForViewingMonth: () => {
    const { timeline, viewingDate, year, month } = get();
    const viewYear = viewingDate?.year ?? year;
    const viewMonth = viewingDate?.month ?? month;

    return timeline.filter(
      e => e.date.year === viewYear && e.date.month === viewMonth
    ).sort((a, b) => (a.date.day || 0) - (b.date.day || 0));
  },

  // Check if can navigate backward
  canGoBack: () => {
    const { viewingDate, year, month } = get();
    const viewYear = viewingDate?.year ?? year;
    const viewMonth = viewingDate?.month ?? month;
    // Can go back if not at game start (2025-01)
    return viewYear > 2025 || (viewYear === 2025 && viewMonth > 1);
  },

  // Check if can navigate forward (always true - will advance game if at current)
  canGoForward: () => true,

  // =========================================================================
  // TIER 4/5/6 ACTIONS
  // =========================================================================

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

  // =========================================================================
  // BREAKING NEWS ACTIONS
  // =========================================================================

  // Dismiss breaking news banner
  dismissBreakingNews: () => {
    set({ showBreakingNews: false, breakingNewsEvent: null });
  },

  // Trigger breaking news for a critical event
  triggerBreakingNews: (event: GameEvent) => {
    set({ breakingNewsEvent: event, showBreakingNews: true });
  },
}));
