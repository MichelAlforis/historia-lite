'use client';

import { useEffect, useState, useCallback, memo } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { COUNTRY_FLAGS } from '@/lib/types';
import dynamic from 'next/dynamic';
import { Zap, MessageCircle, Lightbulb, Loader2, X, Users, ChevronRight, ChevronLeft, Grid3X3, Map, Calendar } from 'lucide-react';
import { useMemo } from 'react';

// Static components (lightweight, always needed)
import CountrySelector from '@/components/CountrySelector';
import VideoSkeleton from '@/components/VideoSkeleton';
import EventToast from '@/components/EventToast';

// API
import { getScenarioStatus, ScenarioStatus } from '@/lib/api';

// ==================== LAZY LOADED COMPONENTS ====================
// Heavy modals loaded only when opened - reduces initial bundle size

const ActionDropup = dynamic(() => import('@/components/ActionDropup'), {
  loading: () => null,
});

const DialogueDropup = dynamic(() => import('@/components/DialogueDropup'), {
  loading: () => null,
});

const AdvisorDropleft = dynamic(() => import('@/components/AdvisorDropleft'), {
  loading: () => null,
});

const VictoryScreen = dynamic(() => import('@/components/game/VictoryScreen'), {
  loading: () => <VideoSkeleton message="Chargement..." variant="minimalist" />,
});

const DefeatScreen = dynamic(() => import('@/components/game/DefeatScreen'), {
  loading: () => <VideoSkeleton message="Chargement..." variant="minimalist" />,
});

const EventHistorySidebar = dynamic(() => import('@/components/EventHistorySidebar'), {
  loading: () => <SidebarLoader />,
});

const RelationsPanel = dynamic(() => import('@/components/RelationsPanel'), {
  loading: () => <SidebarLoader />,
});

const RelationMatrix = dynamic(() => import('@/components/RelationMatrix'), {
  loading: () => <ModalLoader />,
});

const TimelineModal = dynamic(() => import('@/components/TimelineModal'), {
  loading: () => <ModalLoader />,
});

// Map - no SSR, heavy component with WebGL
const WorldMapGL = dynamic(() => import('@/components/map/WorldMapGL'), {
  ssr: false,
  loading: () => (
    <VideoSkeleton message="Chargement de la carte..." variant="minimalist" />
  ),
});

// ==================== LOADING COMPONENTS ====================

function ModalLoader() {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 flex items-center gap-3">
        <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
        <span className="text-gray-300">Chargement...</span>
      </div>
    </div>
  );
}

function SidebarLoader() {
  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-gray-800/90 backdrop-blur flex items-center justify-center z-40">
      <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
    </div>
  );
}

export default function PaxPage() {
  const {
    world,
    isLoading,
    error,
    playerCountryId,
    pendingDilemmas,
    tier4Countries,
    tier5Countries,
    tier6Countries,
    regions,
    fetchWorldState,
    fetchAllTiers,
    fetchRegions,
    checkPlayerCountry,
    selectPlayerCountry,
    fetchPendingDilemmas,
    resetWorld,
    clearError,
    recentTickEvents,
    showEventToast,
    dismissEventToast,
    // Timeline state (NEW)
    year,
    month,
    dateDisplayFr,
    viewingDate,
    unreadEventCount,
    timelineModalOpen,
    // Timeline actions (NEW)
    advanceMonth,
    goToPreviousMonth,
    goToNextMonth,
    openTimelineModal,
    closeTimelineModal,
    canGoBack,
  } = useGameStore();

  // Modal states
  const [showAgir, setShowAgir] = useState(false);
  const [showDiscuter, setShowDiscuter] = useState(false);
  const [showConseil, setShowConseil] = useState(false);
  const [showEventHistory, setShowEventHistory] = useState(false);
  const [showRelations, setShowRelations] = useState(false);
  const [showMatrix, setShowMatrix] = useState(false);

  // Map view mode
  const [mapViewMode, setMapViewMode] = useState<'power' | 'relations'>('power');

  // Selected country on map
  const [selectedMapCountry, setSelectedMapCountry] = useState<string | null>(null);

  // Scenario status for victory/defeat
  const [scenarioStatus, setScenarioStatus] = useState<ScenarioStatus | null>(null);
  const [startYear, setStartYear] = useState<number>(2025);

  // Fetch scenario status
  const fetchScenarioStatus = useCallback(async () => {
    try {
      const status = await getScenarioStatus();
      setScenarioStatus(status);
    } catch {
      // Scenario system not active, ignore
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchWorldState();
    fetchAllTiers();
    fetchRegions();
    checkPlayerCountry();
    fetchScenarioStatus();
  }, [fetchWorldState, fetchAllTiers, fetchRegions, checkPlayerCountry, fetchScenarioStatus]);

  // Track start year when world loads
  useEffect(() => {
    if (world && startYear === 2025) {
      setStartYear(world.year);
    }
  }, [world, startYear]);

  // Fetch dilemmas when player country is set
  useEffect(() => {
    if (playerCountryId) {
      fetchPendingDilemmas();
    }
  }, [playerCountryId, fetchPendingDilemmas]);

  // Handle country selection at game start
  const handleSelectCountry = async (countryId: string) => {
    await selectPlayerCountry(countryId);
  };


  // Handle restart game
  const handleRestart = useCallback(async () => {
    setScenarioStatus(null);
    setStartYear(2025);
    await resetWorld();
    await fetchWorldState();
    await fetchScenarioStatus();
  }, [resetWorld, fetchWorldState, fetchScenarioStatus]);

  // Handle return to main menu (country selection)
  const handleMainMenu = useCallback(() => {
    setScenarioStatus(null);
    setStartYear(2025);
    // Reset to show country selector
    window.location.reload();
  }, []);

  // Filter events to only show those relevant to player country
  // NOTE: Must be called before any conditional returns to respect React hooks rules
  const playerEvents = useMemo(() => {
    return recentTickEvents.filter(event =>
      event.country_id === playerCountryId ||
      event.target_id === playerCountryId
    );
  }, [recentTickEvents, playerCountryId]);

  // Loading state
  if (!world) {
    if (error) {
      return (
        <div className="min-h-screen bg-stone-900 flex items-center justify-center">
          <div className="bg-white/10 backdrop-blur-md rounded-2xl shadow-lg p-8 text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={() => { clearError(); fetchWorldState(); }}
              className="px-6 py-2 bg-amber-500 text-stone-900 rounded-xl hover:bg-amber-400 transition font-medium"
            >
              Reessayer
            </button>
          </div>
        </div>
      );
    }
    return <VideoSkeleton message="Chargement du monde..." variant="globe" />;
  }

  // Country selection screen (no player country yet)
  if (!playerCountryId) {
    return <CountrySelector onSelect={handleSelectCountry} />;
  }

  // Game end screens (victory or defeat)
  const yearsPlayed = world.year - startYear;

  // Check for victory via scenario system
  if (scenarioStatus?.is_complete) {
    const objectives = scenarioStatus.objectives.map(obj => ({
      id: obj.id,
      name: obj.name,
      status: obj.status as 'completed' | 'failed' | 'pending',
      points: obj.points,
    }));

    return (
      <VictoryScreen
        scenarioName={scenarioStatus.scenario_name || 'Partie libre'}
        finalScore={scenarioStatus.total_score}
        maxScore={scenarioStatus.max_possible_score}
        yearsPlayed={yearsPlayed}
        objectives={objectives}
        onRestart={handleRestart}
        onMainMenu={handleMainMenu}
      />
    );
  }

  // Check for defeat via scenario system or game_ended
  if (scenarioStatus?.is_failed || world.game_ended) {
    const objectives = scenarioStatus?.objectives.map(obj => ({
      id: obj.id,
      name: obj.name,
      status: obj.status as 'completed' | 'failed' | 'pending',
      points: obj.points,
    })) || [];

    return (
      <DefeatScreen
        scenarioName={scenarioStatus?.scenario_name || 'Partie libre'}
        finalScore={scenarioStatus?.total_score || world.final_score || 0}
        maxScore={scenarioStatus?.max_possible_score || 100}
        yearsPlayed={yearsPlayed}
        reason={world.game_end_reason || 'unknown'}
        reasonFr={world.game_end_message_fr || world.game_end_message || 'Cause inconnue'}
        objectives={objectives}
        onRestart={handleRestart}
        onMainMenu={handleMainMenu}
      />
    );
  }

  // Get player country data
  const playerCountry = world.countries.find(c => c.id === playerCountryId);
  const selectedCountry = selectedMapCountry
    ? world.countries.find(c => c.id === selectedMapCountry)
    : null;

  return (
    <div className="h-screen bg-amber-50 flex flex-col overflow-hidden relative">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-stone-200 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Player country + Timeline Navigation */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{COUNTRY_FLAGS[playerCountryId] || '🏳️'}</span>
              <div>
                <h1 className="text-lg font-medium text-stone-800">
                  {playerCountry?.name || playerCountryId}
                </h1>
                <span className="text-xs text-stone-500">Votre nation</span>
              </div>
            </div>

            {/* Timeline Navigation: ◀ Date ▶ */}
            <div className="flex items-center gap-2 bg-stone-100 rounded-xl px-2 py-1">
              {/* Previous month button */}
              <button
                onClick={goToPreviousMonth}
                disabled={!canGoBack()}
                className="p-2 hover:bg-white rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed"
                title="Mois precedent"
              >
                <ChevronLeft className="w-5 h-5 text-stone-600" />
              </button>

              {/* Current date - clickable to open timeline modal */}
              <button
                onClick={openTimelineModal}
                className="min-w-[140px] text-center px-3 py-1 hover:bg-white rounded-lg transition group"
                title="Ouvrir la chronologie"
              >
                <span className="text-xl font-light text-stone-700 group-hover:text-indigo-600 transition">
                  {viewingDate ? viewingDate.display_fr : dateDisplayFr}
                </span>
                {unreadEventCount > 0 && (
                  <span className="ml-2 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-full">
                    {unreadEventCount}
                  </span>
                )}
              </button>

              {/* Next month / Advance button */}
              <button
                onClick={goToNextMonth}
                disabled={isLoading}
                className="p-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg transition disabled:opacity-50"
                title={viewingDate ? "Mois suivant" : "Avancer d'un mois"}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-4">
            {/* DEFCON */}
            <div className={`px-4 py-1.5 rounded-full text-sm font-medium ${
              world.defcon_level <= 2
                ? 'bg-red-100 text-red-700'
                : world.defcon_level <= 3
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-emerald-100 text-emerald-700'
            }`}>
              DEFCON {world.defcon_level}
            </div>

            {/* Tension */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-stone-500">Tension</span>
              <div className="w-20 h-2 bg-stone-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    world.global_tension >= 70 ? 'bg-red-400' :
                    world.global_tension >= 40 ? 'bg-amber-400' : 'bg-emerald-400'
                  }`}
                  style={{ width: `${world.global_tension}%` }}
                />
              </div>
              <span className="text-sm text-stone-600">{world.global_tension}%</span>
            </div>

            {/* Dilemmas badge */}
            {pendingDilemmas.length > 0 && (
              <button
                onClick={() => setShowDiscuter(true)}
                className="px-3 py-1.5 bg-rose-100 text-rose-700 rounded-full text-sm font-medium
                  hover:bg-rose-200 transition animate-pulse"
              >
                {pendingDilemmas.length} dialogue{pendingDilemmas.length > 1 ? 's' : ''}
              </button>
            )}

            {/* Relations buttons */}
            <div className="flex items-center gap-1 bg-stone-100 rounded-xl p-1">
              <button
                onClick={() => setShowRelations(true)}
                className="p-2 hover:bg-white rounded-lg transition"
                title="Relations diplomatiques"
              >
                <Users className="w-4 h-4 text-stone-500" />
              </button>
              <button
                onClick={() => setShowMatrix(true)}
                className="p-2 hover:bg-white rounded-lg transition"
                title="Matrice des relations"
              >
                <Grid3X3 className="w-4 h-4 text-stone-500" />
              </button>
              <button
                onClick={() => setMapViewMode(mapViewMode === 'power' ? 'relations' : 'power')}
                className={`p-2 rounded-lg transition ${
                  mapViewMode === 'relations' ? 'bg-violet-500 text-white' : 'hover:bg-white text-stone-500'
                }`}
                title={mapViewMode === 'power' ? 'Vue relations' : 'Vue puissance'}
              >
                <Map className="w-4 h-4" />
              </button>
            </div>

            {/* Timeline button (opens full history modal) */}
            <button
              onClick={openTimelineModal}
              className="flex items-center gap-2 px-3 py-2 bg-stone-100 hover:bg-white rounded-xl transition"
              title="Voir toute la chronologie"
            >
              <Calendar className="w-4 h-4 text-stone-500" />
              <span className="text-sm font-medium text-stone-600">Historique</span>
              {unreadEventCount > 0 && (
                <span className="px-1.5 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-full">
                  {unreadEventCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main content - Map (extends under footer) */}
      <main className="absolute inset-0 top-[72px]">
        <WorldMapGL
          countries={world.countries}
          tier4Countries={tier4Countries}
          tier5Countries={tier5Countries}
          tier6Countries={tier6Countries}
          regions={regions}
          selectedCountryId={selectedMapCountry}
          onCountryClick={(id) => setSelectedMapCountry(id)}
          viewMode={mapViewMode}
          playerCountryId={playerCountryId}
          playerRelations={playerCountry?.relations || {}}
          playerAllies={playerCountry?.allies || []}
          playerRivals={playerCountry?.rivals || []}
          playerAtWar={playerCountry?.at_war || []}
        />

        {/* Country info panel (when country selected on map) */}
        {selectedCountry && (
          <div className="absolute top-4 right-4 w-80 bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="bg-gradient-to-r from-sky-500 to-indigo-500 px-5 py-4 text-white">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{COUNTRY_FLAGS[selectedCountry.id] || '🏳️'}</span>
                  <div>
                    <h3 className="text-lg font-semibold">{selectedCountry.name}</h3>
                    <span className="text-sky-100 text-sm">Tier {selectedCountry.tier}</span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedMapCountry(null)}
                  className="text-white/70 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-4 space-y-3">
              <StatBar label="Economie" value={selectedCountry.economy} color="emerald" />
              <StatBar label="Militaire" value={selectedCountry.military} color="rose" />
              <StatBar label="Technologie" value={selectedCountry.technology} color="sky" />
              <StatBar label="Stabilite" value={selectedCountry.stability} color="amber" />
              <div className="pt-2 border-t border-stone-100 text-sm text-stone-500">
                Score de puissance: <span className="font-medium text-stone-700">{selectedCountry.power_score}</span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Bottom action bar */}
      <footer className="fixed bottom-0 left-0 right-0 bg-transparent px-6 py-3 z-20">
        <div className="flex items-center justify-center">
          {/* Cadre autour des 2 boutons principaux - meme style que header */}
          <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-stone-200 rounded-xl p-2">
            {/* AGIR */}
            <button
              onClick={() => setShowAgir(true)}
              disabled={isLoading}
              className="group flex items-center gap-1 px-3 py-1.5 bg-emerald-600 text-white rounded-lg
                hover:bg-emerald-500 transition-all duration-200 disabled:opacity-50 text-xs"
            >
              <Zap className="w-3 h-3" />
              <span className="font-medium">AGIR</span>
            </button>

            {/* DISCUTER */}
            <button
              onClick={() => setShowDiscuter(true)}
              disabled={isLoading}
              className={`group relative flex items-center gap-1 px-3 py-1.5 rounded-lg
                transition-all duration-200 disabled:opacity-50 text-xs ${
                  pendingDilemmas.length > 0
                    ? 'bg-sky-500 text-white ring-1 ring-sky-300 hover:bg-sky-400'
                    : 'bg-sky-600 text-white hover:bg-sky-500'
                }`}
            >
              <MessageCircle className="w-3 h-3" />
              <span className="font-medium">DISCUTER</span>
              {pendingDilemmas.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center
                  bg-rose-500 text-white text-[10px] rounded-full font-bold">
                  {pendingDilemmas.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* CONSEIL - onglet vertical a droite */}
        <button
          onClick={() => setShowConseil(true)}
          disabled={isLoading}
          className="fixed bottom-3 right-0 flex flex-col items-center justify-center py-2 px-1.5
            bg-white border border-stone-200 border-r-0 rounded-l-lg shadow-md
            hover:bg-amber-50 transition-all duration-200 disabled:opacity-50"
        >
          <Lightbulb className="w-4 h-4 text-amber-500" />
        </button>
      </footer>

      {/* Modals */}
      <ActionDropup isOpen={showAgir} onClose={() => setShowAgir(false)} />
      <DialogueDropup isOpen={showDiscuter} onClose={() => setShowDiscuter(false)} />
      <AdvisorDropleft isOpen={showConseil} onClose={() => setShowConseil(false)} />

      {/* Event Toast - Only player country events */}
      {showEventToast && playerEvents.length > 0 && (
        <EventToast
          events={playerEvents}
          onDismiss={dismissEventToast}
          onViewHistory={() => {
            dismissEventToast();
            setShowEventHistory(true);
          }}
        />
      )}

      {/* Event History Sidebar */}
      <EventHistorySidebar
        isOpen={showEventHistory}
        onClose={() => setShowEventHistory(false)}
      />

      {/* Relations Panel */}
      <RelationsPanel
        isOpen={showRelations}
        onClose={() => setShowRelations(false)}
      />

      {/* Relation Matrix */}
      <RelationMatrix
        isOpen={showMatrix}
        onClose={() => setShowMatrix(false)}
        onCountrySelect={(countryId) => {
          setShowMatrix(false);
          setSelectedMapCountry(countryId);
        }}
      />

      {/* Timeline Modal - Full history navigation */}
      <TimelineModal
        isOpen={timelineModalOpen}
        onClose={closeTimelineModal}
      />
    </div>
  );
}

// Mini stat bar component
function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-400',
    rose: 'bg-rose-400',
    sky: 'bg-sky-400',
    amber: 'bg-amber-400',
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-stone-500 w-20">{label}</span>
      <div className="flex-1 h-2 bg-stone-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-stone-600 w-8 text-right">{value}</span>
    </div>
  );
}
