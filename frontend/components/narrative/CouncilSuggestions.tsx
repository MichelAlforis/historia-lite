"use client";

/**
 * CouncilSuggestions - "Conseil des urgences"
 *
 * Affiche les dossiers urgents AVANT le jump.
 * Le joueur prepare ses decisions pendant que le monde prepare ses consequences.
 *
 * Philosophie:
 * - Le Conseil ne dit pas "faites ceci" mais "voici ce qui brule"
 * - Chaque dossier = 2-3 suggestions (pas d'action parfaite)
 * - Cliquer une suggestion = pre-remplir la queue (pas executer)
 * - Le joueur peut ignorer consciemment
 */

import React, { useEffect } from "react";
import { getRiskStyle } from "@/lib/styleUtils";
import {
  useNarrativeStore,
  UrgentDossier,
  SuggestedAction,
  DossierUrgency,
  DossierType,
} from "@/stores/narrativeStore";

// =============================================================================
// DOSSIER CARD
// =============================================================================

interface DossierCardProps {
  dossier: UrgentDossier;
  onSelectSuggestion: (suggestion: SuggestedAction) => void;
  isLoading: boolean;
}

function DossierCard({ dossier, onSelectSuggestion, isLoading }: DossierCardProps) {
  // Urgency styling
  const urgencyConfig: Record<DossierUrgency, { border: string; badge: string; glow: string; label: string }> = {
    critical: {
      border: "border-red-800/60",
      badge: "bg-red-900/50 text-red-400 animate-pulse",
      glow: "shadow-red-900/20 shadow-lg",
      label: "CRITIQUE",
    },
    high: {
      border: "border-orange-800/50",
      badge: "bg-orange-900/50 text-orange-400",
      glow: "",
      label: "URGENT",
    },
    moderate: {
      border: "border-yellow-800/40",
      badge: "bg-yellow-900/50 text-yellow-400",
      glow: "",
      label: "ATTENTION",
    },
    low: {
      border: "border-slate-700/50",
      badge: "bg-slate-800/50 text-slate-400",
      glow: "",
      label: "INFO",
    },
  };

  // Type styling
  const typeConfig: Record<DossierType, { icon: string; color: string; label: string }> = {
    crisis: { icon: "🔥", color: "text-red-400", label: "CRISE" },
    opportunity: { icon: "⭐", color: "text-amber-400", label: "OPPORTUNITE" },
    pressure: { icon: "⚠️", color: "text-yellow-400", label: "PRESSION" },
    summit: { icon: "🤝", color: "text-blue-400", label: "DIPLOMATIE" },
    threat: { icon: "☢️", color: "text-red-500", label: "MENACE" },
  };

  const urgency = urgencyConfig[dossier.urgency];
  const type = typeConfig[dossier.type];

  return (
    <div className={`
      bg-[#0a0e18] rounded-lg border p-4
      ${urgency.border} ${urgency.glow}
      transition-all hover:border-opacity-100
    `}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{type.icon}</span>
          <div>
            <h4 className="text-sm font-medium text-slate-200">{dossier.title_fr}</h4>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-[10px] font-mono uppercase ${type.color}`}>
                {type.label}
              </span>
              {dossier.zone_id && (
                <span className="text-[10px] font-mono text-slate-600">
                  {dossier.zone_id.replace(/_/g, " ")}
                </span>
              )}
            </div>
          </div>
        </div>
        <span className={`text-[9px] font-mono px-2 py-0.5 rounded ${urgency.badge}`}>
          {urgency.label}
        </span>
      </div>

      {/* Summary */}
      <p className="text-xs text-slate-400 leading-relaxed mb-4">
        {dossier.summary_fr}
      </p>

      {/* Suggestions */}
      <div className="space-y-2">
        <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider mb-2">
          Actions possibles
        </div>
        {dossier.suggestions.map((suggestion) => (
          <SuggestionButton
            key={suggestion.id}
            suggestion={suggestion}
            onClick={() => onSelectSuggestion(suggestion)}
            disabled={isLoading}
          />
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// SUGGESTION BUTTON
// =============================================================================

interface SuggestionButtonProps {
  suggestion: SuggestedAction;
  onClick: () => void;
  disabled: boolean;
}

function SuggestionButton({ suggestion, onClick, disabled }: SuggestionButtonProps) {
  const risk = getRiskStyle(suggestion.risk_level);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full text-left p-2 rounded border border-slate-800
        bg-[#080c14] hover:bg-slate-800/50 hover:border-cyan-900/50
        transition-all group disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-cyan-400 group-hover:text-cyan-300">
              {suggestion.label}
            </span>
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${risk.bgColor} ${risk.color}`}>
              {suggestion.political_cost} pts
            </span>
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">
            {suggestion.description_fr}
          </p>
        </div>
        <span className="text-slate-600 group-hover:text-cyan-400 transition-colors">
          +
        </span>
      </div>
    </button>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface CouncilSuggestionsProps {
  className?: string;
}

export default function CouncilSuggestions({ className = "" }: CouncilSuggestionsProps) {
  const {
    councilDossiers,
    councilLoading,
    hasCouncilCritical,
    gamePhase,
    loadCouncilSuggestions,
    queueSuggestion,
    isLoading,
  } = useNarrativeStore();

  // Charger les suggestions au montage et quand on revient en phase accumulating
  useEffect(() => {
    if (gamePhase === "accumulating") {
      loadCouncilSuggestions();
    }
  }, [gamePhase, loadCouncilSuggestions]);

  // Ne rien afficher si pas en phase accumulating
  if (gamePhase !== "accumulating") {
    return null;
  }

  const handleSelectSuggestion = async (suggestion: SuggestedAction) => {
    const success = await queueSuggestion(suggestion);
    if (success) {
      // Recharger les suggestions pour reflechir les changements
      loadCouncilSuggestions();
    }
  };

  // Rien a afficher
  if (!councilLoading && councilDossiers.length === 0) {
    return null;
  }

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm">📋</span>
          <h3 className="text-sm font-mono text-slate-300 uppercase tracking-wider">
            Conseil des urgences
          </h3>
          {hasCouncilCritical && (
            <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-red-900/50 text-red-400 animate-pulse">
              ALERTE
            </span>
          )}
        </div>
        {councilLoading && (
          <span className="text-[10px] text-slate-500 animate-pulse">
            Analyse...
          </span>
        )}
      </div>

      {/* Loading state */}
      {councilLoading && councilDossiers.length === 0 && (
        <div className="text-center py-8 text-slate-500 text-sm">
          <div className="animate-pulse">Analyse de la situation...</div>
        </div>
      )}

      {/* Dossiers */}
      <div className="space-y-4">
        {councilDossiers.map((dossier) => (
          <DossierCard
            key={dossier.id}
            dossier={dossier}
            onSelectSuggestion={handleSelectSuggestion}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Footer hint */}
      {councilDossiers.length > 0 && (
        <div className="mt-4 text-center">
          <p className="text-[10px] text-slate-600 italic">
            Cliquer une action l'ajoute a la queue. Vous pouvez ignorer ces suggestions.
          </p>
        </div>
      )}
    </div>
  );
}
