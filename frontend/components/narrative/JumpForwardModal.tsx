"use client";

/**
 * JumpForwardModal - Cold War Command Center Style
 *
 * Dramatic time-jump interface styled as military command console
 */

import React, { useState } from "react";
import { useNarrativeStore } from "@/stores/narrativeStore";

// =============================================================================
// DURATION OPTIONS
// =============================================================================

interface DurationOption {
  id: string;
  label: string;
  code: string;
  description: string;
}

const DURATION_OPTIONS: DurationOption[] = [
  {
    id: "week",
    label: "1 SEMAINE",
    code: "7D",
    description: "Cycle operationnel court",
  },
  {
    id: "month",
    label: "1 MOIS",
    code: "30D",
    description: "Cycle strategique standard",
  },
  {
    id: "quarter",
    label: "1 TRIMESTRE",
    code: "90D",
    description: "Periode de planification",
  },
  {
    id: "year",
    label: "1 AN",
    code: "365D",
    description: "Cycle geopolitique complet",
  },
  {
    id: "next_event",
    label: "PROCHAIN EVENEMENT",
    code: "EVT",
    description: "Jusqu'a la prochaine crise majeure",
  },
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface JumpForwardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function JumpForwardModal({ isOpen, onClose }: JumpForwardModalProps) {
  const [selectedDuration, setSelectedDuration] = useState("month");
  const {
    jumpForward,
    actionQueue,
    queueSummary,
    player,
    isLoading,
    gamePhase,
  } = useNarrativeStore();

  const handleJump = async () => {
    const success = await jumpForward(selectedDuration);
    if (success) {
      onClose();
    }
  };

  if (!isOpen) return null;

  const canJump =
    actionQueue.length > 0 &&
    !isLoading &&
    gamePhase === "accumulating" &&
    (queueSummary?.total_cost || 0) <= (player.available_capital || player.political_capital);

  const isOverBudget = (queueSummary?.total_cost || 0) > (player.available_capital || player.political_capital);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with scanlines */}
      <div
        className="absolute inset-0 bg-black/90 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[#0a0e17] border border-cyan-500/30 rounded-lg w-full max-w-lg mx-4 shadow-[0_0_50px_rgba(6,182,212,0.15)]">
        {/* Scanlines overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-20 rounded-lg overflow-hidden">
          <div className="absolute inset-0" style={{
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)',
          }} />
        </div>

        {/* Header */}
        <div className="relative px-5 py-4 border-b border-cyan-900/50 bg-[#080c14]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Animated indicator */}
              <div className="relative">
                <div className="w-3 h-3 rounded-full bg-amber-500 animate-pulse" />
                <div className="absolute inset-0 w-3 h-3 rounded-full bg-amber-500/50 animate-ping" />
              </div>
              <div>
                <h2 className="text-sm font-mono tracking-[0.2em] text-cyan-400 uppercase">
                  JUMP FORWARD
                </h2>
                <p className="text-xs font-mono text-slate-500 mt-0.5">
                  SIMULATION TEMPORELLE
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="text-slate-500 hover:text-cyan-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="relative p-5">
          {/* Queue Summary */}
          {queueSummary && queueSummary.count > 0 && (
            <div className="bg-[#080c14] border border-slate-800 rounded-lg p-4 mb-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                  Operations en attente
                </span>
                <span className="text-sm font-mono text-cyan-400">
                  {queueSummary.count} OP{queueSummary.count > 1 ? "S" : ""}
                </span>
              </div>

              {/* Cost bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs font-mono mb-1">
                  <span className="text-slate-500">COUT TOTAL</span>
                  <span className={isOverBudget ? "text-red-400" : "text-amber-400"}>
                    {queueSummary.total_cost} / {player.available_capital || player.political_capital} PTS
                  </span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${isOverBudget ? "bg-red-500" : "bg-amber-500"}`}
                    style={{
                      width: `${Math.min(100, (queueSummary.total_cost / (player.available_capital || player.political_capital)) * 100)}%`
                    }}
                  />
                </div>
              </div>

              {/* Warnings */}
              {(queueSummary.has_high_risk || isOverBudget) && (
                <div className="flex flex-wrap gap-2">
                  {queueSummary.has_high_risk && (
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-orange-400 bg-orange-500/10 px-2 py-1 rounded">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      OPERATIONS RISQUEES
                    </div>
                  )}
                  {isOverBudget && (
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-1 rounded">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      CAPITAL INSUFFISANT
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* No actions warning */}
          {actionQueue.length === 0 && (
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-5 mb-5 text-center">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-amber-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-xs font-mono text-amber-400/80 uppercase tracking-wider">
                Aucune operation en queue
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Ajoutez des ordres avant de lancer la simulation
              </p>
            </div>
          )}

          {/* Duration Selection */}
          <div>
            <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">
              Duree de la simulation
            </label>

            <div className="space-y-2">
              {DURATION_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setSelectedDuration(option.id)}
                  className={`w-full flex items-center gap-4 p-3 rounded-lg border transition-all ${
                    selectedDuration === option.id
                      ? "bg-cyan-500/10 border-cyan-500/50 text-cyan-300"
                      : "bg-[#080c14] border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  {/* Code badge */}
                  <div className={`w-12 h-8 rounded flex items-center justify-center font-mono text-xs ${
                    selectedDuration === option.id
                      ? "bg-cyan-500/20 text-cyan-400"
                      : "bg-slate-800 text-slate-500"
                  }`}>
                    {option.code}
                  </div>

                  {/* Label and description */}
                  <div className="flex-1 text-left">
                    <div className="font-mono text-sm tracking-wide">
                      {option.label}
                    </div>
                    <div className="text-[10px] text-slate-600">
                      {option.description}
                    </div>
                  </div>

                  {/* Selection indicator */}
                  <div className={`w-4 h-4 rounded-full border-2 transition-colors ${
                    selectedDuration === option.id
                      ? "border-cyan-400 bg-cyan-400"
                      : "border-slate-700"
                  }`}>
                    {selectedDuration === option.id && (
                      <svg className="w-full h-full text-[#0a0e17]" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative px-5 py-4 border-t border-cyan-900/50 bg-[#080c14] rounded-b-lg">
          <div className="flex items-center justify-between">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors uppercase tracking-wider"
            >
              Annuler
            </button>

            <button
              onClick={handleJump}
              disabled={!canJump}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
                canJump
                  ? "bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-lg shadow-cyan-500/25"
                  : "bg-slate-800 text-slate-600 cursor-not-allowed"
              }`}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Calcul...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                  </svg>
                  <span>Lancer</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// JUMP BUTTON (for header)
// =============================================================================

interface JumpForwardButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export function JumpForwardButton({ onClick, disabled }: JumpForwardButtonProps) {
  const { actionQueue, gamePhase, isLoading } = useNarrativeStore();

  const isDisabled =
    disabled ||
    actionQueue.length === 0 ||
    gamePhase !== "accumulating" ||
    isLoading;

  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      className={`group relative flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
        isDisabled
          ? "bg-slate-800 text-slate-600 cursor-not-allowed"
          : "bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40"
      }`}
      title={
        actionQueue.length === 0
          ? "Ajoutez des actions a la queue"
          : "Jump Forward - Avancer le temps"
      }
    >
      {/* Pulse effect when ready */}
      {!isDisabled && (
        <div className="absolute inset-0 rounded-lg bg-cyan-400/20 animate-pulse" />
      )}

      <svg className="relative w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
      </svg>
      <span className="relative hidden sm:inline">&gt;&gt;&gt;</span>

      {actionQueue.length > 0 && (
        <span className="relative bg-white/20 px-2 py-0.5 rounded text-xs">
          {actionQueue.length}
        </span>
      )}
    </button>
  );
}

export default JumpForwardModal;
