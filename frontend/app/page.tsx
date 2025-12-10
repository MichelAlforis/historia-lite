'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
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
import { useHistoriaShortcuts, SHORTCUTS_HELP } from '@/hooks/useKeyboardShortcuts';
import { InfluenceZone } from '@/lib/types';
import { getInfluenceZonesAdvanced } from '@/lib/api';

export default function HomePage() {
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
  const [activeTab, setActiveTab] = useState<'countries' | 'influence' | 'map' | 'history'>('countries');
  const [selectedZone, setSelectedZone] = useState<InfluenceZone | null>(null);
  const [zones, setZones] = useState<InfluenceZone[]>([]);
  const [previousZones, setPreviousZones] = useState<InfluenceZone[]>([]);
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  const prevYearRef = useRef<number | null>(null);

  // Tab navigation order
  const tabs: Array<'countries' | 'influence' | 'map' | 'history'> = ['countries', 'influence', 'map', 'history'];

  // Initial load
  useEffect(() => {
    fetchWorldState();
    fetchSettings();
    loadZones();
  }, [fetchWorldState, fetchSettings]);

  // Load zones data
  const loadZones = async () => {
    try {
      const data = await getInfluenceZonesAdvanced();
      setZones(data.zones);
    } catch (error) {
      console.error('Failed to load zones:', error);
    }
  };

  // Reload zones when year changes (after tick)
  useEffect(() => {
    if (world && world.year !== prevYearRef.current) {
      setPreviousZones(zones);
      loadZones();
      prevYearRef.current = world.year;
    }
  }, [world?.year]);

  // Auto-play effect
  useEffect(() => {
    if (!autoPlay) return;

    const interval = setInterval(() => {
      advanceTick();
    }, 1500);

    return () => clearInterval(interval);
  }, [autoPlay, advanceTick]);

  // Filter countries
  const filteredCountries = world?.countries.filter(country => {
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
  }) || [];

  // Sort by power score
  const sortedCountries = [...filteredCountries].sort(
    (a, b) => b.power_score - a.power_score
  );

  const handleAutoPlayToggle = useCallback(() => {
    setAutoPlay(!autoPlay);
  }, [autoPlay, setAutoPlay]);

  const handleAiModeToggle = useCallback(() => {
    const newMode = settings?.ai_mode === 'ollama' ? 'algorithmic' : 'ollama';
    setAiMode(newMode);
  }, [settings?.ai_mode, setAiMode]);

  // Handle tab navigation with keyboard
  const handleNavigateTab = useCallback((direction: 'left' | 'right') => {
    const currentIndex = tabs.indexOf(activeTab);
    let newIndex: number;
    if (direction === 'left') {
      newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
    } else {
      newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
    }
    setActiveTab(tabs[newIndex]);
  }, [activeTab, tabs]);

  // Close all modals
  const handleCloseModals = useCallback(() => {
    if (selectedZone) {
      setSelectedZone(null);
    } else if (selectedCountry) {
      selectCountry(null);
    } else if (showShortcutsHelp) {
      setShowShortcutsHelp(false);
    }
  }, [selectedZone, selectedCountry, showShortcutsHelp, selectCountry]);

  // Keyboard shortcuts
  useHistoriaShortcuts({
    onTick: advanceTick,
    onToggleAutoPlay: handleAutoPlayToggle,
    onCloseModal: handleCloseModals,
    onNavigateTab: handleNavigateTab,
    enabled: !isLoading,
  });

  if (!world) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          {error ? (
            <div>
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={() => {
                  clearError();
                  fetchWorldState();
                }}
                className="px-4 py-2 bg-blue-600 rounded"
              >
                Reessayer
              </button>
            </div>
          ) : (
            <div className="text-xl">Chargement de Historia Lite...</div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      {/* Header */}
      <header className="mb-4 lg:mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <h1 className="text-2xl lg:text-3xl font-bold">
          Historia Lite
          <span className="text-sm lg:text-lg font-normal text-gray-400 ml-2 lg:ml-3 hidden sm:inline">
            Simulateur Geopolitique Moderne
          </span>
        </h1>
        <div className="flex items-center gap-3">
          {/* Player country selector */}
          <PlayerSelector
            countries={world.countries}
            selectedCountry={selectedCountry}
            onSelectCountry={(country) => selectCountry(country?.id || null)}
          />

          {/* Keyboard shortcuts help */}
          <button
            onClick={() => setShowShortcutsHelp(true)}
            className="p-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white transition-colors"
            title="Raccourcis clavier (?)"
          >
            <span className="text-lg">&#9000;</span>
          </button>

          {/* Notifications */}
          <NotificationCenter
            events={world.recent_events}
            zones={zones}
            previousZones={previousZones}
          />
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="mb-4 p-3 bg-red-800 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-white hover:text-gray-300">
            X
          </button>
        </div>
      )}

      {/* Main layout */}
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

        {/* Center - Main content with tabs */}
        <div className="lg:col-span-6 order-1 lg:order-2">
          {/* Main tabs */}
          <div className="flex flex-wrap gap-2 mb-4">
            {([
              { key: 'countries', label: 'Pays', icon: '&#127463;', color: 'blue' },
              { key: 'influence', label: 'Influence', icon: '&#127760;', color: 'purple' },
              { key: 'map', label: 'Carte', icon: '&#128506;', color: 'cyan' },
              { key: 'history', label: 'Stats', icon: '&#128200;', color: 'emerald' },
            ] as const).map(({ key, label, icon, color }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-colors flex items-center gap-1.5 lg:gap-2 ${
                  activeTab === key
                    ? `bg-${color}-600 text-white`
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                style={{
                  backgroundColor: activeTab === key
                    ? (color === 'blue' ? '#2563eb' :
                       color === 'purple' ? '#9333ea' :
                       color === 'cyan' ? '#0891b2' :
                       color === 'emerald' ? '#059669' : '#2563eb')
                    : undefined
                }}
              >
                <span dangerouslySetInnerHTML={{ __html: icon }} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>

          {/* Countries Tab */}
          {activeTab === 'countries' && (
            <>
              {/* Filter tabs */}
              <div className="flex flex-wrap gap-1.5 lg:gap-2 mb-3 lg:mb-4">
                {[
                  { key: 'all', label: 'Tous' },
                  { key: 'tier1', label: 'T1' },
                  { key: 'tier2', label: 'T2' },
                  { key: 'tier3', label: 'T3' },
                  { key: 'nuclear', label: 'Nuc.' },
                ].map(({ key, label }) => (
                  <button
                    key={key}
                    onClick={() => setFilter(key as typeof filter)}
                    className={`px-2 lg:px-3 py-1 rounded-lg text-xs lg:text-sm transition-colors ${
                      filter === key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Countries grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 lg:gap-3 max-h-[60vh] lg:max-h-[calc(100vh-250px)] overflow-y-auto pr-2">
                {sortedCountries.map(country => (
                  <CountryCard
                    key={country.id}
                    country={country}
                    isSelected={selectedCountry?.id === country.id}
                    onClick={() => selectCountry(
                      selectedCountry?.id === country.id ? null : country.id
                    )}
                  />
                ))}
              </div>
            </>
          )}

          {/* Influence Tab */}
          {activeTab === 'influence' && (
            <div className="space-y-3 lg:space-y-4 max-h-[60vh] lg:max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
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
            <div className="space-y-3 lg:space-y-4 max-h-[60vh] lg:max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
              <WorldMap
                zones={zones}
                onZoneClick={(zone) => setSelectedZone(zone)}
                selectedZoneId={selectedZone?.id}
                highlightPower={selectedCountry?.id}
              />
            </div>
          )}

          {/* History/Stats Tab */}
          {activeTab === 'history' && (
            <div className="space-y-3 lg:space-y-4 max-h-[60vh] lg:max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
              <InfluenceHistory
                currentYear={world.year}
                zones={zones}
              />
            </div>
          )}
        </div>

        {/* Right sidebar - Events */}
        <div className="lg:col-span-3 order-3">
          <div className="h-auto lg:h-[calc(100vh-150px)]">
            <EventLog events={world.recent_events} maxEvents={30} />
          </div>
        </div>
      </div>

      {/* Country detail modal */}
      {selectedCountry && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => selectCountry(null)}
        >
          <div onClick={e => e.stopPropagation()}>
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

      {/* Keyboard shortcuts help modal */}
      {showShortcutsHelp && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowShortcutsHelp(false)}
        >
          <div
            className="bg-gray-800 rounded-lg shadow-2xl max-w-md w-full overflow-hidden animate-scaleIn"
            onClick={e => e.stopPropagation()}
          >
            <div className="px-6 py-4 bg-gradient-to-r from-indigo-900/50 to-gray-700 border-b border-gray-700">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>&#9000;</span>
                Raccourcis Clavier
              </h2>
            </div>
            <div className="p-6 space-y-3">
              {SHORTCUTS_HELP.map(({ keys, description }) => (
                <div key={keys} className="flex items-center justify-between">
                  <span className="text-gray-300">{description}</span>
                  <kbd className="px-2 py-1 bg-gray-700 rounded text-sm font-mono text-amber-400">
                    {keys}
                  </kbd>
                </div>
              ))}
            </div>
            <div className="px-6 py-3 bg-gray-750 border-t border-gray-700 text-center">
              <button
                onClick={() => setShowShortcutsHelp(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
