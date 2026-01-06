"use client";

/**
 * Intent Review component for Historia Narrative
 *
 * Shows parsed intentions and allows player to select/deselect before generating actions
 */

import React from "react";
import { useNarrativeStore, ParsedIntention } from "@/stores/narrativeStore";

interface IntentReviewProps {
  intentions: ParsedIntention[];
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  diplomacy: { label: "Diplomatie", color: "blue" },
  military: { label: "Militaire", color: "red" },
  covert: { label: "Clandestin", color: "purple" },
  intel: { label: "Renseignement", color: "yellow" },
  economic: { label: "Economique", color: "green" },
  domestic: { label: "Domestique", color: "gray" },
};

export default function IntentReview({ intentions }: IntentReviewProps) {
  const {
    selectedIntentions,
    selectIntention,
    deselectIntention,
    generateActions,
    setInputText,
    isLoading,
  } = useNarrativeStore();

  const handleToggle = (id: string) => {
    if (selectedIntentions.includes(id)) {
      deselectIntention(id);
    } else {
      selectIntention(id);
    }
  };

  const handleBack = () => {
    // Go back to input phase
    useNarrativeStore.setState({ current_phase: "player_input" });
  };

  const handleContinue = async () => {
    if (selectedIntentions.length === 0) return;
    await generateActions();
  };

  if (intentions.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-3">Aucune intention reconnue</h3>
        <p className="text-gray-400 mb-4">
          Votre texte n&apos;a pas ete compris. Essayez d&apos;etre plus explicite
          sur ce que vous souhaitez faire.
        </p>
        <button
          onClick={handleBack}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
        >
          Reessayer
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-lg font-bold mb-1">Intentions detectees</h3>
      <p className="text-sm text-gray-400 mb-4">
        Selectionnez les intentions a transformer en actions
      </p>

      {/* Intentions list */}
      <div className="space-y-2 mb-4">
        {intentions.map((intention) => {
          const isSelected = selectedIntentions.includes(intention.id);
          const category = CATEGORY_LABELS[intention.category] || {
            label: intention.category,
            color: "gray",
          };

          return (
            <div
              key={intention.id}
              onClick={() => handleToggle(intention.id)}
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
                  <div className="flex items-center gap-2 mb-1">
                    {/* Category badge */}
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium bg-${category.color}-900 text-${category.color}-300`}
                      style={{
                        backgroundColor: `var(--color-${category.color}-900, #1e3a5f)`,
                        color: `var(--color-${category.color}-300, #93c5fd)`,
                      }}
                    >
                      {category.label}
                    </span>

                    {/* Confidence */}
                    <span
                      className={`text-xs ${
                        intention.confidence > 0.7
                          ? "text-green-400"
                          : intention.confidence > 0.5
                          ? "text-yellow-400"
                          : "text-red-400"
                      }`}
                    >
                      {Math.round(intention.confidence * 100)}% confiance
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-white font-medium">
                    {intention.description_fr}
                  </p>

                  {/* Target info */}
                  {(intention.target_zone || intention.target_country) && (
                    <p className="text-sm text-gray-400 mt-1">
                      Cible:{" "}
                      {intention.target_zone ||
                        intention.target_country ||
                        "Non specifie"}
                    </p>
                  )}

                  {/* Original text */}
                  <p className="text-xs text-gray-500 mt-1 italic">
                    &quot;{intention.source_text}&quot;
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selection summary */}
      <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
        <span>
          {selectedIntentions.length} / {intentions.length} selectionnees
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => intentions.forEach((i) => selectIntention(i.id))}
            className="text-blue-400 hover:text-blue-300"
          >
            Tout selectionner
          </button>
          <span>|</span>
          <button
            onClick={() => intentions.forEach((i) => deselectIntention(i.id))}
            className="text-blue-400 hover:text-blue-300"
          >
            Tout deselectionner
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleBack}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
        >
          Modifier le texte
        </button>
        <button
          onClick={handleContinue}
          disabled={selectedIntentions.length === 0 || isLoading}
          className={`flex-1 px-4 py-2 rounded font-medium ${
            selectedIntentions.length === 0 || isLoading
              ? "bg-gray-600 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {isLoading
            ? "Generation..."
            : `Generer ${selectedIntentions.length} action(s)`}
        </button>
      </div>
    </div>
  );
}
