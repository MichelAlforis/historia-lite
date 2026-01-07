"use client";

/**
 * ActionQueue - Military Operations Queue
 *
 * Displays pending operations in Cold War command style
 */

import React from "react";
import { useNarrativeStore, QueuedAction, QueueSummary } from "@/stores/narrativeStore";
import { getRiskStyle, getCategoryStyle } from "@/lib/styleUtils";

// =============================================================================
// ACTION ITEM
// =============================================================================

interface ActionItemProps {
  action: QueuedAction;
  onRemove: (id: string) => void;
  index: number;
}

function ActionItem({ action, onRemove, index }: ActionItemProps) {
  const category = action.intention_type?.split("_")[0] || "GEN";
  const risk = getRiskStyle(action.risk_level);
  const catConfig = getCategoryStyle(category);

  // Determine if this is a high-cost action (contextually expensive)
  const isExpensive = action.political_cost >= 30;
  const isVeryExpensive = action.political_cost >= 50;

  return (
    <div className={`
      group relative bg-[#080c14] border rounded-md p-3 transition-all
      ${risk.label === "EXTREME" ? "border-red-900/50 hover:border-red-700/50" : "border-slate-800 hover:border-cyan-900/50"}
    `}>
      {/* Risk indicator bar */}
      <div className={`absolute -left-px top-0 bottom-0 w-1 rounded-l ${
        risk.label === "EXTREME" ? "bg-red-500" :
        risk.label === "ELEVE" ? "bg-orange-500" :
        risk.label === "MOYEN" ? "bg-yellow-500" :
        "bg-green-500"
      }`} />

      <div className="flex items-start gap-3">
        {/* Category Icon */}
        <div className={`flex-shrink-0 w-8 h-8 rounded flex items-center justify-center ${catConfig.color} bg-slate-800`}>
          <span className="text-sm">{catConfig.icon}</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Category badge */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-mono uppercase tracking-wider ${catConfig.color}`}>
              {category}
            </span>
            {action.target_zone && (
              <span className="text-[10px] font-mono text-slate-600">
                → {action.target_zone.replace(/_/g, " ")}
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-xs text-slate-300 leading-relaxed">
            {action.description_fr}
          </p>

          {/* Cost and Risk */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {/* Cost badge - more prominent for expensive actions */}
            <span className={`
              text-[10px] font-mono px-2 py-0.5 rounded
              ${isVeryExpensive ? "bg-red-500/20 text-red-400 font-bold" :
                isExpensive ? "bg-orange-500/20 text-orange-400" :
                "bg-amber-500/10 text-amber-400"}
            `}>
              {isVeryExpensive ? "⚡ " : ""}{action.political_cost} PTS
            </span>

            {/* Risk badge */}
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${risk.bgColor} ${risk.color}`}>
              {risk.label === "EXTREME" ? "☢️ " : ""}{risk.label}
            </span>
          </div>
        </div>

        {/* Remove button */}
        <button
          onClick={() => onRemove(action.id)}
          className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded transition-all"
          title="Annuler cette operation"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Extreme risk warning */}
      {risk.label === "EXTREME" && (
        <div className="mt-2 pt-2 border-t border-red-900/30 text-[10px] font-mono text-red-400/80 flex items-center gap-1">
          <span>⚠</span>
          <span>Operation tres risquee - consequences potentiellement graves</span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// QUEUE SUMMARY
// =============================================================================

interface QueueSummaryDisplayProps {
  summary: QueueSummary;
  availableCapital: number;
}

function QueueSummaryDisplay({ summary, availableCapital }: QueueSummaryDisplayProps) {
  const isOverBudget = summary.total_cost > availableCapital;

  return (
    <div className="px-3 py-2 border-b border-slate-800 bg-[#080c14]">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-slate-500">
          {summary.count} OP{summary.count > 1 ? "S" : ""} EN ATTENTE
        </span>
        <span className={`text-xs font-mono ${isOverBudget ? "text-red-400" : "text-cyan-400"}`}>
          {summary.total_cost} / {availableCapital} PTS
        </span>
      </div>

      {/* Warnings */}
      {(summary.has_high_risk || isOverBudget) && (
        <div className="mt-2 flex flex-wrap gap-2">
          {summary.has_high_risk && (
            <span className="text-[10px] font-mono text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded">
              ! OPERATIONS RISQUEES
            </span>
          )}
          {isOverBudget && (
            <span className="text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded">
              ! CAPITAL INSUFFISANT
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function ActionQueue() {
  const {
    actionQueue,
    queueSummary,
    player,
    removeFromQueue,
    isLoading,
    gamePhase,
  } = useNarrativeStore();

  const handleRemove = async (actionId: string) => {
    await removeFromQueue(actionId);
  };

  if (gamePhase === "playback") {
    return null;
  }

  return (
    <div className="bg-[#0d1420] border border-cyan-900/30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 border-b border-cyan-900/30 bg-[#0a0e17]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              actionQueue.length > 0 ? "bg-amber-500 animate-pulse" : "bg-slate-600"
            }`} />
            <span className="text-xs font-mono tracking-wider text-cyan-400/70 uppercase">
              Operations en Queue
            </span>
          </div>
          {gamePhase === "jumping" && (
            <span className="text-[10px] font-mono text-amber-400 animate-pulse">
              EXECUTION...
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      {queueSummary && queueSummary.count > 0 && (
        <QueueSummaryDisplay
          summary={queueSummary}
          availableCapital={player.available_capital || player.political_capital}
        />
      )}

      {/* Actions List */}
      <div className="p-3">
        {actionQueue.length === 0 ? (
          <div className="py-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800/50 flex items-center justify-center">
              <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <p className="text-xs font-mono text-slate-600 uppercase tracking-wider">
              Aucune operation
            </p>
            <p className="text-[10px] text-slate-700 mt-1">
              Vos ordres apparaitront ici
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
            {actionQueue.map((action, idx) => (
              <ActionItem
                key={action.id}
                action={action}
                onRemove={handleRemove}
                index={idx}
              />
            ))}
          </div>
        )}
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-[#0a0e17]/80 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}

export default ActionQueue;
