'use client';

import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { CountryCard } from '@/components/CountryCard';
import { CountryPanel } from '@/components/CountryPanel';
import { EventLog } from '@/components/EventLog';
import { Controls } from '@/components/Controls';
import { GlobalStats } from '@/components/GlobalStats';
import { Tier4List } from '@/components/Tier4List';
import InfluencePanel from '@/components/InfluencePanel';
import MilitaryBasesPanel from '@/components/MilitaryBasesPanel';
import ZoneDetailModal from '@/components/ZoneDetailModal';
import ActionPanel from '@/components/ActionPanel';
import WorldMap from '@/components/WorldMap';
import InfluenceHistory from '@/components/InfluenceHistory';
import NotificationCenter from '@/components/NotificationCenter';
import PlayerSelector from '@/components/PlayerSelector';
import SaveLoadPanel from '@/components/SaveLoadPanel';
import ScenarioSelector from '@/components/ScenarioSelector';
import { MultiplayerPanel } from '@/components/multiplayer';
import { useHistoriaShortcuts, SHORTCUTS_HELP } from '@/hooks/useKeyboardShortcuts';
import { InfluenceZone, COUNTRY_FLAGS } from '@/lib/types';
import { getInfluenceZonesAdvanced, startScenario } from '@/lib/api';

// Tab configuration with icons, colors, and descriptions
const TABS_CONFIG = [
  {
    key: 'countries' as const,
    label: 'Pays',
    icon: '🌍',
    color: '#3b82f6',
    description: 'Puissances mondiales',
    gradient: 'from-blue-600 to-blue-800',
  },
  {
    key: 'influence' as const,
    label: 'Influence',
    icon: '⚔️',
    color: '#9333ea',
    description: 'Actions & zones',
    gradient: 'from-purple-600 to-purple-800',
  },
  {
    key: 'map' as const,
    label: 'Carte',
    icon: '🗺️',
    color: '#0891b2',
    description: 'Vue mondiale',
    gradient: 'from-cyan-600 to-cyan-800',
  },
  {
    key: 'stats' as const,
    label: 'Stats',
    icon: '📊',
    color: '#059669',
    description: 'Historique & classements',
    gradient: 'from-emerald-600 to-emerald-800',
  },
];

type TabKey = typeof TABS_CONFIG[number]['key'];

export default function GameApp() {
  const {
    world,
    selectedCountry,
    isLoading,
    error,
    autoPlay,
    settings,
    fetchWorldState,
    fetchSettings,
    selectCountry,
    advanceTick,
    advanceMultipleTicks,
    resetWorld,
    setAutoPlay,
    setAiMode,
    clearError,
  } = useGameStore();

  const [filter, setFilter] = useState<'all' | 'tier1' | 'tier2' | 'tier3' | 'nuclear'>('all');
  const [activeTab, setActiveTab] = useState<TabKey>('countries');
  const [selectedZone, setSelectedZone] = useState<InfluenceZone | null>(null);
  const [zones, setZones] = useState<InfluenceZone[]>([]);
  const [previousZones, setPreviousZones] = useState<InfluenceZone[]>([]);
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  const [showSaveLoad, setShowSaveLoad] = useState(false);
  const [showScenarioSelector, setShowScenarioSelector] = useState(false);
  const [showMultiplayer, setShowMultiplayer] = useState(false);
  const [zonesLoading, setZonesLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const prevYearRef = useRef<number | null>(null);

  // Tab keys for navigation
  const tabKeys = TABS_CONFIG.map(t => t.key);

  // Initial load
  useEffect(() => {
    fetchWorldState();
    fetchSettings();
    loadZones();
  }, [fetchWorldState, fetchSettings]);

  // Load zones data with loading state
  const loadZones = useCallback(async () => {
    setZonesLoading(true);
    try {
      const data = await getInfluenceZonesAdvanced();
      setZones(data.zones);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to load zones:', error);
    } finally {
      setZonesLoading(false);
    }
  }, []);

  // Reload zones when year changes (after tick) with previous state preservation
  useEffect(() => {
    if (world && world.year !== prevYearRef.current) {
      // Save current zones as previous before loading new ones
      if (zones.length > 0) {
        setPreviousZones([...zones]);
      }
      loadZones();
      prevYearRef.current = world.year;
    }
  }, [world?.year, zones, loadZones]);

  // Auto-play effect with visual feedback
  useEffect(() => {
    if (!autoPlay) return;

    const interval = setInterval(() => {
      advanceTick();
    }, 1500);

    return () => clearInterval(interval);
  }, [autoPlay, advanceTick]);

  // Filter countries
  const filteredCountries = useMemo(() => {
    if (!world?.countries) return [];
    return world.countries.filter(country => {
      switch (filter) {
        case 'tier1':
          return country.tier === 1;
        case 'tier2':
          return country.tier === 2;
        case 'tier3':
          return country.tier === 3;
        case 'nuclear':
          return country.nuclear > 0;
        default:
          return true;
      }
    });
  }, [world?.countries, filter]);

  // Sort by power score
  const sortedCountries = useMemo(() => {
    return [...filteredCountries].sort((a, b) => b.power_score - a.power_score);
  }, [filteredCountries]);

  // Stats for tabs badges
  const tabStats = useMemo(() => {
    const contestedZones = zones.filter(z => z.contested_by.length > 0).length;
    const criticalZones = zones.filter(z => {
      // Check for high tension zones - you might need to adjust this based on your data
      const tensions = z.contested_by.length * 20;
      return tensions >= 60;
    }).length;

    return {
      countries: world?.countries.length || 0,
      influence: contestedZones,
      map: zones.length,
      stats: criticalZones,
    };
  }, [world?.countries, zones]);

  const handleAutoPlayToggle = useCallback(() => {
    setAutoPlay(!autoPlay);
  }, [autoPlay, setAutoPlay]);

  const handleAiModeToggle = useCallback(() => {
    const newMode = settings?.ai_mode === 'ollama' ? 'algorithmic' : 'ollama';
    setAiMode(newMode);
  }, [settings?.ai_mode, setAiMode]);

  // Handle tab navigation with keyboard
  const handleNavigateTab = useCallback((direction: 'left' | 'right') => {
    const currentIndex = tabKeys.indexOf(activeTab);
    let newIndex: number;
    if (direction === 'left') {
      newIndex = currentIndex === 0 ? tabKeys.length - 1 : currentIndex - 1;
    } else {
      newIndex = currentIndex === tabKeys.length - 1 ? 0 : currentIndex + 1;
    }
    setActiveTab(tabKeys[newIndex]);
  }, [activeTab, tabKeys]);

  // Close all modals
  const handleCloseModals = useCallback(() => {
    if (showMultiplayer) {
      setShowMultiplayer(false);
    } else if (showScenarioSelector) {
      setShowScenarioSelector(false);
    } else if (showSaveLoad) {
      setShowSaveLoad(false);
    } else if (selectedZone) {
      setSelectedZone(null);
    } else if (selectedCountry) {
      selectCountry(null);
    } else if (showShortcutsHelp) {
      setShowShortcutsHelp(false);
    }
  }, [showMultiplayer, showScenarioSelector, showSaveLoad, selectedZone, selectedCountry, showShortcutsHelp, selectCountry]);

  // Start scenario handler
  const handleStartScenario = useCallback(async (scenarioId: string, playerCountryId?: string) => {
    await startScenario(scenarioId, playerCountryId);
    await fetchWorldState();
    await loadZones();
    if (playerCountryId) {
      selectCountry(playerCountryId);
    }
  }, [fetchWorldState, loadZones, selectCountry]);

  // Open save panel
  const handleOpenSaveLoad = useCallback(() => {
    setShowSaveLoad(true);
  }, []);

  // Reload game state after loading
  const handleGameLoaded = useCallback(() => {
    fetchWorldState();
    loadZones();
  }, [fetchWorldState, loadZones]);

  // Manual refresh zones
  const handleRefreshZones = useCallback(() => {
    setPreviousZones([...zones]);
    loadZones();
  }, [zones, loadZones]);

  // Keyboard shortcuts
  useHistoriaShortcuts({
    onTick: advanceTick,
    onToggleAutoPlay: handleAutoPlayToggle,
    onCloseModal: handleCloseModals,
    onNavigateTab: handleNavigateTab,
    onSave: handleOpenSaveLoad,
    enabled: !isLoading,
  });

  // Loading screen
  if (!world) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          {error ? (
            <div className="bg-gray-800 rounded-xl p-8 shadow-2xl max-w-md">
              <div className="text-5xl mb-4">{'⚠️'}</div>
              <p className="text-red-400 mb-4 text-lg">{error}</p>
              <button
                onClick={() => {
                  clearError();
                  fetchWorldState();
                }}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
              >
                Reessayer
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-6xl animate-pulse">{'🌍'}</div>
              <div className="text-2xl font-bold">Historia Lite</div>
              <div className="text-gray-400">Chargement du monde...</div>
              <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden mx-auto">
                <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Enhanced Header */}
      <header className="sticky top-0 z-40 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 px-4 py-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xl shadow-lg">
              {'🌍'}
            </div>
            <div>
              <h1 className="text-xl lg:text-2xl font-bold flex items-center gap-2">
                Historia Lite
                {autoPlay && (
                  <span className="px-2 py-0.5 bg-green-600 rounded-full text-xs animate-pulse">
                    AUTO
                  </span>
                )}
              </h1>
              <div className="text-xs text-gray-400 hidden sm:block">
                Simulateur Geopolitique | Annee {world.year}
              </div>
            </div>
          </div>

          {/* Header Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Year indicator (mobile) */}
            <div className="sm:hidden px-3 py-1.5 bg-gray-800 rounded-lg text-sm">
              <span className="text-gray-400">Annee</span>{' '}
              <span className="font-bold text-amber-400">{world.year}</span>
            </div>

            {/* Global tension indicator */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg">
              <span className="text-sm text-gray-400">Tension:</span>
              <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    world.global_tension >= 70 ? 'bg-red-500' :
                    world.global_tension >= 40 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${world.global_tension}%` }}
                />
              </div>
              <span className={`text-sm font-bold ${
                world.global_tension >= 70 ? 'text-red-400' :
                world.global_tension >= 40 ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {world.global_tension}%
              </span>
            </div>

            {/* Player country selector */}
            <PlayerSelector
              countries={world.countries}
              selectedCountry={selectedCountry}
              onSelectCountry={(country) => selectCountry(country?.id || null)}
            />

            {/* Scenario selector button */}
            <button
              onClick={() => setShowScenarioSelector(true)}
              className="p-2.5 rounded-xl bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition-all"
              title="Choisir un scenario"
            >
              {'🎬'}
            </button>

            {/* Multiplayer button */}
            <button
              onClick={() => setShowMultiplayer(true)}
              className="p-2.5 rounded-xl bg-purple-800 text-purple-300 hover:bg-purple-700 hover:text-white transition-all"
              title="Mode Multijoueur"
            >
              {'🎮'}
            </button>

            {/* Save/Load button */}
            <button
              onClick={() => setShowSaveLoad(true)}
              className="p-2.5 rounded-xl bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition-all"
              title="Sauvegardes (Ctrl+S)"
            >
              {'💾'}
            </button>

            {/* Keyboard shortcuts help */}
            <button
              onClick={() => setShowShortcutsHelp(true)}
              className="p-2.5 rounded-xl bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition-all"
              title="Raccourcis clavier (?)"
            >
              {'⌨️'}
            </button>

            {/* Notifications */}
            <NotificationCenter
              events={world.recent_events}
              zones={zones}
              previousZones={previousZones}
              currentYear={world.year}
              playerPower={selectedCountry?.id}
            />
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span>{'⚠️'}</span>
            <span>{error}</span>
          </div>
          <button onClick={clearError} className="text-gray-400 hover:text-white p-1">
            {'✕'}
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="p-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left sidebar - Controls & Stats */}
          <div className="lg:col-span-3 space-y-4 order-2 lg:order-1">
            <Controls
              year={world.year}
              oilPrice={world.oil_price}
              globalTension={world.global_tension}
              isLoading={isLoading}
              autoPlay={autoPlay}
              settings={settings}
              onTick={advanceTick}
              onMultiTick={advanceMultipleTicks}
              onReset={resetWorld}
              onAutoPlayToggle={handleAutoPlayToggle}
              onAiModeToggle={handleAiModeToggle}
            />
            <GlobalStats world={world} onShowInfluence={() => setActiveTab('influence')} />
            <Tier4List />
          </div>

          {/* Center - Main content with enhanced tabs */}
          <div className="lg:col-span-6 order-1 lg:order-2">
            {/* Enhanced Tab Navigation */}
            <div className="bg-gray-800 rounded-xl p-1.5 mb-4 flex gap-1">
              {TABS_CONFIG.map((tab) => {
                const isActive = activeTab === tab.key;
                const stat = tabStats[tab.key];

                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex-1 relative px-3 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                      isActive
                        ? 'text-white shadow-lg'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                    }`}
                    style={{
                      backgroundColor: isActive ? tab.color : undefined,
                    }}
                  >
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-lg">{tab.icon}</span>
                      <span className="hidden sm:inline">{tab.label}</span>
                    </div>

                    {/* Badge with stat */}
                    {stat > 0 && (
                      <span className={`absolute -top-1 -right-1 min-w-5 h-5 flex items-center justify-center text-[10px] font-bold rounded-full ${
                        isActive ? 'bg-white text-gray-900' : 'bg-gray-600 text-white'
                      }`}>
                        {stat}
                      </span>
                    )}

                    {/* Active indicator */}
                    {isActive && (
                      <div className="absolute inset-x-2 -bottom-1 h-0.5 bg-white/50 rounded-full" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Tab description & refresh button */}
            <div className="flex items-center justify-between mb-4 px-1">
              <div className="text-sm text-gray-400">
                {TABS_CONFIG.find(t => t.key === activeTab)?.description}
                {zonesLoading && (
                  <span className="ml-2 text-cyan-400 animate-pulse">
                    {'⟳'} Mise a jour...
                  </span>
                )}
              </div>
              {(activeTab === 'map' || activeTab === 'influence') && (
                <button
                  onClick={handleRefreshZones}
                  disabled={zonesLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <span className={zonesLoading ? 'animate-spin' : ''}>{'⟳'}</span>
                  Actualiser
                  {lastRefresh && (
                    <span className="text-gray-500 hidden sm:inline">
                      ({lastRefresh.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })})
                    </span>
                  )}
                </button>
              )}
            </div>

            {/* Tab Content with animations */}
            <div className="relative">
              {/* Countries Tab */}
              {activeTab === 'countries' && (
                <div className="animate-fadeIn">
                  {/* Filter tabs */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {[
                      { key: 'all', label: 'Tous', count: world.countries.length },
                      { key: 'tier1', label: 'Tier 1', count: world.countries.filter(c => c.tier === 1).length },
                      { key: 'tier2', label: 'Tier 2', count: world.countries.filter(c => c.tier === 2).length },
                      { key: 'tier3', label: 'Tier 3', count: world.countries.filter(c => c.tier === 3).length },
                      { key: 'nuclear', label: 'Nucleaire', count: world.countries.filter(c => c.nuclear > 0).length, icon: '☢️' },
                    ].map(({ key, label, count, icon }) => (
                      <button
                        key={key}
                        onClick={() => setFilter(key as typeof filter)}
                        className={`px-3 py-1.5 rounded-lg text-sm transition-all flex items-center gap-1.5 ${
                          filter === key
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        {icon && <span>{icon}</span>}
                        {label}
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          filter === key ? 'bg-white/20' : 'bg-gray-700'
                        }`}>
                          {count}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Countries grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[60vh] lg:max-h-[calc(100vh-320px)] overflow-y-auto pr-2 scrollbar-thin">
                    {sortedCountries.map((country, index) => (
                      <div
                        key={country.id}
                        style={{ animationDelay: `${index * 30}ms` }}
                        className="animate-fadeInUp"
                      >
                        <CountryCard
                          country={country}
                          isSelected={selectedCountry?.id === country.id}
                          onClick={() => selectCountry(
                            selectedCountry?.id === country.id ? null : country.id
                          )}
                        />
                      </div>
                    ))}
                  </div>

                  {/* Empty state */}
                  {sortedCountries.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <span className="text-4xl block mb-2">{'🔍'}</span>
                      Aucun pays ne correspond au filtre
                    </div>
                  )}
                </div>
              )}

              {/* Influence Tab */}
              {activeTab === 'influence' && (
                <div className="space-y-4 max-h-[60vh] lg:max-h-[calc(100vh-280px)] overflow-y-auto pr-2 scrollbar-thin animate-fadeIn">
                  <ActionPanel
                    playerCountry={selectedCountry}
                    zones={zones}
                    allCountries={world.countries}
                    onActionComplete={loadZones}
                  />
                  <InfluencePanel onZoneSelect={(zone) => setSelectedZone(zone)} />
                  <MilitaryBasesPanel />
                </div>
              )}

              {/* Map Tab */}
              {activeTab === 'map' && (
                <div className="space-y-4 animate-fadeIn">
                  <WorldMap
                    zones={zones}
                    onZoneClick={(zone) => setSelectedZone(zone)}
                    selectedZoneId={selectedZone?.id}
                    highlightPower={selectedCountry?.id}
                  />

                  {/* Quick zone stats */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { label: 'Zones totales', value: zones.length, icon: '🌍', color: 'blue' },
                      { label: 'Contestees', value: zones.filter(z => z.contested_by.length > 0).length, icon: '⚔️', color: 'yellow' },
                      { label: 'Petrole', value: zones.filter(z => z.has_oil).length, icon: '🛢️', color: 'gray' },
                      { label: 'Strategiques', value: zones.filter(z => z.has_strategic_resources).length, icon: '💎', color: 'cyan' },
                    ].map(({ label, value, icon, color }) => (
                      <div key={label} className="bg-gray-800 rounded-lg p-3 text-center">
                        <div className="text-xl mb-1">{icon}</div>
                        <div className={`text-lg font-bold text-${color}-400`}>{value}</div>
                        <div className="text-xs text-gray-500">{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Stats/History Tab */}
              {activeTab === 'stats' && (
                <div className="space-y-4 max-h-[60vh] lg:max-h-[calc(100vh-280px)] overflow-y-auto pr-2 scrollbar-thin animate-fadeIn">
                  <InfluenceHistory
                    currentYear={world.year}
                    zones={zones}
                  />
                </div>
              )}

              {/* Loading overlay */}
              {(isLoading || zonesLoading) && (
                <div className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center rounded-lg">
                  <div className="bg-gray-800 rounded-lg px-6 py-4 flex items-center gap-3 shadow-xl">
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <span>Chargement...</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right sidebar - Events */}
          <div className="lg:col-span-3 order-3">
            <div className="sticky top-20">
              <EventLog events={world.recent_events} maxEvents={30} />
            </div>
          </div>
        </div>
      </main>

      {/* Country detail modal */}
      {selectedCountry && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => selectCountry(null)}
        >
          <div
            onClick={e => e.stopPropagation()}
            className="animate-scaleIn"
          >
            <CountryPanel
              country={selectedCountry}
              allCountries={world.countries}
              onClose={() => selectCountry(null)}
            />
          </div>
        </div>
      )}

      {/* Zone detail modal */}
      {selectedZone && (
        <ZoneDetailModal
          zone={selectedZone}
          onClose={() => setSelectedZone(null)}
        />
      )}

      {/* Save/Load modal */}
      <SaveLoadPanel
        currentYear={world.year}
        isOpen={showSaveLoad}
        onClose={() => setShowSaveLoad(false)}
        onGameLoaded={handleGameLoaded}
      />

      {/* Keyboard shortcuts help modal */}
      {showShortcutsHelp && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowShortcutsHelp(false)}
        >
          <div
            className="bg-gray-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden animate-scaleIn"
            onClick={e => e.stopPropagation()}
          >
            <div className="px-6 py-4 bg-gradient-to-r from-indigo-900/50 to-gray-800 border-b border-gray-700">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>{'⌨️'}</span>
                Raccourcis Clavier
              </h2>
            </div>
            <div className="p-6 space-y-3">
              {SHORTCUTS_HELP.map(({ keys, description }) => (
                <div key={keys} className="flex items-center justify-between">
                  <span className="text-gray-300">{description}</span>
                  <kbd className="px-2.5 py-1 bg-gray-700 rounded-lg text-sm font-mono text-amber-400 shadow-inner">
                    {keys}
                  </kbd>
                </div>
              ))}
            </div>
            <div className="px-6 py-4 bg-gray-750 border-t border-gray-700 flex justify-between items-center">
              <span className="text-xs text-gray-500">
                Appuyez sur ? pour afficher cette aide
              </span>
              <button
                onClick={() => setShowShortcutsHelp(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors font-medium"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scenario Selector modal */}
      {showScenarioSelector && (
        <ScenarioSelector
          onScenarioStart={handleStartScenario}
          onClose={() => setShowScenarioSelector(false)}
        />
      )}

      {/* Multiplayer Panel */}
      {showMultiplayer && (
        <MultiplayerPanel
          countries={world.countries}
          onStartGame={() => {
            setShowMultiplayer(false);
            // Could integrate with game state for multiplayer mode
          }}
          onClose={() => setShowMultiplayer(false)}
        />
      )}

    </div>
  );
}
