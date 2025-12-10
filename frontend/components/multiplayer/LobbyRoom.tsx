'use client';

import { useCallback, useMemo } from 'react';
import { useMultiplayerStore } from '@/stores/multiplayerStore';
import { Country } from '@/lib/types';
import ChatPanel from './ChatPanel';

interface LobbyRoomProps {
  countries: Country[];
  onLeave: () => void;
}

export default function LobbyRoom({ countries, onLeave }: LobbyRoomProps) {
  const {
    currentLobby,
    playerId,
    selectCountry,
    toggleReady,
    startGame,
    leaveLobby,
    connectionError,
    clearError,
  } = useMultiplayerStore();

  const currentPlayer = useMemo(
    () => currentLobby?.players.find((p) => p.id === playerId),
    [currentLobby, playerId]
  );

  const isHost = currentPlayer?.is_host ?? false;

  const canStartGame = useMemo(() => {
    if (!currentLobby || !isHost) return false;
    // All players must be ready and have selected a country
    return currentLobby.players.every((p) => p.is_ready && p.country_id);
  }, [currentLobby, isHost]);

  const selectedCountries = useMemo(
    () => new Set(currentLobby?.players.map((p) => p.country_id).filter(Boolean)),
    [currentLobby]
  );

  const handleSelectCountry = useCallback(
    (countryId: string) => {
      if (!currentPlayer?.is_ready && !selectedCountries.has(countryId)) {
        selectCountry(countryId);
      }
    },
    [currentPlayer?.is_ready, selectedCountries, selectCountry]
  );

  const handleLeave = useCallback(async () => {
    await leaveLobby();
    onLeave();
  }, [leaveLobby, onLeave]);

  if (!currentLobby) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 text-center">
        <span className="text-4xl">{'⚠️'}</span>
        <p className="mt-4 text-gray-400">Salon non trouve</p>
        <button
          onClick={onLeave}
          className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
        >
          Retour
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gray-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span>{'🎮'}</span>
              {currentLobby.name}
            </h2>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
              <span>
                {currentLobby.game_mode === 'simultaneous' ? 'Mode simultane' : 'Tour par tour'}
              </span>
              {currentLobby.game_mode === 'turn_based' && (
                <span>{currentLobby.turn_timer}s par tour</span>
              )}
            </div>
          </div>
          <button
            onClick={handleLeave}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            Quitter
          </button>
        </div>
      </div>

      {/* Error */}
      {connectionError && (
        <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg flex justify-between items-center">
          <span>{connectionError}</span>
          <button onClick={clearError} className="text-gray-400 hover:text-white">
            {'✕'}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Players list */}
        <div className="bg-gray-800 rounded-xl p-4">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <span>{'👥'}</span>
            Joueurs ({currentLobby.players.length}/{currentLobby.max_players})
          </h3>
          <div className="space-y-2">
            {currentLobby.players.map((player) => {
              const country = countries.find((c) => c.id === player.country_id);
              return (
                <div
                  key={player.id}
                  className={`p-3 rounded-lg ${
                    player.id === playerId ? 'bg-blue-900/50 border border-blue-700' : 'bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {player.is_host && (
                        <span title="Hote" className="text-amber-400">
                          {'👑'}
                        </span>
                      )}
                      <span className="font-medium">{player.name}</span>
                    </div>
                    {player.is_ready ? (
                      <span className="px-2 py-0.5 bg-green-600 rounded text-xs">Pret</span>
                    ) : (
                      <span className="px-2 py-0.5 bg-gray-600 rounded text-xs">En attente</span>
                    )}
                  </div>
                  {country && (
                    <div className="mt-2 text-sm text-gray-400">
                      Pays: <span className="text-white">{country.name_fr}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Ready button */}
          <div className="mt-4 space-y-2">
            <button
              onClick={toggleReady}
              disabled={!currentPlayer?.country_id}
              className={`w-full py-2 rounded-lg transition-colors ${
                currentPlayer?.is_ready
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-green-600 hover:bg-green-700'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {currentPlayer?.is_ready ? 'Annuler' : 'Je suis pret'}
            </button>

            {isHost && (
              <button
                onClick={startGame}
                disabled={!canStartGame}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Lancer la partie
              </button>
            )}
          </div>
        </div>

        {/* Country selection */}
        <div className="bg-gray-800 rounded-xl p-4">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <span>{'🌍'}</span>
            Choisir un pays
          </h3>
          <div className="max-h-[400px] overflow-y-auto space-y-2 pr-2">
            {countries
              .filter((c) => c.tier <= 2) // Only tier 1 & 2 playable
              .sort((a, b) => a.tier - b.tier || b.power_score - a.power_score)
              .map((country) => {
                const isSelected = currentPlayer?.country_id === country.id;
                const isTaken = selectedCountries.has(country.id) && !isSelected;
                const takenBy = currentLobby.players.find((p) => p.country_id === country.id);

                return (
                  <button
                    key={country.id}
                    onClick={() => handleSelectCountry(country.id)}
                    disabled={isTaken || currentPlayer?.is_ready}
                    className={`w-full p-3 rounded-lg text-left transition-colors ${
                      isSelected
                        ? 'bg-blue-600 border-2 border-blue-400'
                        : isTaken
                        ? 'bg-gray-700/50 cursor-not-allowed opacity-60'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{country.name_fr}</div>
                        <div className="text-xs text-gray-400">
                          Tier {country.tier} | Score: {country.power_score}
                        </div>
                      </div>
                      {isTaken && takenBy && (
                        <span className="text-xs text-gray-500">{takenBy.name}</span>
                      )}
                      {isSelected && <span className="text-green-400">{'✓'}</span>}
                    </div>
                  </button>
                );
              })}
          </div>
        </div>

        {/* Chat */}
        <ChatPanel />
      </div>
    </div>
  );
}
