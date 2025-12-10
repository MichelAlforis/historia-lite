'use client';

import { useState } from 'react';
import { useMultiplayerStore } from '@/stores/multiplayerStore';

interface CreateLobbyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateLobbyModal({ isOpen, onClose, onCreated }: CreateLobbyModalProps) {
  const { createLobby, connectionError, clearError } = useMultiplayerStore();

  const [name, setName] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [gameMode, setGameMode] = useState<'simultaneous' | 'turn_based'>('simultaneous');
  const [turnTimer, setTurnTimer] = useState(60);
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) return;

    setIsCreating(true);
    const lobby = await createLobby(name.trim(), maxPlayers, gameMode, turnTimer);
    setIsCreating(false);

    if (lobby) {
      onCreated();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden animate-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-blue-900/50 to-gray-800 border-b border-gray-700">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <span>{'🎮'}</span>
            Creer un salon
          </h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error */}
          {connectionError && (
            <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg flex justify-between items-center">
              <span className="text-sm">{connectionError}</span>
              <button type="button" onClick={clearError} className="text-gray-400 hover:text-white">
                {'✕'}
              </button>
            </div>
          )}

          {/* Lobby name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nom du salon
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ma partie multijoueur"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              required
              maxLength={50}
            />
          </div>

          {/* Max players */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nombre de joueurs maximum
            </label>
            <div className="flex items-center gap-2">
              {[2, 4, 6, 8].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setMaxPlayers(n)}
                  className={`flex-1 py-2 rounded-lg transition-colors ${
                    maxPlayers === n
                      ? 'bg-blue-600'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Game mode */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Mode de jeu
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setGameMode('simultaneous')}
                className={`p-3 rounded-lg text-center transition-colors ${
                  gameMode === 'simultaneous'
                    ? 'bg-blue-600 border-2 border-blue-400'
                    : 'bg-gray-700 hover:bg-gray-600 border-2 border-transparent'
                }`}
              >
                <div className="text-lg mb-1">{'⚡'}</div>
                <div className="font-medium">Simultane</div>
                <div className="text-xs text-gray-400">Tous jouent en meme temps</div>
              </button>
              <button
                type="button"
                onClick={() => setGameMode('turn_based')}
                className={`p-3 rounded-lg text-center transition-colors ${
                  gameMode === 'turn_based'
                    ? 'bg-blue-600 border-2 border-blue-400'
                    : 'bg-gray-700 hover:bg-gray-600 border-2 border-transparent'
                }`}
              >
                <div className="text-lg mb-1">{'🔄'}</div>
                <div className="font-medium">Tour par tour</div>
                <div className="text-xs text-gray-400">Chaque joueur joue a son tour</div>
              </button>
            </div>
          </div>

          {/* Turn timer (only for turn-based) */}
          {gameMode === 'turn_based' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Temps par tour (secondes)
              </label>
              <div className="flex items-center gap-2">
                {[30, 60, 90, 120].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTurnTimer(t)}
                    className={`flex-1 py-2 rounded-lg transition-colors ${
                      turnTimer === t
                        ? 'bg-blue-600'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    {t}s
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isCreating || !name.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isCreating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creation...
                </>
              ) : (
                'Creer le salon'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
