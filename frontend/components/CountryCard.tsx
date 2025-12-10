'use client';

import { Country, TIER_NAMES, REGIME_NAMES, COUNTRY_FLAGS } from '@/lib/types';
import { StatBar } from './StatBar';

interface CountryCardProps {
  country: Country;
  isSelected: boolean;
  onClick: () => void;
}

// Tier gradient backgrounds
const TIER_GRADIENTS: Record<number, string> = {
  1: 'from-yellow-900/20 to-transparent border-yellow-500',
  2: 'from-blue-900/20 to-transparent border-blue-500',
  3: 'from-gray-700/30 to-transparent border-gray-500',
  4: 'from-gray-800/30 to-transparent border-gray-600',
};

// Tier glow effects
const TIER_GLOWS: Record<number, string> = {
  1: 'shadow-yellow-500/20',
  2: 'shadow-blue-500/20',
  3: 'shadow-gray-500/10',
  4: 'shadow-gray-600/5',
};

export function CountryCard({ country, isSelected, onClick }: CountryCardProps) {
  const tierGradient = TIER_GRADIENTS[country.tier] || TIER_GRADIENTS[4];
  const tierGlow = TIER_GLOWS[country.tier] || TIER_GLOWS[4];
  const flag = COUNTRY_FLAGS[country.id] || '';

  // Determine status indicators
  const isAtWar = country.at_war.length > 0;
  const hasNukes = country.nuclear > 0;
  const isUnstable = country.stability < 30;

  return (
    <div
      className={`country-card relative p-4 rounded-xl cursor-pointer border-2 bg-gradient-to-br ${tierGradient} ${
        isSelected
          ? 'bg-gray-700 ring-2 ring-purple-500 ring-offset-2 ring-offset-gray-900'
          : 'bg-gray-800 hover:bg-gray-750'
      } shadow-lg ${tierGlow} hover:shadow-xl transition-all duration-200 group`}
      onClick={onClick}
    >
      {/* Status indicators */}
      <div className="absolute top-2 right-2 flex items-center gap-1">
        {isAtWar && (
          <span
            className="w-6 h-6 rounded-full bg-red-900/50 flex items-center justify-center text-xs animate-pulse"
            title="En guerre"
          >
            &#9876;
          </span>
        )}
        {hasNukes && (
          <span
            className="w-6 h-6 rounded-full bg-yellow-900/50 flex items-center justify-center text-xs"
            title={`Nucleaire: ${country.nuclear}`}
          >
            &#9762;
          </span>
        )}
        {isUnstable && (
          <span
            className="w-6 h-6 rounded-full bg-orange-900/50 flex items-center justify-center text-xs"
            title="Instable"
          >
            &#9888;
          </span>
        )}
      </div>

      {/* Header with flag */}
      <div className="flex items-start gap-3 mb-3">
        <div className="text-3xl group-hover:scale-110 transition-transform duration-200">
          {flag}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg truncate group-hover:text-purple-400 transition-colors">
            {country.name_fr}
          </h3>
          <p className="text-xs text-gray-400 truncate">
            {TIER_NAMES[country.tier]} | {REGIME_NAMES[country.regime] || country.regime}
          </p>
        </div>
      </div>

      {/* Power score */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1.5 rounded-lg ${
            country.tier === 1 ? 'bg-yellow-900/30 border border-yellow-700/50' :
            country.tier === 2 ? 'bg-blue-900/30 border border-blue-700/50' :
            'bg-gray-700/50 border border-gray-600/50'
          }`}>
            <div className="text-xl font-bold text-yellow-400">
              {country.power_score.toFixed(0)}
            </div>
          </div>
          <div className="text-xs text-gray-500">
            Score de<br/>puissance
          </div>
        </div>

        {/* Population indicator */}
        <div className="text-right">
          <div className="text-sm font-medium">{country.population}</div>
          <div className="text-xs text-gray-500">Population</div>
        </div>
      </div>

      {/* Stats */}
      <div className="space-y-1.5">
        <StatBar label="Economie" value={country.economy} color="bg-green-500" />
        <StatBar label="Militaire" value={country.military} color="bg-red-500" />
        <StatBar label="Technologie" value={country.technology} color="bg-blue-500" />
        <StatBar label="Stabilite" value={country.stability} color="auto" />
      </div>

      {/* War status */}
      {isAtWar && (
        <div className="mt-3 px-2 py-1.5 bg-red-900/30 rounded-lg border border-red-700/30">
          <div className="flex items-center gap-1.5 text-xs text-red-400">
            <span>&#9876;</span>
            <span className="font-medium">En guerre:</span>
            <span className="truncate">{country.at_war.map(id => COUNTRY_FLAGS[id] || id).join(' ')}</span>
          </div>
        </div>
      )}

      {/* Blocs */}
      {country.blocs.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {country.blocs.slice(0, 3).map((bloc) => (
            <span
              key={bloc}
              className="px-2 py-0.5 bg-gray-700/70 rounded-full text-xs border border-gray-600/50 hover:bg-gray-600 transition-colors"
            >
              {bloc}
            </span>
          ))}
          {country.blocs.length > 3 && (
            <span className="px-2 py-0.5 text-xs text-gray-500">
              +{country.blocs.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Allies/Rivals quick view */}
      {(country.allies.length > 0 || country.rivals.length > 0) && (
        <div className="mt-3 pt-3 border-t border-gray-700/50 flex items-center justify-between text-xs">
          {country.allies.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-green-500">&#128077;</span>
              <span className="text-gray-400">{country.allies.length} allies</span>
            </div>
          )}
          {country.rivals.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-red-500">&#128078;</span>
              <span className="text-gray-400">{country.rivals.length} rivaux</span>
            </div>
          )}
        </div>
      )}

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-purple-500 rounded-full" />
      )}
    </div>
  );
}
