"use client";

/**
 * NarrativeGame - Main component (PaxHistoria-style)
 *
 * Cold War Command Center aesthetic
 * Dark, immersive, dramatic
 */

import React, { useEffect, useState } from "react";
import {
  useNarrativeStore,
  selectDefconStatus,
  selectCanConfirm,
  selectTotalActionCost,
} from "@/stores/narrativeStore";
import CommandInput from "./CommandInput";
import IntentReview from "./IntentReview";
import ActionConfirm from "./ActionConfirm";
import TurnResolution from "./TurnResolution";
import PlayerStats from "./PlayerStats";
import DefconBanner from "./DefconBanner";
import NarrativeMap from "./NarrativeMap";
import { ActionQueue } from "./ActionQueue";
import { JumpForwardModal, JumpForwardButton } from "./JumpForwardModal";
import { EventPlayback } from "./EventPlayback";
import { LeaderPanel } from "./LeaderPanel";
import { DramaticWrapper, DefconOverlay, TensionVignette } from "./DramaticEffects";

export default function NarrativeGame() {
  const {
    isConnected,
    isLoading,
    error,
    date_display,
    current_phase,
    defcon,
    world_tension,
    player,
    zones,
    parsedIntentions,
    pendingActions,
    lastTurnResult,
    gameOver,
    victory,
    endReason,
    loadState,
    newGame,
    gamePhase,
    actionQueue,
    queueSummary,
  } = useNarrativeStore();

  const canConfirm = useNarrativeStore(selectCanConfirm);
  const totalCost = useNarrativeStore(selectTotalActionCost);

  const [showJumpModal, setShowJumpModal] = useState(false);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  useEffect(() => {
    loadState();
  }, [loadState]);

  // Loading
  if (isLoading && !isConnected) {
    return <LoadingScreen />;
  }

  // Error
  if (error && !isConnected) {
    return <ErrorScreen error={error} onRetry={loadState} />;
  }

  // Game Over
  if (gameOver) {
    return (
      <GameOverScreen
        victory={victory}
        endReason={endReason}
        onNewGame={newGame}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white overflow-hidden">
      {/* DRAMATIC EFFECTS - Tension Overlay */}
      <TensionVignette tension={world_tension} />
      <DefconOverlay defcon={defcon} worldTension={world_tension} />

      {/* Scanlines overlay for CRT effect */}
      <div className="pointer-events-none fixed inset-0 z-50 bg-[repeating-linear-gradient(0deg,rgba(0,0,0,0.1)_0px,rgba(0,0,0,0.1)_1px,transparent_1px,transparent_2px)] opacity-30" />

      {/* Vignette */}
      <div className="pointer-events-none fixed inset-0 z-40 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.4)_100%)]" />

      {/* HEADER - War Room Style */}
      <header className="relative z-30 border-b border-cyan-900/30 bg-gradient-to-b from-[#0d1420] to-transparent">
        <div className="max-w-[1800px] mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Title + Date */}
            <div className="flex items-center gap-6">
              <div>
                <h1 className="text-lg font-mono tracking-[0.3em] text-cyan-400/80 uppercase">
                  Historia
                </h1>
                <div className="flex items-center gap-3 mt-1">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-mono text-slate-400">
                    {date_display}
                  </span>
                </div>
              </div>

              {/* Phase Badge */}
              <GamePhaseBadge phase={gamePhase} />
            </div>

            {/* Center: World Tension */}
            <WorldTensionGauge tension={world_tension} />

            {/* Right: DEFCON + Jump */}
            <div className="flex items-center gap-4">
              <DefconBanner level={defcon} />
              <JumpForwardButton onClick={() => setShowJumpModal(true)} />
            </div>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="relative z-20 max-w-[1800px] mx-auto px-6 py-4">
        <div className="grid grid-cols-12 gap-4 h-[calc(100vh-100px)]">

          {/* LEFT PANEL - Command Center */}
          <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
            {gamePhase === "accumulating" && (
              <>
                <CommandInput />
                <div className="flex-1 overflow-auto">
                  <ActionQueue />
                </div>

                {current_phase === "intent_review" && (
                  <IntentReview intentions={parsedIntentions} />
                )}
                {current_phase === "action_confirm" && (
                  <ActionConfirm
                    actions={pendingActions}
                    totalCost={totalCost}
                    playerCapital={player.political_capital}
                    canConfirm={canConfirm}
                  />
                )}
              </>
            )}

            {gamePhase === "jumping" && <JumpingIndicator />}

            {lastTurnResult && gamePhase === "accumulating" && (
              <TurnResolution result={lastTurnResult} />
            )}
          </div>

          {/* CENTER - Strategic Map */}
          <div className="col-span-6">
            <div className="h-full rounded-lg overflow-hidden border border-cyan-900/30 bg-[#0d1420]">
              <NarrativeMap
                zones={zones}
                selectedZone={selectedZone}
                onZoneClick={setSelectedZone}
              />
            </div>
          </div>

          {/* RIGHT PANEL - Intelligence + Adversary */}
          <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
            {/* Leader contextuel - change selon la zone */}
            <LeaderPanel
              selectedZone={selectedZone}
              defcon={defcon}
              worldTension={world_tension}
            />

            <PlayerStats player={player} />

            {/* Intel Panel */}
            <IntelPanel
              intelExposure={player.intel_exposure}
              selectedZone={selectedZone ? zones[selectedZone] : null}
            />

            {/* Queue Summary */}
            {queueSummary && queueSummary.count > 0 && (
              <QueueSummaryCard summary={queueSummary} />
            )}

            {/* Quick Actions */}
            <div className="mt-auto">
              <button
                onClick={() => newGame()}
                className="w-full px-4 py-2 text-xs font-mono uppercase tracking-wider text-slate-500 hover:text-slate-300 border border-slate-800 hover:border-slate-700 rounded transition-colors"
              >
                Nouvelle Partie
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Loading Overlay */}
      {isLoading && gamePhase !== "jumping" && gamePhase !== "playback" && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm font-mono text-cyan-400/60">TRAITEMENT...</p>
          </div>
        </div>
      )}

      {/* Modals */}
      <JumpForwardModal
        isOpen={showJumpModal}
        onClose={() => setShowJumpModal(false)}
      />
      <EventPlayback />
    </div>
  );
}

// =============================================================================
// SUB COMPONENTS
// =============================================================================

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-24 h-24 mx-auto mb-6">
          <div className="absolute inset-0 border-2 border-cyan-500/20 rounded-full" />
          <div className="absolute inset-0 border-2 border-transparent border-t-cyan-500 rounded-full animate-spin" />
          <div className="absolute inset-3 border border-cyan-500/10 rounded-full" />
        </div>
        <h2 className="text-lg font-mono tracking-[0.3em] text-cyan-400/60 uppercase">
          Initialisation
        </h2>
        <p className="text-xs text-slate-600 mt-2 font-mono">
          HISTORIA NARRATIVE SYSTEM
        </p>
      </div>
    </div>
  );
}

function ErrorScreen({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
          <span className="text-2xl">!</span>
        </div>
        <h2 className="text-lg font-mono text-red-400 mb-2">ERREUR SYSTEME</h2>
        <p className="text-sm text-slate-500 mb-6">{error}</p>
        <button
          onClick={onRetry}
          className="px-6 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-sm font-mono text-cyan-400 transition-colors"
        >
          RECONNECTER
        </button>
      </div>
    </div>
  );
}

function GamePhaseBadge({ phase }: { phase: string | undefined }) {
  const config: Record<string, { label: string; color: string }> = {
    accumulating: { label: "PLANIFICATION", color: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10" },
    jumping: { label: "RESOLUTION", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
    playback: { label: "EVENEMENTS", color: "text-purple-400 border-purple-500/30 bg-purple-500/10" },
  };

  const c = config[phase || "accumulating"] || config.accumulating;

  return (
    <div className={`px-3 py-1 rounded border text-xs font-mono tracking-wider ${c.color}`}>
      {c.label}
    </div>
  );
}

function WorldTensionGauge({ tension }: { tension: number }) {
  const getColor = () => {
    if (tension >= 80) return "from-red-500 to-red-600";
    if (tension >= 60) return "from-orange-500 to-red-500";
    if (tension >= 40) return "from-yellow-500 to-orange-500";
    return "from-green-500 to-yellow-500";
  };

  return (
    <div className="flex items-center gap-4">
      <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">
        Tension Mondiale
      </span>
      <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${getColor()} transition-all duration-500`}
          style={{ width: `${tension}%` }}
        />
      </div>
      <span className={`text-sm font-mono font-bold ${
        tension >= 80 ? "text-red-400" : tension >= 60 ? "text-orange-400" : "text-slate-400"
      }`}>
        {tension}%
      </span>
    </div>
  );
}

function JumpingIndicator() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center p-8">
        <div className="relative w-20 h-20 mx-auto mb-6">
          <div className="absolute inset-0 border-2 border-amber-500/30 rounded-full animate-ping" />
          <div className="absolute inset-0 border-2 border-amber-500/50 rounded-full animate-pulse" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl">&#9889;</span>
          </div>
        </div>
        <h3 className="text-sm font-mono text-amber-400 tracking-wider uppercase mb-2">
          Resolution en cours
        </h3>
        <p className="text-xs text-slate-500">
          Generation des evenements...
        </p>
      </div>
    </div>
  );
}

function IntelPanel({
  intelExposure,
  selectedZone
}: {
  intelExposure: number;
  selectedZone: { name_fr: string; influence_us: number; influence_ussr: number; stability: number } | null;
}) {
  return (
    <div className="bg-[#0d1420] border border-cyan-900/30 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
        <h3 className="text-xs font-mono tracking-wider text-cyan-400/80 uppercase">
          Renseignement
        </h3>
      </div>

      <div className="space-y-3">
        {/* Intel Exposure */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500">Exposition</span>
            <span className={
              intelExposure > 70 ? "text-red-400" :
              intelExposure > 40 ? "text-yellow-400" : "text-green-400"
            }>
              {intelExposure}%
            </span>
          </div>
          <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                intelExposure > 70 ? "bg-red-500" :
                intelExposure > 40 ? "bg-yellow-500" : "bg-green-500"
              }`}
              style={{ width: `${intelExposure}%` }}
            />
          </div>
        </div>

        {/* Selected Zone Intel */}
        {selectedZone && (
          <div className="pt-3 border-t border-slate-800">
            <h4 className="text-xs text-slate-400 mb-2">{selectedZone.name_fr}</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-400">US</span>
                <span className="text-slate-500 ml-2">{selectedZone.influence_us}%</span>
              </div>
              <div>
                <span className="text-red-400">URSS</span>
                <span className="text-slate-500 ml-2">{selectedZone.influence_ussr}%</span>
              </div>
            </div>
          </div>
        )}

        {/* USSR Intel */}
        <div className="pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            {intelExposure < 40
              ? "Intel limitee sur l'URSS"
              : "Sources actives en URSS"}
          </div>
        </div>
      </div>
    </div>
  );
}

function QueueSummaryCard({ summary }: { summary: { count: number; total_cost: number; has_high_risk: boolean } }) {
  return (
    <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-blue-400/80 uppercase tracking-wider">
          Actions en queue
        </span>
        <span className="text-sm font-mono text-amber-400">
          {summary.total_cost} pts
        </span>
      </div>
      <div className="text-lg font-mono text-white">
        {summary.count} action{summary.count > 1 ? "s" : ""}
      </div>
      {summary.has_high_risk && (
        <div className="mt-2 text-xs text-orange-400">
          Actions risquees incluses
        </div>
      )}
    </div>
  );
}

function GameOverScreen({
  victory,
  endReason,
  onNewGame,
}: {
  victory: boolean | null;
  endReason: string | null;
  onNewGame: () => void;
}) {
  const reasons: Record<string, { title: string; description: string }> = {
    apocalypse: {
      title: "APOCALYPSE NUCLEAIRE",
      description: "Le monde n'est plus que cendres et radiation.",
    },
    coup_etat: {
      title: "COUP D'ETAT",
      description: "Votre gouvernement a ete renverse.",
    },
    domination: {
      title: "HEGEMONIE AMERICAINE",
      description: "Les Etats-Unis dominent le monde libre.",
    },
    adversary_collapse: {
      title: "EFFONDREMENT SOVIETIQUE",
      description: "L'Empire rouge s'est effondre.",
    },
    survival: {
      title: "SURVIE",
      description: "Vous avez traverse la Guerre Froide.",
    },
    defeat_honorable: {
      title: "DEFAITE",
      description: "L'URSS a prevalu.",
    },
  };

  const reason = reasons[endReason || ""] || {
    title: "FIN DE PARTIE",
    description: "La partie est terminee.",
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
      <div className="text-center max-w-lg">
        <div className={`text-6xl font-mono font-bold mb-4 ${
          victory ? "text-cyan-400" : "text-red-500"
        }`}>
          {victory ? "VICTOIRE" : "DEFAITE"}
        </div>
        <h2 className="text-xl font-mono text-slate-300 mb-2">{reason.title}</h2>
        <p className="text-slate-500 mb-8">{reason.description}</p>
        <button
          onClick={onNewGame}
          className="px-8 py-3 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-sm font-mono text-cyan-400 uppercase tracking-wider transition-colors"
        >
          Nouvelle Partie
        </button>
      </div>
    </div>
  );
}
