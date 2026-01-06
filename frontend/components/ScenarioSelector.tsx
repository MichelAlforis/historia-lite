'use client';

import { useState, useEffect } from 'react';
import {
  BookOpen,
  Play,
  Star,
  Clock,
  Users,
  X,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { ScenarioSummary, ScenarioDetail } from '@/lib/types';

interface ScenarioSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectScenario: (scenarioId: string, countryId?: string) => void;
}

// Difficulty badge colors
const DIFFICULTY_COLORS: Record<string, { bg: string; text: string }> = {
  tutorial: { bg: 'bg-green-500/20', text: 'text-green-400' },
  easy: { bg: 'bg-sky-500/20', text: 'text-sky-400' },
  normal: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
  hard: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
  extreme: { bg: 'bg-red-500/20', text: 'text-red-400' },
  custom: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
};

const DIFFICULTY_LABELS: Record<string, string> = {
  tutorial: 'Tutoriel',
  easy: 'Facile',
  normal: 'Normal',
  hard: 'Difficile',
  extreme: 'Extreme',
  custom: 'Libre',
};

export default function ScenarioSelector({
  isOpen,
  onClose,
  onSelectScenario,
}: ScenarioSelectorProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch scenarios list
  useEffect(() => {
    if (!isOpen) return;

    const fetchScenarios = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/scenarios/');
        const data = await response.json();
        if (data.scenarios) {
          // Put tutorial first
          const sorted = [...data.scenarios].sort((a, b) => {
            if (a.difficulty === 'tutorial') return -1;
            if (b.difficulty === 'tutorial') return 1;
            return 0;
          });
          setScenarios(sorted);
        }
      } catch (err) {
        setError('Impossible de charger les scenarios');
      } finally {
        setLoading(false);
      }
    };

    fetchScenarios();
  }, [isOpen]);

  // Fetch scenario details
  const fetchScenarioDetail = async (scenarioId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}`);
      const data = await response.json();
      setSelectedScenario(data);
    } catch (err) {
      setError('Impossible de charger les details');
    } finally {
      setLoading(false);
    }
  };

  // Handle scenario selection
  const handleScenarioClick = (scenario: ScenarioSummary) => {
    fetchScenarioDetail(scenario.id);
  };

  // Handle start scenario
  const handleStart = () => {
    if (!selectedScenario) return;
    const defaultCountry = selectedScenario.recommended_countries[0] || 'FRA';
    onSelectScenario(selectedScenario.id, defaultCountry);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-800 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Star className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Choisir un Scenario</h2>
              <p className="text-sm text-slate-400">Selectionnez votre point de depart</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-300 hover:bg-slate-700 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex h-[calc(85vh-80px)]">
          {/* Scenarios list */}
          <div className="w-1/2 border-r border-slate-700 overflow-y-auto p-4">
            {loading && !scenarios.length ? (
              <div className="flex items-center justify-center h-40 text-slate-400">
                Chargement...
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-40 text-red-400">
                {error}
              </div>
            ) : (
              <div className="space-y-2">
                {scenarios.map((scenario) => {
                  const diffColors = DIFFICULTY_COLORS[scenario.difficulty] || DIFFICULTY_COLORS.normal;
                  const isTutorial = scenario.difficulty === 'tutorial';

                  return (
                    <button
                      key={scenario.id}
                      onClick={() => handleScenarioClick(scenario)}
                      className={`w-full text-left p-4 rounded-lg border transition ${
                        selectedScenario?.id === scenario.id
                          ? 'bg-sky-500/20 border-sky-500'
                          : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{scenario.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-white truncate">
                              {scenario.name_fr}
                            </span>
                            {isTutorial && (
                              <Sparkles className="w-4 h-4 text-green-400 flex-shrink-0" />
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <span className={`px-2 py-0.5 rounded ${diffColors.bg} ${diffColors.text}`}>
                              {DIFFICULTY_LABELS[scenario.difficulty]}
                            </span>
                            <span className="text-slate-500">{scenario.start_year}</span>
                            {scenario.duration && (
                              <span className="text-slate-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {scenario.duration} ans
                              </span>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-slate-500" />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Scenario detail */}
          <div className="w-1/2 p-6 overflow-y-auto">
            {selectedScenario ? (
              <div className="space-y-6">
                {/* Header */}
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-4xl">{selectedScenario.icon}</span>
                    <div>
                      <h3 className="text-2xl font-bold text-white">
                        {selectedScenario.name_fr}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          DIFFICULTY_COLORS[selectedScenario.difficulty]?.bg || ''
                        } ${DIFFICULTY_COLORS[selectedScenario.difficulty]?.text || ''}`}>
                          {DIFFICULTY_LABELS[selectedScenario.difficulty]}
                        </span>
                        <span className="text-slate-400 text-sm">
                          {selectedScenario.start_year}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="text-slate-300">{selectedScenario.description}</p>
                </div>

                {/* Tutorial badge */}
                {selectedScenario.difficulty === 'tutorial' && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                      <BookOpen className="w-5 h-5" />
                      <span className="font-semibold">Scenario Guide</span>
                    </div>
                    <p className="text-sm text-green-300/80">
                      Ce scenario inclut un tutoriel interactif qui vous guidera pas a pas
                      dans les mecaniques de base du jeu.
                    </p>
                  </div>
                )}

                {/* Recommended countries */}
                {selectedScenario.recommended_countries.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-400 mb-2 flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      Pays Recommandes
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedScenario.recommended_countries.map((countryId) => (
                        <span
                          key={countryId}
                          className="px-3 py-1 bg-slate-800 rounded-lg text-sm text-white"
                        >
                          {countryId}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tags */}
                {selectedScenario.tags.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-400 mb-2">Tags</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedScenario.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Start button */}
                <div className="pt-4 border-t border-slate-700">
                  <button
                    onClick={handleStart}
                    className="w-full py-3 bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-500 hover:to-cyan-500 rounded-lg font-semibold text-white flex items-center justify-center gap-2 transition"
                  >
                    <Play className="w-5 h-5" />
                    Commencer
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Selectionnez un scenario pour voir les details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
