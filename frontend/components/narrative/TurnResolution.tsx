"use client";

/**
 * Turn Resolution component for Historia Narrative
 *
 * Displays the results of a turn: player actions, adversary actions, events
 */

import React from "react";
import { TurnResult, useNarrativeStore } from "@/stores/narrativeStore";

interface TurnResolutionProps {
  result: TurnResult;
}

export default function TurnResolution({ result }: TurnResolutionProps) {
  const handleNextTurn = () => {
    useNarrativeStore.setState({ current_phase: "player_input" });
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="border-b border-gray-700 pb-3">
        <h3 className="text-lg font-bold">Resolution du tour {result.turn}</h3>
        <p className="text-gray-400">{result.date_display}</p>
      </div>

      {/* Player actions */}
      {result.player_actions_executed.length > 0 && (
        <div>
          <h4 className="font-bold text-blue-400 mb-2">Vos actions</h4>
          <div className="space-y-1">
            {result.player_actions_executed.map((action, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-sm bg-blue-900/30 p-2 rounded"
              >
                <span className="text-green-400">✓</span>
                <span>{action.type.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Adversary actions */}
      {result.adversary_actions.length > 0 && (
        <div>
          <h4 className="font-bold text-red-400 mb-2">Actions sovietiques</h4>
          <div className="space-y-1">
            {result.adversary_actions.map((action, i) => (
              <div
                key={i}
                className={`text-sm p-2 rounded ${
                  action.visible
                    ? "bg-red-900/30"
                    : "bg-gray-700 text-gray-500 italic"
                }`}
              >
                {action.visible ? (
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">⚡</span>
                    <span>{action.description_fr}</span>
                    {action.target && (
                      <span className="text-gray-400">({action.target})</span>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span>?</span>
                    <span>Activite secrete detectee</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events */}
      {result.events.length > 0 && (
        <div>
          <h4 className="font-bold text-yellow-400 mb-2">Evenements</h4>
          <div className="space-y-1">
            {result.events.map((event, i) => (
              <div
                key={i}
                className="text-sm bg-yellow-900/30 p-2 rounded flex items-center gap-2"
              >
                <span className="text-yellow-400">!</span>
                <span>{event.description_fr}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* State changes summary */}
      {Object.keys(result.state_changes).length > 0 && (
        <div>
          <h4 className="font-bold text-gray-400 mb-2">
            Changements d&apos;etat
          </h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(result.state_changes).map(([key, value]) => (
              <div key={key} className="flex justify-between bg-gray-700 p-2 rounded">
                <span className="text-gray-400">{formatKey(key)}</span>
                <span
                  className={
                    typeof value === "number"
                      ? value > 0
                        ? "text-green-400"
                        : value < 0
                        ? "text-red-400"
                        : "text-white"
                      : "text-white"
                  }
                >
                  {typeof value === "number" && value > 0 ? "+" : ""}
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Narrative summary */}
      {result.narrative_summary_fr && (
        <div className="bg-gray-900 p-3 rounded-lg">
          <h4 className="font-bold mb-2">Recit</h4>
          <div
            className="text-sm text-gray-300 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{
              __html: result.narrative_summary_fr
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/\*(.*?)\*/g, "<em>$1</em>"),
            }}
          />
        </div>
      )}

      {/* Continue button */}
      {!result.game_over && (
        <button
          onClick={handleNextTurn}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium"
        >
          Continuer au tour suivant
        </button>
      )}
    </div>
  );
}

function formatKey(key: string): string {
  const labels: Record<string, string> = {
    political_capital: "Capital politique",
    world_tension: "Tension mondiale",
    defcon: "DEFCON",
    influence_us: "Influence US",
    influence_ussr: "Influence URSS",
    control_us: "Controle US",
    control_ussr: "Controle URSS",
    stability: "Stabilite",
    trust: "Confiance",
    fear: "Peur",
    respect: "Respect",
    leverage: "Levier",
  };

  return labels[key] || key.replace(/_/g, " ");
}
