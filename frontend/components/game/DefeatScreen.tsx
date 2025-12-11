'use client';

import { useRef } from 'react';

interface DefeatScreenProps {
  scenarioName: string;
  finalScore: number;
  maxScore: number;
  yearsPlayed: number;
  reason: string;
  reasonFr?: string;
  objectives: {
    id: string;
    name: string;
    status: 'completed' | 'failed' | 'pending';
    points: number;
  }[];
  onRestart: () => void;
  onMainMenu: () => void;
}

export default function DefeatScreen({
  scenarioName,
  finalScore,
  maxScore,
  yearsPlayed,
  reason,
  reasonFr,
  objectives,
  onRestart,
  onMainMenu,
}: DefeatScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  const completedCount = objectives.filter(o => o.status === 'completed').length;
  const failedCount = objectives.filter(o => o.status === 'failed').length;
  const scorePercentage = maxScore > 0 ? Math.round((finalScore / maxScore) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-gray-950 via-red-950/10 to-gray-900 overflow-y-auto">
      {/* Video de fond - subtile */}
      <video
        ref={videoRef}
        autoPlay
        muted
        loop
        playsInline
        className="absolute inset-0 w-full h-full object-cover opacity-15"
      >
        <source src="/video/defeat.mp4" type="video/mp4" />
      </video>

      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-transparent to-gray-950/50" />

      {/* Contenu - visible immediatement */}
      <div className="relative z-10 flex flex-col items-center min-h-screen p-6 py-12">
        {/* Header - Titre compact */}
        <div className="text-center mb-6">
          <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-red-500 to-red-600 mb-2">
            DEFAITE
          </h1>
          <p className="text-lg text-gray-400">{scenarioName}</p>
        </div>

        {/* Raison de la defaite */}
        <div className="bg-red-900/20 backdrop-blur rounded-xl p-4 max-w-md w-full mb-6 border border-red-700/30">
          <div className="text-center">
            <div className="text-xs text-red-400 uppercase tracking-wider mb-1">
              Cause
            </div>
            <div className="text-base text-red-200">
              {reasonFr || reason}
            </div>
          </div>
        </div>

        {/* Score Card */}
        <div className="bg-gray-800/80 backdrop-blur rounded-2xl p-6 max-w-md w-full mb-6 border border-gray-700 shadow-xl">
          {/* Score */}
          <div className="text-center mb-4">
            <div className="text-4xl font-bold text-gray-300 mb-1">{finalScore}</div>
            <div className="text-sm text-gray-500">sur {maxScore} points</div>
            <div className="text-base text-gray-400 mt-1">{scorePercentage}% complete</div>
          </div>

          {/* Stats row */}
          <div className="flex justify-around border-t border-gray-700 pt-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{yearsPlayed}</div>
              <div className="text-xs text-gray-500">Annees</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{completedCount}</div>
              <div className="text-xs text-gray-500">Reussis</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{failedCount}</div>
              <div className="text-xs text-gray-500">Echoues</div>
            </div>
          </div>
        </div>

        {/* Objectifs - Liste compacte */}
        {objectives.length > 0 && (
          <div className="bg-gray-800/60 backdrop-blur rounded-xl p-4 max-w-md w-full mb-6 border border-gray-700">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Objectifs ({completedCount}/{objectives.length})
            </h2>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {objectives.map((obj) => (
                <div
                  key={obj.id}
                  className={`flex items-center justify-between py-2 px-3 rounded-lg text-sm ${
                    obj.status === 'completed'
                      ? 'bg-green-900/30 text-green-300'
                      : obj.status === 'failed'
                      ? 'bg-red-900/30 text-red-300'
                      : 'bg-gray-700/30 text-gray-500'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>
                      {obj.status === 'completed' ? '✓' : obj.status === 'failed' ? '✗' : '○'}
                    </span>
                    <span className="truncate">{obj.name}</span>
                  </div>
                  <span className="font-medium">
                    {obj.status === 'completed' ? `+${obj.points}` : obj.points}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Boutons */}
        <div className="flex gap-3">
          <button
            onClick={onRestart}
            className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-semibold transition-all hover:scale-105 shadow-lg"
          >
            Reessayer
          </button>
          <button
            onClick={onMainMenu}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
          >
            Menu
          </button>
        </div>

        {/* Message */}
        <p className="mt-6 text-sm text-gray-500 text-center max-w-sm">
          Analysez vos erreurs et tentez a nouveau.
        </p>
      </div>
    </div>
  );
}
