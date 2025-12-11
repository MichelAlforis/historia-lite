'use client';

import { useRef } from 'react';

interface VictoryScreenProps {
  scenarioName: string;
  finalScore: number;
  maxScore: number;
  yearsPlayed: number;
  objectives: {
    id: string;
    name: string;
    status: 'completed' | 'failed' | 'pending';
    points: number;
  }[];
  onRestart: () => void;
  onMainMenu: () => void;
}

export default function VictoryScreen({
  scenarioName,
  finalScore,
  maxScore,
  yearsPlayed,
  objectives,
  onRestart,
  onMainMenu,
}: VictoryScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  const completedCount = objectives.filter(o => o.status === 'completed').length;
  const scorePercentage = maxScore > 0 ? Math.round((finalScore / maxScore) * 100) : 0;

  // Determiner le rang selon le score
  const getRank = () => {
    if (scorePercentage >= 100) return { label: 'Parfait', color: 'text-yellow-400', stars: 3 };
    if (scorePercentage >= 80) return { label: 'Excellent', color: 'text-green-400', stars: 3 };
    if (scorePercentage >= 60) return { label: 'Bien', color: 'text-blue-400', stars: 2 };
    if (scorePercentage >= 40) return { label: 'Correct', color: 'text-gray-300', stars: 1 };
    return { label: 'Insuffisant', color: 'text-gray-500', stars: 0 };
  };

  const rank = getRank();

  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 overflow-y-auto">
      {/* Video de fond - subtile */}
      <video
        ref={videoRef}
        autoPlay
        muted
        loop
        playsInline
        className="absolute inset-0 w-full h-full object-cover opacity-20"
      >
        <source src="/video/victory.mp4" type="video/mp4" />
      </video>

      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-gray-900/50" />

      {/* Contenu - visible immediatement */}
      <div className="relative z-10 flex flex-col items-center min-h-screen p-6 py-12">
        {/* Header - Titre compact */}
        <div className="text-center mb-6">
          <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500 mb-2">
            VICTOIRE
          </h1>
          <p className="text-lg text-gray-400">{scenarioName}</p>
        </div>

        {/* Score Card - Element principal */}
        <div className="bg-gray-800/80 backdrop-blur rounded-2xl p-6 max-w-md w-full mb-6 border border-yellow-500/20 shadow-xl shadow-yellow-500/5">
          {/* Stars */}
          <div className="flex justify-center gap-2 mb-4">
            {[1, 2, 3].map((star) => (
              <span
                key={star}
                className={`text-3xl transition-all ${
                  star <= rank.stars ? 'text-yellow-400 scale-100' : 'text-gray-600 scale-75'
                }`}
              >
                ★
              </span>
            ))}
          </div>

          {/* Score */}
          <div className="text-center mb-4">
            <div className="text-5xl font-bold text-white mb-1">{finalScore}</div>
            <div className="text-sm text-gray-400">sur {maxScore} points</div>
            <div className={`text-lg font-semibold mt-2 ${rank.color}`}>
              {rank.label}
            </div>
          </div>

          {/* Stats row */}
          <div className="flex justify-around border-t border-gray-700 pt-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{yearsPlayed}</div>
              <div className="text-xs text-gray-500">Annees</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{completedCount}</div>
              <div className="text-xs text-gray-500">Objectifs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400">{scorePercentage}%</div>
              <div className="text-xs text-gray-500">Completion</div>
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
                      : 'bg-gray-700/30 text-gray-500'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>{obj.status === 'completed' ? '✓' : '○'}</span>
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
            className="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-gray-900 rounded-xl font-semibold transition-all hover:scale-105 shadow-lg"
          >
            Rejouer
          </button>
          <button
            onClick={onMainMenu}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
          >
            Menu
          </button>
        </div>
      </div>
    </div>
  );
}
