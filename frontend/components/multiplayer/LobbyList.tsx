'use client';

import { useEffect, useState } from 'react';
import { useMultiplayerStore, LobbyInfo } from '@/stores/multiplayerStore';

interface LobbyListProps {
  onJoinLobby: (lobbyId: string) => void;
  onCreateLobby: () => void;
}

export default function LobbyList({ onJoinLobby, onCreateLobby }: LobbyListProps) {
  const { availableLobbies, fetchLobbies, connectionError, clearError } = useMultiplayerStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadLobbies = async () => {
      setIsLoading(true);
      await fetchLobbies();
      setIsLoading(false);
    };

    loadLobbies();

    // Refresh every 5 seconds
    const interval = setInterval(loadLobbies, 5000);
    return () => clearInterval(interval);
  }, [fetchLobbies]);

  const getGameModeLabel = (mode: string) => {
    return mode === 'simultaneous' ? 'Simultane' : 'Tour par tour';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'waiting':
        return <span className="px-2 py-0.5 bg-green-600 rounded text-xs">En attente</span>;
      case 'in_progress':
        return <span className="px-2 py-0.5 bg-yellow-600 rounded text-xs">En cours</span>;
      case 'finished':
        return <span className="px-2 py-0.5 bg-gray-600 rounded text-xs">Termine</span>;
      default:
        return null;
    }
  };

  if (isLoading && availableLobbies.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="ml-3 text-gray-400">Chargement des salons...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span>{'🎮'}</span>
          Salons Multijoueur
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchLobbies()}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            title="Actualiser"
          >
            {'🔄'}
          </button>
          <button
            onClick={onCreateLobby}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <span>{'+'}</span>
            Creer un salon
          </button>
        </div>
      </div>

      {/* Error */}
      {connectionError && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg flex justify-between items-center">
          <span>{connectionError}</span>
          <button onClick={clearError} className="text-gray-400 hover:text-white">
            {'✕'}
          </button>
        </div>
      )}

      {/* Lobbies list */}
      {availableLobbies.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <span className="text-4xl block mb-2">{'🏚️'}</span>
          <p>Aucun salon disponible</p>
          <p className="text-sm mt-2">Creez un salon pour commencer une partie multijoueur</p>
        </div>
      ) : (
        <div className="space-y-3">
          {availableLobbies.map((lobby) => (
            <LobbyCard
              key={lobby.id}
              lobby={lobby}
              onJoin={() => onJoinLobby(lobby.id)}
              getGameModeLabel={getGameModeLabel}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface LobbyCardProps {
  lobby: LobbyInfo;
  onJoin: () => void;
  getGameModeLabel: (mode: string) => string;
  getStatusBadge: (status: string) => React.ReactNode;
}

function LobbyCard({ lobby, onJoin, getGameModeLabel, getStatusBadge }: LobbyCardProps) {
  const canJoin = lobby.status === 'waiting' && lobby.players.length < lobby.max_players;

  return (
    <div className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-bold text-lg">{lobby.name}</h3>
            {getStatusBadge(lobby.status)}
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1">
              <span>{'👥'}</span>
              {lobby.players.length}/{lobby.max_players} joueurs
            </span>
            <span className="flex items-center gap-1">
              <span>{'🎯'}</span>
              {getGameModeLabel(lobby.game_mode)}
            </span>
            {lobby.game_mode === 'turn_based' && (
              <span className="flex items-center gap-1">
                <span>{'⏱️'}</span>
                {lobby.turn_timer}s/tour
              </span>
            )}
          </div>

          {/* Players preview */}
          {lobby.players.length > 0 && (
            <div className="flex items-center gap-2 mt-3">
              {lobby.players.slice(0, 4).map((player) => (
                <div
                  key={player.id}
                  className={`px-2 py-1 rounded text-xs ${
                    player.is_host ? 'bg-amber-600' : 'bg-gray-600'
                  }`}
                  title={player.is_host ? 'Hote' : 'Joueur'}
                >
                  {player.name}
                  {player.is_ready && <span className="ml-1">{'✓'}</span>}
                </div>
              ))}
              {lobby.players.length > 4 && (
                <span className="text-xs text-gray-500">+{lobby.players.length - 4}</span>
              )}
            </div>
          )}
        </div>

        <button
          onClick={onJoin}
          disabled={!canJoin}
          className={`px-4 py-2 rounded-lg transition-colors ${
            canJoin
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-gray-600 cursor-not-allowed opacity-50'
          }`}
        >
          {canJoin ? 'Rejoindre' : lobby.status === 'in_progress' ? 'En cours' : 'Complet'}
        </button>
      </div>
    </div>
  );
}
