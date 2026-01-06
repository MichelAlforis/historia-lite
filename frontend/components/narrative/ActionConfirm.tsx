"use client";

/**
 * Action Confirm component for Historia Narrative
 *
 * Shows generated actions with costs and risks, allows player to confirm execution
 */

import React from "react";
import { useNarrativeStore, PendingAction } from "@/stores/narrativeStore";

interface ActionConfirmProps {
  actions: PendingAction[];
  totalCost: number;
  playerCapital: number;
  canConfirm: boolean;
}

const RISK_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  low: { bg: "bg-green-900", text: "text-green-300", label: "Faible" },
  medium: { bg: "bg-yellow-900", text: "text-yellow-300", label: "Moyen" },
  high: { bg: "bg-orange-900", text: "text-orange-300", label: "Eleve" },
  extreme: { bg: "bg-red-900", text: "text-red-300", label: "Extreme" },
};

export default function ActionConfirm({
  actions,
  totalCost,
  playerCapital,
  canConfirm,
}: ActionConfirmProps) {
  const {
    selectedActions,
    selectAction,
    deselectAction,
    confirmActions,
    isLoading,
  } = useNarrativeStore();

  const handleToggle = (id: string) => {
    if (selectedActions.includes(id)) {
      deselectAction(id);
    } else {
      selectAction(id);
    }
  };

  const handleBack = () => {
    // Go back to intent review
    useNarrativeStore.setState({ current_phase: "intent_review" });
  };

  const handleConfirm = async () => {
    if (!canConfirm || isLoading) return;
    await confirmActions();
  };

  const selectedCost = actions
    .filter((a) => selectedActions.includes(a.id))
    .reduce((sum, a) => sum + a.political_cost, 0);

  const hasEnoughCapital = selectedCost <= playerCapital;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-lg font-bold mb-1">Confirmer les actions</h3>
      <p className="text-sm text-gray-400 mb-4">
        Verifiez les couts et risques avant de confirmer
      </p>

      {/* Actions list */}
      <div className="space-y-3 mb-4">
        {actions.map((action) => {
          const isSelected = selectedActions.includes(action.id);
          const risk = RISK_COLORS[action.risk_level] || RISK_COLORS.medium;

          return (
            <div
              key={action.id}
              onClick={() => handleToggle(action.id)}
              className={`p-3 rounded-lg cursor-pointer transition-all ${
                isSelected
                  ? "bg-blue-900/50 border border-blue-500"
                  : "bg-gray-700 border border-transparent hover:border-gray-500"
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Checkbox */}
                <div
                  className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    isSelected
                      ? "bg-blue-500 border-blue-500"
                      : "border-gray-500"
                  }`}
                >
                  {isSelected && (
                    <svg
                      className="w-3 h-3 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{action.description_fr}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${risk.bg} ${risk.text}`}
                    >
                      Risque {risk.label}
                    </span>
                  </div>

                  {/* Cost */}
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Cout: </span>
                      <span
                        className={
                          action.political_cost > 20
                            ? "text-red-400 font-bold"
                            : "text-white"
                        }
                      >
                        {action.political_cost} capital
                      </span>
                    </div>

                    {action.target_zone && (
                      <div>
                        <span className="text-gray-400">Zone: </span>
                        <span className="text-white">{action.target_zone}</span>
                      </div>
                    )}

                    {action.target_actor && (
                      <div>
                        <span className="text-gray-400">Cible: </span>
                        <span className="text-white">{action.target_actor}</span>
                      </div>
                    )}
                  </div>

                  {/* Predicted effects */}
                  {Object.keys(action.predicted_effects).length > 0 && (
                    <div className="mt-2 text-xs text-gray-400">
                      <span>Effets prevus: </span>
                      {Object.entries(action.predicted_effects).map(
                        ([key, value], i) => (
                          <span key={key}>
                            {i > 0 && ", "}
                            {key}: {value}
                          </span>
                        )
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Cost summary */}
      <div className="p-3 bg-gray-900 rounded-lg mb-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Cout total</span>
          <span
            className={`text-xl font-bold ${
              hasEnoughCapital ? "text-white" : "text-red-500"
            }`}
          >
            {selectedCost} / {playerCapital}
          </span>
        </div>

        {!hasEnoughCapital && (
          <p className="text-red-400 text-sm mt-2">
            Capital politique insuffisant! Deselectionnez des actions.
          </p>
        )}

        {/* Progress bar */}
        <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              hasEnoughCapital ? "bg-blue-500" : "bg-red-500"
            }`}
            style={{
              width: `${Math.min(100, (selectedCost / playerCapital) * 100)}%`,
            }}
          />
        </div>
      </div>

      {/* Warning for high-risk actions */}
      {actions.some(
        (a) =>
          selectedActions.includes(a.id) &&
          (a.risk_level === "high" || a.risk_level === "extreme")
      ) && (
        <div className="p-3 bg-orange-900/30 border border-orange-700 rounded-lg mb-4">
          <p className="text-orange-300 text-sm">
            <strong>Attention:</strong> Vous avez selectionne des actions a
            risque eleve. Elles pourraient avoir des consequences imprevues.
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleBack}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
        >
          Modifier les intentions
        </button>
        <button
          onClick={handleConfirm}
          disabled={!canConfirm || isLoading}
          className={`flex-1 px-4 py-2 rounded font-medium ${
            !canConfirm || isLoading
              ? "bg-gray-600 text-gray-400 cursor-not-allowed"
              : "bg-green-600 hover:bg-green-700 text-white"
          }`}
        >
          {isLoading
            ? "Execution..."
            : `Executer ${selectedActions.length} action(s)`}
        </button>
      </div>
    </div>
  );
}
