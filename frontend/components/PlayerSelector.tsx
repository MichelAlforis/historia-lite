'use client';

import { useState, useEffect } from 'react';
import { Country, COUNTRY_FLAGS, TIER_NAMES } from '@/lib/types';
import { selectPlayerCountry, getPlayerCountry } from '@/lib/api';

interface PlayerSelectorProps {
  countries: Country[];
  selectedCountry: Country | null;
  onSelectCountry: (country: Country | null) => void;
}

export default function PlayerSelector({
  countries,
  selectedCountry,
  onSelectCountry,
}: PlayerSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [playerCountryId, setPlayerCountryId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'tier1' | 'tier2' | 'tier3'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Load player country from API on mount
  useEffect(() => {
    loadPlayerCountry();
  }, []);

  const loadPlayerCountry = async () => {
    try {
      const data = await getPlayerCountry();
      if (data.player_country_id) {
        setPlayerCountryId(data.player_country_id);
        const country = countries.find(c => c.id === data.player_country_id);
        if (country) {
          onSelectCountry(country);
        }
      }
    } catch (error) {
      console.error('Failed to load player country:', error);
    }
  };

  const handleSelectPlayer = async (country: Country) => {
    try {
      await selectPlayerCountry(country.id);
      setPlayerCountryId(country.id);
      onSelectCountry(country);
      setIsOpen(false);
      setSearchQuery('');
    } catch (error) {
      console.error('Failed to select player country:', error);
    }
  };

  const handleClearPlayer = () => {
    setPlayerCountryId(null);
    onSelectCountry(null);
  };

  // Filter countries
  const filteredCountries = countries.filter(country => {
    if (filter !== 'all' && `tier${country.tier}` !== filter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        country.name_fr.toLowerCase().includes(query) ||
        country.id.toLowerCase().includes(query)
      );
    }
    return true;
  }).sort((a, b) => a.tier - b.tier || b.power_score - a.power_score);

  // Playable countries (tier 1-3)
  const playableCountries = filteredCountries.filter(c => c.tier <= 3);

  return (
    <div className="relative">
      {/* Current player button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
          playerCountryId
            ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
      >
        {playerCountryId ? (
          <>
            <span className="text-xl">{COUNTRY_FLAGS[playerCountryId]}</span>
            <span className="font-medium">
              {countries.find(c => c.id === playerCountryId)?.name_fr || playerCountryId}
            </span>
            <span className="text-xs bg-black/20 px-1.5 py-0.5 rounded">Joueur</span>
          </>
        ) : (
          <>
            <span className="text-lg">&#128100;</span>
            <span>Choisir un pays</span>
          </>
        )}
        <span className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}>&#9660;</span>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-gray-800 rounded-lg shadow-2xl border border-gray-700 z-50 overflow-hidden animate-scaleIn">
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-amber-900/50 to-gray-700 border-b border-gray-700">
            <div className="font-bold">Selectionnez votre pays</div>
            <div className="text-xs text-gray-400">Jouez en tant que puissance mondiale</div>
          </div>

          {/* Search */}
          <div className="px-3 py-2 border-b border-gray-700">
            <div className="relative">
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-gray-700 text-white text-sm rounded-lg pl-8 pr-3 py-2 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <span className="absolute left-2.5 top-2.5 text-gray-500 text-sm">&#128269;</span>
            </div>
          </div>

          {/* Filters */}
          <div className="px-3 py-2 border-b border-gray-700 flex gap-1">
            {([
              { key: 'all', label: 'Tous' },
              { key: 'tier1', label: 'Superpuissances' },
              { key: 'tier2', label: 'Majeures' },
              { key: 'tier3', label: 'Regionales' },
            ] as const).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-2 py-1 text-xs rounded transition-all ${
                  filter === key
                    ? 'bg-amber-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Country list */}
          <div className="max-h-64 overflow-y-auto scrollbar-thin">
            {playableCountries.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500">
                <span className="text-2xl block mb-1">&#128269;</span>
                Aucun pays trouve
              </div>
            ) : (
              playableCountries.map(country => (
                <button
                  key={country.id}
                  onClick={() => handleSelectPlayer(country)}
                  className={`w-full px-3 py-2 flex items-center gap-3 hover:bg-gray-700/50 transition-colors ${
                    playerCountryId === country.id ? 'bg-amber-900/30' : ''
                  }`}
                >
                  <span className="text-2xl">{COUNTRY_FLAGS[country.id]}</span>
                  <div className="flex-1 text-left">
                    <div className="font-medium">{country.name_fr}</div>
                    <div className="text-xs text-gray-400">
                      {TIER_NAMES[country.tier]} | Score: {Math.round(country.power_score)}
                    </div>
                  </div>
                  {playerCountryId === country.id && (
                    <span className="text-amber-400">&#10003;</span>
                  )}
                </button>
              ))
            )}
          </div>

          {/* Footer with clear button */}
          {playerCountryId && (
            <div className="px-3 py-2 border-t border-gray-700 bg-gray-750">
              <button
                onClick={handleClearPlayer}
                className="w-full px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
              >
                Annuler la selection
              </button>
            </div>
          )}
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
