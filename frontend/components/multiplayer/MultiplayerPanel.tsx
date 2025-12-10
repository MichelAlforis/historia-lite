'use client';

import { useState, useEffect, useCallback } from 'react';
import { useMultiplayerStore } from '@/stores/multiplayerStore';
import { Country } from '@/lib/types';
import LobbyList from './LobbyList';
import LobbyRoom from './LobbyRoom';
import CreateLobbyModal from './CreateLobbyModal';

interface MultiplayerPanelProps {
  countries: Country[];
  onStartGame: () => void;
  onClose: () => void;
}

type Screen = 'setup' | 'lobbies' | 'lobby';

export default function MultiplayerPanel({ countries, onStartGame, onClose }: MultiplayerPanelProps) {
  const {
    playerId,
    playerName,
    setPlayerId,
    setPlayerName,
    currentLobby,
    isGameStarted,
    joinLobby,
    disconnect,
  } = useMultiplayerStore();

  const [screen, setScreen] = useState<Screen>('setup');
  const [inputName, setInputName] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Generate a unique player ID on first render
  useEffect(() => {
    if (!playerId) {
      const id = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setPlayerId(id);
    }
  }, [playerId, setPlayerId]);

  // Navigate to lobby room when joined
  useEffect(() => {
    if (currentLobby) {
      setScreen('lobby');
    }
  }, [currentLobby]);

  // Start game when all ready
  useEffect(() => {
    if (isGameStarted) {
      onStartGame();
    }
  }, [isGameStarted, onStartGame]);

  const handleSetupComplete = useCallback(() => {
    if (!inputName.trim()) return;
    setPlayerName(inputName.trim());
    setScreen('lobbies');
  }, [inputName, setPlayerName]);

  const handleJoinLobby = useCallback(async (lobbyId: string) => {
    const success = await joinLobby(lobbyId);
    if (success) {
      setScreen('lobby');
    }
  }, [joinLobby]);

  const handleLeaveLobby = useCallback(() => {
    disconnect();
    setScreen('lobbies');
  }, [disconnect]);

  const handleLobbyCreated = useCallback(() => {
    setShowCreateModal(false);
    setScreen('lobby');
  }, []);

  const handleClose = useCallback(() => {
    disconnect();
    onClose();
  }, [disconnect, onClose]);

  // Setup screen
  if (screen === 'setup' || !playerName) {
    return (
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={handleClose}
      >
        <div
          className="bg-gray-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden animate-scaleIn"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 bg-gradient-to-r from-purple-900/50 to-gray-800 border-b border-gray-700">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span>{'🎮'}</span>
              Mode Multijoueur
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Jouez avec vos amis en temps reel
            </p>
          </div>

          {/* Content */}
          <div className="p-6">
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">{'🌍'}</div>
              <h3 className="text-lg font-bold">Bienvenue dans Historia Lite Multijoueur</h3>
              <p className="text-gray-400 text-sm mt-2">
                Affrontez d'autres joueurs dans une simulation geopolitique en temps reel
              </p>
            </div>

            {/* Player name input */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Votre nom de joueur
                </label>
                <input
                  type="text"
                  value={inputName}
                  onChange={(e) => setInputName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSetupComplete()}
                  placeholder="Entrez votre nom..."
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-lg"
                  maxLength={20}
                  autoFocus
                />
              </div>

              <button
                onClick={handleSetupComplete}
                disabled={!inputName.trim()}
                className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continuer
              </button>

              <button
                onClick={handleClose}
                className="w-full py-2 text-gray-400 hover:text-white transition-colors"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Lobbies screen
  if (screen === 'lobbies') {
    return (
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={handleClose}
      >
        <div
          className="bg-gray-900 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-scaleIn"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 z-10 px-6 py-4 bg-gray-900 border-b border-gray-800 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>{'🎮'}</span>
                Salons Multijoueur
              </h2>
              <p className="text-sm text-gray-400">
                Connecte en tant que <span className="text-purple-400">{playerName}</span>
              </p>
            </div>
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              {'✕'}
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <LobbyList
              onJoinLobby={handleJoinLobby}
              onCreateLobby={() => setShowCreateModal(true)}
            />
          </div>
        </div>

        {/* Create lobby modal */}
        <CreateLobbyModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreated={handleLobbyCreated}
        />
      </div>
    );
  }

  // Lobby room screen
  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={handleClose}
    >
      <div
        className="bg-gray-900 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto animate-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-6 py-4 bg-gray-900 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span>{'🎮'}</span>
              {currentLobby?.name || 'Salon'}
            </h2>
            <p className="text-sm text-gray-400">
              Connecte en tant que <span className="text-purple-400">{playerName}</span>
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            {'✕'}
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <LobbyRoom countries={countries} onLeave={handleLeaveLobby} />
        </div>
      </div>
    </div>
  );
}
