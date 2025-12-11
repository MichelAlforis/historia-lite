'use client';

import { useEffect, useState, useCallback } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { WorldMapGL, RegionAttackPanel } from '@/components/map';
import {
  TIER_NAMES,
  COUNTRY_FLAGS,
  SubnationalRegion,
} from '@/lib/types';
import Link from 'next/link';
import { ToastProvider, useToast } from '@/components/ui/Toast';

// Inner component that uses toast
function PaxMapContent() {
  const {
    world,
    isLoading,
    error,
    autoPlay,
    fetchWorldState,
    advanceTick,
    setAutoPlay,
    clearError,
    tier4Countries,
    tier5Countries,
    tier6Countries,
    fetchAllTiers,
    regions,
    regionsSummary,
    selectedRegionId,
    fetchRegions,
    selectRegion,
    executeRegionAttack,
    lastAttackResult,
  } = useGameStore();

  const { addToast } = useToast();

  const [selectedCountryId, setSelectedCountryId] = useState<string | null>(null);
  const [highlightedInfluence, setHighlightedInfluence] = useState<string[]>([]);
  const [showAttackPanel, setShowAttackPanel] = useState(false);
  const [showAttackResult, setShowAttackResult] = useState(false);

  // Initial data fetch
  useEffect(() => {
    fetchWorldState();
    fetchAllTiers();
    fetchRegions();
  }, [fetchWorldState, fetchAllTiers, fetchRegions]);

  // Auto-play
  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(advanceTick, 2000);
    return () => clearInterval(interval);
  }, [autoPlay, advanceTick]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        advanceTick();
      } else if (e.code === 'KeyP') {
        setAutoPlay(!autoPlay);
      } else if (e.code === 'Escape') {
        setSelectedCountryId(null);
        selectRegion(null);
        setHighlightedInfluence([]);
        setShowAttackPanel(false);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [advanceTick, autoPlay, setAutoPlay, selectRegion]);

  // Handle country selection - highlight influence sphere
  const handleCountryClick = useCallback((countryId: string) => {
    setSelectedCountryId(countryId);
    selectRegion(null);
    setShowAttackPanel(false);

    // Find countries under this country's influence
    const country = world?.countries.find(c => c.id === countryId);
    if (country && country.tier <= 2) {
      // For major powers, show their sphere of influence
      const influenced = [
        ...(country.allies || []),
        ...(country.sphere_of_influence || []),
      ];
      setHighlightedInfluence(influenced);
    } else {
      // For smaller countries, show their protector
      const tier4 = tier4Countries.find(c => c.id === countryId);
      const tier5 = tier5Countries.find(c => c.id === countryId);
      const tier6 = tier6Countries.find(c => c.id === countryId);

      const protector = tier6?.protector || tier5?.protector || null;
      if (protector) {
        setHighlightedInfluence([protector]);
      } else {
        setHighlightedInfluence([]);
      }
    }
  }, [world, tier4Countries, tier5Countries, tier6Countries, selectRegion]);

  // Handle region selection
  const handleRegionClick = useCallback((regionId: string) => {
    selectRegion(regionId);
    setShowAttackPanel(true);
  }, [selectRegion]);

  // Handle attack - get player country or default to USA
  const getPlayerCountry = useCallback(() => {
    const playerCountry = world?.countries.find(c => c.is_player);
    return playerCountry?.id || 'USA';
  }, [world]);

  // Handle attack
  const handleAttack = useCallback(async (regionId: string, attackType: string) => {
    const attackerId = getPlayerCountry();
    setShowAttackPanel(false);

    const result = await executeRegionAttack(regionId, attackType, attackerId);
    if (result) {
      setShowAttackResult(true);
      // Auto-hide after 5 seconds
      setTimeout(() => setShowAttackResult(false), 5000);

      // Show toast based on result
      if (result.success) {
        addToast('success', 'Attaque reussie', result.message_fr);
      } else {
        addToast('warning', 'Attaque repoussee', result.message_fr);
      }
    } else {
      addToast('error', 'Erreur', 'L\'attaque a echoue');
    }
  }, [executeRegionAttack, getPlayerCountry, addToast]);

  // Get selected region
  const selectedRegion = selectedRegionId
    ? regions.find(r => r.id === selectedRegionId)
    : null;

  if (!world) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          {error ? (
            <div className="bg-slate-800 rounded-2xl shadow-lg p-8">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={() => { clearError(); fetchWorldState(); }}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
              >
                Reessayer
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-slate-400">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-lg">Chargement...</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Type for selected country
  type SelectedCountry = {
    id: string;
    name?: string;
    name_fr: string;
    tier?: number;
    economy: number;
    military?: number;
    stability: number;
    technology?: number;
  } | null;

  const selectedCountry: SelectedCountry = selectedCountryId
    ? world.countries.find(c => c.id === selectedCountryId) ||
      tier4Countries.find(c => c.id === selectedCountryId) ||
      tier5Countries.find(c => c.id === selectedCountryId) ||
      tier6Countries.find(c => c.id === selectedCountryId) ||
      null
    : null;

  // Country regions
  const countryRegions = selectedCountryId
    ? regions.filter(r => r.country_id === selectedCountryId)
    : [];

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800/90 backdrop-blur-sm border-b border-slate-700 px-4 py-3 sticky top-0 z-20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link
              href="/pax"
              className="text-slate-400 hover:text-white transition text-sm"
            >
              ← Liste
            </Link>
            <h1 className="text-xl font-light tracking-wide text-white">
              <span className="font-semibold">Pax</span>
              <span className="text-slate-400 ml-2">Mundi</span>
              <span className="text-blue-400 ml-3 text-2xl font-extralight">{world.year}</span>
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* DEFCON badge */}
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              world.defcon_level <= 2
                ? 'bg-red-500/20 text-red-400 ring-1 ring-red-500/30'
                : world.defcon_level <= 3
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              DEFCON {world.defcon_level}
            </div>

            {/* Tension meter */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Tension</span>
              <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    world.global_tension >= 70 ? 'bg-red-500' :
                    world.global_tension >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${world.global_tension}%` }}
                />
              </div>
              <span className="text-xs font-medium text-slate-300">{world.global_tension}%</span>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={advanceTick}
                disabled={isLoading}
                className="px-4 py-1.5 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition shadow-sm disabled:opacity-50"
              >
                {isLoading ? '...' : 'Avancer'}
              </button>
              <button
                onClick={() => setAutoPlay(!autoPlay)}
                className={`px-3 py-1.5 rounded-lg text-sm transition ${
                  autoPlay
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {autoPlay ? 'Stop' : 'Auto'}
              </button>
            </div>

            {/* Regions summary */}
            {regionsSummary && (
              <div className="text-xs text-slate-400 border-l border-slate-700 pl-4">
                {regionsSummary.total} regions | {Object.keys(regionsSummary.by_country).length} pays
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content - Map */}
      <div className="flex-1 relative">
        <WorldMapGL
          countries={world.countries}
          tier4Countries={tier4Countries}
          tier5Countries={tier5Countries}
          tier6Countries={tier6Countries}
          regions={regions}
          selectedCountryId={selectedCountryId}
          selectedRegionId={selectedRegionId}
          highlightedInfluence={highlightedInfluence}
          onCountryClick={handleCountryClick}
          onRegionClick={handleRegionClick}
          viewMode="power"
          showRegions={true}
        />

        {/* Selected country info panel */}
        {selectedCountry && (
          <div className="absolute top-4 right-4 w-80 bg-slate-800/95 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700">
            <div className="p-4 border-b border-slate-700">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <span>{COUNTRY_FLAGS[selectedCountryId!] || ''}</span>
                    <span>{selectedCountry.name_fr || selectedCountry.name}</span>
                  </h2>
                  <p className="text-slate-400 text-sm">
                    Tier {selectedCountry.tier || 4}
                    {countryRegions.length > 0 && ` | ${countryRegions.length} regions`}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedCountryId(null);
                    selectRegion(null);
                    setHighlightedInfluence([]);
                  }}
                  className="text-slate-400 hover:text-white transition"
                >
                  x
                </button>
              </div>
            </div>

            {/* Country stats */}
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <StatBar label="Economie" value={selectedCountry.economy} color="emerald" />
                {selectedCountry.military !== undefined && (
                  <StatBar label="Militaire" value={selectedCountry.military} color="red" />
                )}
                <StatBar label="Stabilite" value={selectedCountry.stability} color="amber" />
                {selectedCountry.technology !== undefined && (
                  <StatBar label="Tech" value={selectedCountry.technology} color="blue" />
                )}
              </div>

              {/* Regions list for this country */}
              {countryRegions.length > 0 && (
                <div className="pt-3 border-t border-slate-700">
                  <h3 className="text-xs uppercase tracking-wide text-slate-400 mb-2">
                    Regions ({countryRegions.length})
                  </h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {countryRegions.map(region => (
                      <button
                        key={region.id}
                        onClick={() => handleRegionClick(region.id)}
                        className={`w-full text-left px-3 py-2 rounded text-xs transition ${
                          selectedRegionId === region.id
                            ? 'bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30'
                            : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <div className="flex justify-between">
                          <span className="font-medium">{region.name_fr}</span>
                          <span className="text-slate-400">{region.strategic_value}/10</span>
                        </div>
                        <div className="flex gap-2 mt-1 text-slate-400">
                          {region.is_capital_region && <span className="text-amber-400">Capitale</span>}
                          {region.is_coastal && <span className="text-blue-400">Cotiere</span>}
                          {region.has_oil && <span className="text-yellow-400">Petrole</span>}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Attack panel */}
        {showAttackPanel && selectedRegion && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
            <RegionAttackPanel
              region={selectedRegion}
              attackerId={getPlayerCountry()}
              onAttack={handleAttack}
              onClose={() => setShowAttackPanel(false)}
            />
          </div>
        )}

        {/* Attack result notification */}
        {showAttackResult && lastAttackResult && (
          <div className={`absolute top-20 left-1/2 -translate-x-1/2 z-40 p-4 rounded-lg shadow-xl border max-w-md ${
            lastAttackResult.success
              ? 'bg-emerald-900/95 border-emerald-500/50'
              : 'bg-red-900/95 border-red-500/50'
          }`}>
            <div className="flex items-start gap-3">
              <div className={`text-2xl ${lastAttackResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                {lastAttackResult.success ? '✓' : '✗'}
              </div>
              <div className="flex-1">
                <h3 className={`font-semibold ${lastAttackResult.success ? 'text-emerald-300' : 'text-red-300'}`}>
                  {lastAttackResult.message_fr}
                </h3>
                <div className="mt-2 text-sm text-slate-300 space-y-1">
                  <div className="flex justify-between">
                    <span>Degats infliges:</span>
                    <span className="text-white">{lastAttackResult.damage_dealt}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pertes attaquant:</span>
                    <span className="text-red-400">{lastAttackResult.casualties_attacker}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pertes defenseur:</span>
                    <span className="text-amber-400">{lastAttackResult.casualties_defender}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Degats region:</span>
                    <span className="text-orange-400">{lastAttackResult.region_damage}%</span>
                  </div>
                </div>
                {lastAttackResult.consequences.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-700">
                    <div className="text-xs text-slate-400 uppercase mb-1">Consequences</div>
                    <ul className="text-xs text-slate-300 space-y-0.5">
                      {lastAttackResult.consequences.map((c, i) => (
                        <li key={i}>- {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowAttackResult(false)}
                className="text-slate-400 hover:text-white"
              >
                x
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-slate-800/90 border-t border-slate-700 py-2">
        <div className="flex justify-center gap-8 text-xs text-slate-500">
          <span><kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">Espace</kbd> Avancer</span>
          <span><kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">P</kbd> Auto</span>
          <span><kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">Echap</kbd> Fermer</span>
        </div>
      </footer>
    </div>
  );
}

// Helper component
function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-500',
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
  };

  return (
    <div>
      <div className="flex justify-between text-slate-400 mb-1">
        <span>{label}</span>
        <span className="text-white">{value}</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

// Main export with ToastProvider wrapper
export default function PaxMapPage() {
  return (
    <ToastProvider>
      <PaxMapContent />
    </ToastProvider>
  );
}
