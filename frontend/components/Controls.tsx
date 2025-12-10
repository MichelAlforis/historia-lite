'use client';

import { GameSettings } from '@/lib/types';

interface ControlsProps {
  year: number;
  oilPrice: number;
  globalTension: number;
  isLoading: boolean;
  autoPlay: boolean;
  settings: GameSettings | null;
  onTick: () => void;
  onMultiTick: (years: number) => void;
  onReset: () => void;
  onAutoPlayToggle: () => void;
  onAiModeToggle: () => void;
}

export function Controls({
  year,
  oilPrice,
  globalTension,
  isLoading,
  autoPlay,
  settings,
  onTick,
  onMultiTick,
  onReset,
  onAutoPlayToggle,
  onAiModeToggle,
}: ControlsProps) {
  const aiMode = settings?.ai_mode || 'algorithmic';
  const ollamaAvailable = settings?.ollama_available || false;
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Year display */}
      <div className="text-center mb-4">
        <div className="text-4xl font-bold text-white">{year}</div>
        <div className="text-sm text-gray-400">Annee en cours</div>
      </div>

      {/* Global indicators */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-700 rounded p-3 text-center">
          <div className="text-lg font-bold text-yellow-400">${oilPrice}</div>
          <div className="text-xs text-gray-400">Prix du petrole</div>
        </div>
        <div className="bg-gray-700 rounded p-3 text-center">
          <div className={`text-lg font-bold ${
            globalTension > 70 ? 'text-red-400' :
            globalTension > 40 ? 'text-yellow-400' :
            'text-green-400'
          }`}>
            {globalTension}%
          </div>
          <div className="text-xs text-gray-400">Tension mondiale</div>
        </div>
      </div>

      {/* Control buttons */}
      <div className="space-y-2">
        <button
          onClick={onTick}
          disabled={isLoading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-bold transition-colors"
        >
          {isLoading ? 'Simulation...' : 'Avancer 1 an'}
        </button>

        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => onMultiTick(5)}
            disabled={isLoading}
            className="py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 rounded text-sm transition-colors"
          >
            +5 ans
          </button>
          <button
            onClick={() => onMultiTick(10)}
            disabled={isLoading}
            className="py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 rounded text-sm transition-colors"
          >
            +10 ans
          </button>
          <button
            onClick={() => onMultiTick(25)}
            disabled={isLoading}
            className="py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 rounded text-sm transition-colors"
          >
            +25 ans
          </button>
        </div>

        <button
          onClick={onAutoPlayToggle}
          className={`w-full py-2 rounded-lg font-medium transition-colors ${
            autoPlay
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-gray-600 hover:bg-gray-500'
          }`}
        >
          {autoPlay ? 'Pause Auto-Play' : 'Auto-Play'}
        </button>

        <button
          onClick={onReset}
          disabled={isLoading}
          className="w-full py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded-lg text-sm transition-colors"
        >
          Reinitialiser (2025)
        </button>

        {/* AI Mode Toggle */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="text-xs text-gray-400 mb-2">Mode IA</div>
          <button
            onClick={onAiModeToggle}
            disabled={!ollamaAvailable && aiMode === 'algorithmic'}
            className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
              aiMode === 'ollama'
                ? 'bg-cyan-600 hover:bg-cyan-700'
                : 'bg-gray-600 hover:bg-gray-500'
            } ${!ollamaAvailable && aiMode === 'algorithmic' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {aiMode === 'ollama' ? 'IA Ollama (LLM)' : 'IA Algorithmique'}
          </button>
          <div className="flex items-center justify-between mt-2 text-xs">
            <span className="text-gray-400">Ollama:</span>
            <span className={ollamaAvailable ? 'text-green-400' : 'text-red-400'}>
              {ollamaAvailable ? 'Connecte' : 'Non disponible'}
            </span>
          </div>
          {settings?.ollama_model && aiMode === 'ollama' && (
            <div className="text-xs text-gray-500 mt-1">
              Modele: {settings.ollama_model}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
