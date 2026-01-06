"use client";

/**
 * JumpForwardButton - Simple Jump Forward avec micro-rituel visuel
 *
 * Un seul bouton. Le systeme avance jusqu'au prochain evenement majeur.
 * Pas de modal, pas de selection de duree. SIMPLE.
 *
 * MICRO-RITUEL: Le bouton se transforme brievement pour marquer
 * le point de non-retour. Le joueur SENT qu'il engage ses decisions.
 */

import React, { useState, useEffect } from "react";
import { useNarrativeStore } from "@/stores/narrativeStore";

// =============================================================================
// JUMP BUTTON - avec rituel d'engagement
// =============================================================================

export function JumpForwardButton({ disabled }: { disabled?: boolean }) {
  const { actionQueue, gamePhase, isLoading, jumpForward } = useNarrativeStore();
  const [isEngaging, setIsEngaging] = useState(false);

  const isDisabled =
    disabled ||
    actionQueue.length === 0 ||
    gamePhase !== "accumulating" ||
    isLoading ||
    isEngaging;

  // Quand on passe en "jumping", reset l'etat d'engagement
  useEffect(() => {
    if (gamePhase === "jumping") {
      setIsEngaging(false);
    }
  }, [gamePhase]);

  const handleClick = () => {
    if (!isDisabled) {
      // RITUEL: transformation visuelle avant le jump
      setIsEngaging(true);

      // Petit delai pour que le joueur VOIE la transformation
      setTimeout(() => {
        jumpForward("next_event");
      }, 400);
    }
  };

  // Etat: en cours d'engagement (transformation visuelle)
  if (isEngaging) {
    return (
      <button
        disabled
        className="group relative flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider bg-amber-600/80 text-white cursor-wait"
      >
        <div className="absolute inset-0 rounded-lg bg-amber-400/30 animate-pulse" />
        <svg className="relative w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span className="relative text-xs">RESOLUTION...</span>
      </button>
    );
  }

  // Etat: desactive
  if (isDisabled) {
    return (
      <button
        disabled
        className="group relative flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider bg-slate-800 text-slate-600 cursor-not-allowed"
        title="Ajoutez des actions a la queue"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
        <span className="hidden sm:inline">&gt;&gt;&gt;</span>
      </button>
    );
  }

  // Etat: pret a engager
  return (
    <button
      onClick={handleClick}
      className="group relative flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40"
      title="Engager vos decisions"
    >
      {/* Pulse effect when ready */}
      <div className="absolute inset-0 rounded-lg bg-cyan-400/20 animate-pulse" />

      <svg className="relative w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
      </svg>
      <span className="relative hidden sm:inline">&gt;&gt;&gt;</span>

      <span className="relative bg-white/20 px-2 py-0.5 rounded text-xs">
        {actionQueue.length}
      </span>
    </button>
  );
}

// =============================================================================
// DEPRECATED: JumpForwardModal - Ne fait plus rien
// =============================================================================

interface JumpForwardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function JumpForwardModal({ isOpen, onClose }: JumpForwardModalProps) {
  return null;
}

export default JumpForwardButton;
