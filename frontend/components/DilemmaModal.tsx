'use client';

import { useState } from 'react';
import { ActiveDilemma, DilemmaChoice, DilemmaResolveResponse, DILEMMA_COLORS } from '@/lib/types';
import { resolveDilemma } from '@/lib/api';

interface DilemmaModalProps {
  dilemma: ActiveDilemma;
  playerCountryId: string;
  onResolved: (response: DilemmaResolveResponse) => void;
  onClose: () => void;
}

export default function DilemmaModal({
  dilemma,
  playerCountryId,
  onResolved,
  onClose,
}: DilemmaModalProps) {
  const [selectedChoice, setSelectedChoice] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (selectedChoice === null) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await resolveDilemma(dilemma.id, selectedChoice, playerCountryId);
      onResolved(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la resolution');
    } finally {
      setIsLoading(false);
    }
  };

  const getEffectColor = (value: number) => {
    if (value > 0) return 'text-green-400';
    if (value < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  const formatEffect = (stat: string, value: number) => {
    const sign = value > 0 ? '+' : '';
    return `${stat}: ${sign}${value}`;
  };

  const typeColor = DILEMMA_COLORS[dilemma.type] || 'bg-gray-500';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
      <div className="bg-gray-800 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-600">
        {/* Header */}
        <div className={`${typeColor} px-6 py-4 rounded-t-xl`}>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">{dilemma.title_fr}</h2>
            {dilemma.expires_at_year && (
              <span className="px-3 py-1 bg-black/30 rounded-full text-sm text-white">
                Expire en {dilemma.expires_at_year}
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="px-6 py-4 border-b border-gray-700">
          <p className="text-gray-200 text-lg">{dilemma.description_fr}</p>
          <p className="text-gray-400 text-sm mt-2">
            Declenche en {dilemma.year_triggered}
          </p>
        </div>

        {/* Choices */}
        <div className="px-6 py-4 space-y-4">
          <h3 className="text-lg font-semibold text-white mb-3">Vos options:</h3>

          {dilemma.choices.map((choice) => (
            <ChoiceCard
              key={choice.id}
              choice={choice}
              isSelected={selectedChoice === choice.id}
              onSelect={() => setSelectedChoice(choice.id)}
              getEffectColor={getEffectColor}
              formatEffect={formatEffect}
            />
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mb-4 p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="px-6 py-4 border-t border-gray-700 flex gap-4">
          <button
            onClick={handleConfirm}
            disabled={selectedChoice === null || isLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            {isLoading ? 'Resolution en cours...' : 'Confirmer mon choix'}
          </button>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
          >
            Reporter
          </button>
        </div>
      </div>
    </div>
  );
}

interface ChoiceCardProps {
  choice: DilemmaChoice;
  isSelected: boolean;
  onSelect: () => void;
  getEffectColor: (value: number) => string;
  formatEffect: (stat: string, value: number) => string;
}

function ChoiceCard({
  choice,
  isSelected,
  onSelect,
  getEffectColor,
  formatEffect,
}: ChoiceCardProps) {
  const hasEffects = Object.keys(choice.effects).length > 0;
  const hasRelationEffects = Object.keys(choice.relation_effects).length > 0;

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
        isSelected
          ? 'border-blue-500 bg-blue-900/30'
          : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-white mb-1">
            {choice.id}. {choice.label_fr}
          </h4>
          <p className="text-gray-300">{choice.description_fr}</p>
        </div>
        <div
          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ml-4 ${
            isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-500'
          }`}
        >
          {isSelected && (
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </div>
      </div>

      {/* Effects preview */}
      {(hasEffects || hasRelationEffects) && (
        <div className="mt-3 pt-3 border-t border-gray-600">
          {hasEffects && (
            <div className="flex flex-wrap gap-2 mb-2">
              {Object.entries(choice.effects).map(([stat, value]) => (
                <span
                  key={stat}
                  className={`px-2 py-1 rounded text-xs font-medium ${getEffectColor(value)} bg-gray-800`}
                >
                  {formatEffect(stat, value)}
                </span>
              ))}
            </div>
          )}

          {hasRelationEffects && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(choice.relation_effects).map(([country, value]) => (
                <span
                  key={country}
                  className={`px-2 py-1 rounded text-xs font-medium ${getEffectColor(value)} bg-gray-800`}
                >
                  {country}: {value > 0 ? '+' : ''}{value}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Special consequences */}
      <div className="mt-2 flex flex-wrap gap-2">
        {choice.declares_war && (
          <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs">
            Declare guerre a {choice.declares_war}
          </span>
        )}
        {choice.ends_war && (
          <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
            Met fin au conflit
          </span>
        )}
        {choice.starts_project && (
          <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs">
            Demarre: {choice.starts_project}
          </span>
        )}
      </div>
    </button>
  );
}
