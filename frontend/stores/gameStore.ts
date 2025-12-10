// Historia Lite - Game State Store (Zustand)
import { create } from 'zustand';
import { WorldState, Country, GameEvent, TickResponse, GameSettings } from '@/lib/types';
import * as api from '@/lib/api';

interface GameStore {
  // State
  world: WorldState | null;
  selectedCountry: Country | null;
  isLoading: boolean;
  error: string | null;
  autoPlay: boolean;
  speed: number; // 1 = normal, 2 = fast, 3 = ultra

  // AI Settings
  settings: GameSettings | null;
  ollamaConnected: boolean;

  // Actions
  fetchWorldState: () => Promise<void>;
  selectCountry: (countryId: string | null) => void;
  advanceTick: () => Promise<TickResponse | null>;
  advanceMultipleTicks: (years: number) => Promise<void>;
  resetWorld: (seed?: number) => Promise<void>;
  setAutoPlay: (autoPlay: boolean) => void;
  setSpeed: (speed: number) => void;
  clearError: () => void;

  // AI Actions
  fetchSettings: () => Promise<void>;
  setAiMode: (mode: 'algorithmic' | 'ollama') => Promise<void>;
  setOllamaModel: (model: string) => Promise<void>;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  world: null,
  selectedCountry: null,
  isLoading: false,
  error: null,
  autoPlay: false,
  speed: 1,

  // AI Settings
  settings: null,
  ollamaConnected: false,

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
    const { settings } = get();
    set({ isLoading: true, error: null });
    try {
      // Use Ollama or algorithmic based on settings
      const result = settings?.ai_mode === 'ollama' && settings?.ollama_available
        ? await api.advanceTickWithOllama()
        : await api.advanceTick();
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
}));
