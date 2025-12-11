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
import ZoneDetailModal from '@/components/ZoneDetailModal';
import WorldMap from '@/components/WorldMap';
import SaveLoadPanel from '@/components/SaveLoadPanel';
import DefconBanner from '@/components/DefconBanner';
import { useHistoriaShortcuts, SHORTCUTS_HELP } from '@/hooks/useKeyboardShortcuts';
import { InfluenceZone } from '@/lib/types';
import { getInfluenceZonesAdvanced } from '@/lib/api';

// 2 onglets simples
type TabKey = 'countries' | 'map';

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

  const [filter, setFilter] = useState<'all' | 'tier1' | 'tier2' | 'tier3'>('all');
  const [activeTab, setActiveTab] = useState<TabKey>('countries');
  const [selectedZone, setSelectedZone] = useState<InfluenceZone | null>(null);
  const [zones, setZones] = useState<InfluenceZone[]>([]);
  const [showSaveLoad, setShowSaveLoad] = useState(false);
  const prevYearRef = useRef<number | null>(null);

  // Critical events state
  const [showDefconBanner, setShowDefconBanner] = useState(false);
  const [criticalFlash, setCriticalFlash] = useState(false);
  const prevDefconRef = useRef<number | null>(null);

  // Chargement initial
  useEffect(() => {
    fetchWorldState();
    fetchSettings();
    loadZones();
  }, [fetchWorldState, fetchSettings]);

  // Charger les zones
  const loadZones = useCallback(async () => {
    try {
      const data = await getInfluenceZonesAdvanced();
      setZones(data.zones);
    } catch (error) {
      console.error('Failed to load zones:', error);
    }
  }, []);

  // Recharger les zones quand l'annee change
  useEffect(() => {
    if (world && world.year !== prevYearRef.current) {
      loadZones();
      prevYearRef.current = world.year;
    }
  }, [world?.year, loadZones]);

  // Detecter changement de DEFCON
  useEffect(() => {
    if (!world) return;

    if (prevDefconRef.current !== null && world.defcon_level !== prevDefconRef.current) {
      setShowDefconBanner(true);

      // Flash rouge si DEFCON critique (1-2)
      if (world.defcon_level <= 2) {
        setCriticalFlash(true);
        setTimeout(() => setCriticalFlash(false), 1500);
      }
    }
    prevDefconRef.current = world.defcon_level;
  }, [world?.defcon_level]);

  // Detecter evenements critiques dans les events recents
  useEffect(() => {
    if (!world?.recent_events?.length) return;

    const criticalTypes = ['war', 'nuclear', 'coup', 'attack', 'conflict'];
    const hasCriticalEvent = world.recent_events.some(event =>
      criticalTypes.some(type =>
        event.type?.toLowerCase().includes(type) ||
        event.title?.toLowerCase().includes(type)
      )
    );

    if (hasCriticalEvent) {
      setCriticalFlash(true);
      setTimeout(() => setCriticalFlash(false), 1500);
    }
  }, [world?.recent_events]);

  // Auto-play
  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(advanceTick, 1500);
    return () => clearInterval(interval);
  }, [autoPlay, advanceTick]);

  // Filtrer les pays
  const filteredCountries = useMemo(() => {
    if (!world?.countries) return [];
    return world.countries.filter(country => {
      if (filter === 'tier1') return country.tier === 1;
      if (filter === 'tier2') return country.tier === 2;
      if (filter === 'tier3') return country.tier === 3;
      return true;
    });
  }, [world?.countries, filter]);

  // Trier par puissance
  const sortedCountries = useMemo(() => {
    return [...filteredCountries].sort((a, b) => b.power_score - a.power_score);
  }, [filteredCountries]);

  const handleAutoPlayToggle = useCallback(() => {
    setAutoPlay(!autoPlay);
  }, [autoPlay, setAutoPlay]);

  const handleAiModeToggle = useCallback(() => {
    const newMode = settings?.ai_mode === 'ollama' ? 'algorithmic' : 'ollama';
    setAiMode(newMode);
  }, [settings?.ai_mode, setAiMode]);

  // Fermer les modals
  const handleCloseModals = useCallback(() => {
    if (showSaveLoad) setShowSaveLoad(false);
    else if (selectedZone) setSelectedZone(null);
    else if (selectedCountry) selectCountry(null);
  }, [showSaveLoad, selectedZone, selectedCountry, selectCountry]);

  // Navigation tabs
  const handleNavigateTab = useCallback((direction: 'left' | 'right') => {
    setActiveTab(prev => prev === 'countries' ? 'map' : 'countries');
  }, []);

  // Raccourcis clavier
  useHistoriaShortcuts({
    onTick: advanceTick,
    onToggleAutoPlay: handleAutoPlayToggle,
    onCloseModal: handleCloseModals,
    onNavigateTab: handleNavigateTab,
    onSave: () => setShowSaveLoad(true),
    enabled: !isLoading,
  });

  // Ecran de chargement
  if (!world) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          {error ? (
            <div className="bg-gray-800 rounded-xl p-8 max-w-md">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={() => { clearError(); fetchWorldState(); }}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                Reessayer
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-6xl animate-pulse">{'🌍'}</div>
              <div className="text-2xl font-bold">Historia Lite</div>
              <div className="text-gray-400">Chargement...</div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-900 text-white ${criticalFlash ? 'critical-flash' : ''}`}>
      {/* DEFCON Banner */}
      <DefconBanner
        level={world.defcon_level}
        show={showDefconBanner}
        onClose={() => setShowDefconBanner(false)}
      />

      {/* Header simple */}
      <header className="sticky top-0 z-40 bg-gray-900 border-b border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{'🌍'}</span>
            <div>
              <h1 className="text-xl font-bold">
                Historia Lite
                {autoPlay && <span className="ml-2 px-2 py-0.5 bg-green-600 rounded text-xs">AUTO</span>}
              </h1>
              <div className="text-xs text-gray-400">Annee {world.year}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* DEFCON */}
            <div className={`px-3 py-1.5 rounded-lg font-bold ${
              world.defcon_level <= 2 ? 'bg-red-900 text-red-400' :
              world.defcon_level === 3 ? 'bg-orange-900 text-orange-400' :
              'bg-green-900 text-green-400'
            }`}>
              DEFCON {world.defcon_level}
            </div>

            {/* Tension */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg">
              <span className="text-sm text-gray-400">Tension:</span>
              <span className={`font-bold ${
                world.global_tension >= 70 ? 'text-red-400' :
                world.global_tension >= 40 ? 'text-yellow-400' : 'text-green-400'
              }`}>
                {world.global_tension}%
              </span>
            </div>

            {/* Sauvegarde */}
            <button
              onClick={() => setShowSaveLoad(true)}
              className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700"
              title="Sauvegardes"
            >
              {'💾'}
            </button>
          </div>
        </div>
      </header>

      {/* Erreur */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg flex justify-between">
          <span>{error}</span>
          <button onClick={clearError}>{'✕'}</button>
        </div>
      )}

      {/* Contenu principal */}
      <main className="p-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Gauche - Controles */}
          <div className="lg:col-span-3 space-y-4">
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
            <GlobalStats world={world} onShowInfluence={() => setActiveTab('map')} />
            <Tier4List />
          </div>

          {/* Centre - Contenu principal */}
          <div className="lg:col-span-6">
            {/* Onglets simples */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setActiveTab('countries')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium ${
                  activeTab === 'countries' ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'
                }`}
              >
                {'🌍'} Pays ({world.countries.length})
              </button>
              <button
                onClick={() => setActiveTab('map')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium ${
                  activeTab === 'map' ? 'bg-cyan-600' : 'bg-gray-800 hover:bg-gray-700'
                }`}
              >
                {'🗺️'} Carte ({zones.length} zones)
              </button>
            </div>

            {/* Contenu des onglets */}
            {activeTab === 'countries' && (
              <div>
                {/* Filtres */}
                <div className="flex gap-2 mb-4">
                  {['all', 'tier1', 'tier2', 'tier3'].map(f => (
                    <button
                      key={f}
                      onClick={() => setFilter(f as typeof filter)}
                      className={`px-3 py-1.5 rounded-lg text-sm ${
                        filter === f ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'
                      }`}
                    >
                      {f === 'all' ? 'Tous' : f.toUpperCase()}
                    </button>
                  ))}
                </div>

                {/* Liste des pays */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto">
                  {sortedCountries.map(country => (
                    <CountryCard
                      key={country.id}
                      country={country}
                      isSelected={selectedCountry?.id === country.id}
                      onClick={() => selectCountry(selectedCountry?.id === country.id ? null : country.id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'map' && (
              <div className="space-y-4">
                <WorldMap
                  zones={zones}
                  onZoneClick={setSelectedZone}
                  selectedZoneId={selectedZone?.id}
                  highlightPower={selectedCountry?.id}
                />
                <InfluencePanel onZoneSelect={setSelectedZone} />
              </div>
            )}
          </div>

          {/* Droite - Evenements */}
          <div className="lg:col-span-3">
            <EventLog events={world.recent_events} maxEvents={20} />
          </div>
        </div>
      </main>

      {/* Modal pays */}
      {selectedCountry && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
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

      {/* Modal zone */}
      {selectedZone && (
        <ZoneDetailModal zone={selectedZone} onClose={() => setSelectedZone(null)} />
      )}

      {/* Modal sauvegarde */}
      <SaveLoadPanel
        currentYear={world.year}
        isOpen={showSaveLoad}
        onClose={() => setShowSaveLoad(false)}
        onGameLoaded={() => { fetchWorldState(); loadZones(); }}
      />
    </div>
  );
}
