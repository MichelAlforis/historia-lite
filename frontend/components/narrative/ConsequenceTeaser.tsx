"use client";

/**
 * ConsequenceTeaser - Apercu des Consequences
 *
 * Montre un teaser de ce qui pourrait arriver suite a cet evenement.
 * Cree de l'anticipation et de la tension narrative.
 */

import React from "react";

// =============================================================================
// TYPES
// =============================================================================

interface ConsequenceTeaserProps {
  text: string;
}

// =============================================================================
// COMPONENT
// =============================================================================

export function ConsequenceTeaser({ text }: ConsequenceTeaserProps) {
  return (
    <div className="bg-gradient-to-r from-slate-900/80 via-cyan-950/20 to-slate-900/80 border border-cyan-800/30 rounded p-3">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-900/50 flex items-center justify-center">
          <span className="text-cyan-400 text-[10px]">...</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="text-[9px] font-mono text-cyan-600 uppercase tracking-wider mb-1">
            A suivre
          </div>
          <p className="text-xs text-cyan-300/80 italic leading-relaxed">
            {text}
          </p>
        </div>
      </div>
    </div>
  );
}

export default ConsequenceTeaser;
