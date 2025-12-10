// Historia Lite - Scenario Selector Component
'use client';

import { useState, useEffect } from 'react';
import { ScenarioSummary, ScenarioDetail, DIFFICULTY_COLORS, DIFFICULTY_NAMES } from '@/lib/types';
import * as api from '@/lib/api';

interface ScenarioSelectorProps {
  onScenarioStart: (scenarioId: string, playerCountry?: string) => Promise<void>;
  onClose: () => void;
}

export default function ScenarioSelector({ onScenarioStart, onClose }: ScenarioSelectorProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioDetail | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      setIsLoading(true);
      const response = await api.getScenarios();
      setScenarios(response.scenarios);
    } catch (err) {
      setError('Erreur lors du chargement des scenarios');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadScenarioDetail(scenarioId: string) {
    try {
      const detail = await api.getScenario(scenarioId);
      setSelectedScenario(detail);
      // Auto-select first recommended country
      if (detail.recommended_countries && detail.recommended_countries.length > 0) {
        setSelectedCountry(detail.recommended_countries[0]);
      }
    } catch (err) {
      setError('Erreur lors du chargement du scenario');
      console.error(err);
    }
  }

  async function handleStart() {
    if (!selectedScenario) return;

    try {
      setIsStarting(true);
      await onScenarioStart(selectedScenario.id, selectedCountry || undefined);
      onClose();
    } catch (err) {
      setError('Erreur lors du demarrage du scenario');
      console.error(err);
    } finally {
      setIsStarting(false);
    }
  }

  // Skeleton loader
  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-700 rounded w-1/3"></div>
            <div className="grid grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-32 bg-gray-700 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-900 to-purple-900 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🎬</span>
            <div>
              <h2 className="text-xl font-bold text-white">Choisir un Scenario</h2>
              <p className="text-sm text-indigo-200">{scenarios.length} scenarios disponibles</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white transition-colors p-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Fermer</button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {selectedScenario ? (
            // Scenario Detail View
            <div className="space-y-6">
              <button
                onClick={() => setSelectedScenario(null)}
                className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Retour aux scenarios
              </button>

              <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
                <div className="flex items-start gap-4">
                  <span className="text-5xl">{selectedScenario.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-2xl font-bold text-white">{selectedScenario.name_fr}</h3>
                      <span
                        className="px-3 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: DIFFICULTY_COLORS[selectedScenario.difficulty] + '20',
                          color: DIFFICULTY_COLORS[selectedScenario.difficulty]
                        }}
                      >
                        {DIFFICULTY_NAMES[selectedScenario.difficulty]}
                      </span>
                    </div>
                    <p className="text-gray-400 mt-2">{selectedScenario.description}</p>

                    <div className="flex gap-4 mt-4 text-sm">
                      <div className="flex items-center gap-2 text-gray-300">
                        <span className="text-lg">📅</span>
                        <span>Debut: {selectedScenario.start_year}</span>
                      </div>
                      {selectedScenario.duration && (
                        <div className="flex items-center gap-2 text-gray-300">
                          <span className="text-lg">⏱️</span>
                          <span>Duree: {selectedScenario.duration} ans</span>
                        </div>
                      )}
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mt-4">
                      {selectedScenario.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Country Selection */}
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <span>🏳️</span>
                  Choisir votre pays
                </h4>

                {selectedScenario.recommended_countries && selectedScenario.recommended_countries.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-400">
                      Pays recommandes pour ce scenario:
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {selectedScenario.recommended_countries.map(countryId => (
                        <button
                          key={countryId}
                          onClick={() => setSelectedCountry(countryId)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            selectedCountry === countryId
                              ? 'border-indigo-500 bg-indigo-900/30'
                              : 'border-gray-600 hover:border-gray-500 bg-gray-800'
                          }`}
                        >
                          <div className="text-2xl mb-1">
                            {countryId === 'USA' ? '🇺🇸' :
                             countryId === 'CHN' ? '🇨🇳' :
                             countryId === 'RUS' ? '🇷🇺' :
                             countryId === 'FRA' ? '🇫🇷' :
                             countryId === 'GBR' ? '🇬🇧' :
                             countryId === 'DEU' ? '🇩🇪' :
                             countryId === 'JPN' ? '🇯🇵' :
                             countryId === 'IND' ? '🇮🇳' :
                             countryId === 'BRA' ? '🇧🇷' :
                             countryId === 'SAU' ? '🇸🇦' : '🏳️'}
                          </div>
                          <div className="text-sm text-white font-medium">{countryId}</div>
                        </button>
                      ))}
                    </div>

                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <label className="flex items-center gap-2 text-sm text-gray-400">
                        <input
                          type="checkbox"
                          checked={selectedCountry === ''}
                          onChange={(e) => setSelectedCountry(e.target.checked ? '' : selectedScenario.recommended_countries![0])}
                          className="rounded bg-gray-700 border-gray-600"
                        />
                        Mode observateur (sans pays joueur)
                      </label>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-400">
                    Ce scenario ne propose pas de pays joueur specifique.
                    Vous pouvez observer la simulation.
                  </p>
                )}
              </div>

              {/* Objectives Preview */}
              {selectedScenario.objectives && selectedCountry && selectedScenario.objectives[selectedCountry] && (
                <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>🎯</span>
                    Objectifs pour {selectedCountry}
                  </h4>
                  <ul className="space-y-2">
                    {selectedScenario.objectives[selectedCountry].map((obj, idx) => (
                      <li key={idx} className="flex items-center gap-3 text-gray-300">
                        <span className="w-6 h-6 rounded-full bg-indigo-900 text-indigo-300 flex items-center justify-center text-xs font-medium">
                          {idx + 1}
                        </span>
                        {obj.replace(/_/g, ' ')}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            // Scenario List View
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scenarios.map(scenario => (
                <button
                  key={scenario.id}
                  onClick={() => loadScenarioDetail(scenario.id)}
                  className="bg-gray-900 rounded-xl p-5 border border-gray-700 hover:border-indigo-500 transition-all text-left group"
                >
                  <div className="flex items-start gap-4">
                    <span className="text-4xl group-hover:scale-110 transition-transform">
                      {scenario.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white truncate">{scenario.name_fr}</h3>
                        <span
                          className="px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0"
                          style={{
                            backgroundColor: DIFFICULTY_COLORS[scenario.difficulty] + '20',
                            color: DIFFICULTY_COLORS[scenario.difficulty]
                          }}
                        >
                          {DIFFICULTY_NAMES[scenario.difficulty]}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                        {scenario.description}
                      </p>
                      <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                        <span>📅 {scenario.start_year}</span>
                        {scenario.duration && <span>⏱️ {scenario.duration} ans</span>}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {scenario.tags.slice(0, 3).map(tag => (
                          <span
                            key={tag}
                            className="px-1.5 py-0.5 bg-gray-700 text-gray-400 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer with Start Button */}
        {selectedScenario && (
          <div className="border-t border-gray-700 px-6 py-4 bg-gray-900 flex items-center justify-between">
            <div className="text-sm text-gray-400">
              {selectedCountry ? (
                <span>Jouer en tant que <strong className="text-white">{selectedCountry}</strong></span>
              ) : (
                <span>Mode observateur</span>
              )}
            </div>
            <button
              onClick={handleStart}
              disabled={isStarting}
              className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all flex items-center gap-2"
            >
              {isStarting ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Chargement...
                </>
              ) : (
                <>
                  <span>Lancer le Scenario</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
