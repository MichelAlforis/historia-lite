'use client';

import { useState } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { Country, COUNTRY_FLAGS } from '@/lib/types';

// Pays jouables (Tier 1-3)
const PLAYABLE_COUNTRIES = [
  { id: 'USA', name_fr: 'Etats-Unis', tier: 1, difficulty: 'Facile' },
  { id: 'CHN', name_fr: 'Chine', tier: 1, difficulty: 'Facile' },
  { id: 'RUS', name_fr: 'Russie', tier: 2, difficulty: 'Normal' },
  { id: 'FRA', name_fr: 'France', tier: 2, difficulty: 'Normal' },
  { id: 'GBR', name_fr: 'Royaume-Uni', tier: 2, difficulty: 'Normal' },
  { id: 'DEU', name_fr: 'Allemagne', tier: 2, difficulty: 'Normal' },
  { id: 'JPN', name_fr: 'Japon', tier: 2, difficulty: 'Normal' },
  { id: 'IND', name_fr: 'Inde', tier: 2, difficulty: 'Normal' },
  { id: 'BRA', name_fr: 'Bresil', tier: 3, difficulty: 'Difficile' },
];

interface CountrySelectorProps {
  onSelect: (countryId: string) => void;
}

export default function CountrySelector({ onSelect }: CountrySelectorProps) {
  const { world, isLoading } = useGameStore();
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Get country data from world state
  const getCountryData = (id: string): Country | undefined => {
    return world?.countries.find(c => c.id === id);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Facile': return 'bg-emerald-100 text-emerald-700';
      case 'Normal': return 'bg-amber-100 text-amber-700';
      case 'Difficile': return 'bg-rose-100 text-rose-700';
      default: return 'bg-stone-100 text-stone-700';
    }
  };

  return (
    <div className="min-h-screen bg-amber-50 flex flex-col items-center justify-center p-8">
      {/* Title */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-light text-stone-800 mb-2">
          Choisissez votre nation
        </h1>
        <p className="text-stone-500 text-lg">
          Selectionnez un pays pour commencer votre partie
        </p>
      </div>

      {/* Country Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl">
        {PLAYABLE_COUNTRIES.map(pc => {
          const countryData = getCountryData(pc.id);
          const isHovered = hoveredCountry === pc.id;

          return (
            <button
              key={pc.id}
              onClick={() => onSelect(pc.id)}
              onMouseEnter={() => setHoveredCountry(pc.id)}
              onMouseLeave={() => setHoveredCountry(null)}
              disabled={isLoading}
              className={`
                bg-white rounded-2xl p-6 shadow-md
                transition-all duration-200 text-left
                hover:shadow-xl hover:scale-[1.02]
                disabled:opacity-50 disabled:cursor-not-allowed
                ${isHovered ? 'ring-2 ring-sky-300' : ''}
              `}
            >
              {/* Flag + Name */}
              <div className="flex items-center gap-4 mb-4">
                <span className="text-5xl">{COUNTRY_FLAGS[pc.id] || '🏳️'}</span>
                <div>
                  <h2 className="text-xl font-semibold text-stone-800">{pc.name_fr}</h2>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getDifficultyColor(pc.difficulty)}`}>
                    {pc.difficulty}
                  </span>
                </div>
              </div>

              {/* Stats bars */}
              {countryData && (
                <div className="space-y-2">
                  <StatBar label="Economie" value={countryData.economy} color="emerald" />
                  <StatBar label="Militaire" value={countryData.military} color="rose" />
                  <StatBar label="Tech" value={countryData.technology} color="sky" />
                </div>
              )}

              {/* Tier indicator */}
              <div className="mt-4 text-xs text-stone-400">
                Tier {pc.tier}
              </div>
            </button>
          );
        })}
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="mt-8 text-stone-500 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
          <span>Chargement...</span>
        </div>
      )}
    </div>
  );
}

// Mini stat bar component
function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-200',
    rose: 'bg-rose-200',
    sky: 'bg-sky-200',
    amber: 'bg-amber-200',
  };

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-stone-500 w-16">{label}</span>
      <div className="flex-1 h-2 bg-stone-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-stone-600 w-8 text-right">{value}</span>
    </div>
  );
}
