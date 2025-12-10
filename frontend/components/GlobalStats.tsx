'use client';

import { useState, useEffect } from 'react';
import { WorldState, COUNTRY_FLAGS, InfluenceRanking } from '@/lib/types';
import { getInfluenceRankings } from '@/lib/api';

interface GlobalStatsProps {
  world: WorldState;
  onShowInfluence?: () => void;
}

export function GlobalStats({ world, onShowInfluence }: GlobalStatsProps) {
  const [influenceRankings, setInfluenceRankings] = useState<InfluenceRanking[]>([]);
  const [loadingInfluence, setLoadingInfluence] = useState(true);

  useEffect(() => {
    loadInfluenceRankings();
  }, [world.year]);

  const loadInfluenceRankings = async () => {
    try {
      const data = await getInfluenceRankings();
      setInfluenceRankings(data.rankings);
    } catch (error) {
      console.error('Failed to load influence rankings:', error);
    } finally {
      setLoadingInfluence(false);
    }
  };

  // Calculate top countries by power
  const topPowers = [...world.countries]
    .sort((a, b) => b.power_score - a.power_score)
    .slice(0, 5);

  // Count nuclear powers
  const nuclearCount = world.countries.filter(c => c.nuclear > 0).length;

  // Count active conflicts
  const atWarCount = new Set(
    world.countries.flatMap(c => c.at_war)
  ).size;

  // Count contested zones
  const contestedZones = world.influence_zones.filter(z => z.contested_by && z.contested_by.length > 0);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="font-bold text-lg mb-3 text-gray-200">Statistiques Mondiales</h2>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-xl font-bold">{world.total_countries}</div>
          <div className="text-xs text-gray-400">Pays</div>
        </div>
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-xl font-bold text-yellow-400">{nuclearCount}</div>
          <div className="text-xs text-gray-400">Puissances nucleaires</div>
        </div>
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-xl font-bold text-red-400">{world.active_wars}</div>
          <div className="text-xs text-gray-400">Conflits actifs</div>
        </div>
        <div
          className="bg-gray-700 rounded p-2 text-center cursor-pointer hover:bg-gray-600 transition-colors"
          onClick={onShowInfluence}
        >
          <div className="text-xl font-bold text-blue-400">{world.influence_zones.length}</div>
          <div className="text-xs text-gray-400">Zones d&apos;influence</div>
        </div>
      </div>

      {/* Top powers */}
      <h3 className="font-bold text-sm text-gray-300 mb-2">Top 5 Puissances</h3>
      <div className="space-y-1">
        {topPowers.map((country, index) => (
          <div
            key={country.id}
            className="flex items-center justify-between bg-gray-700 rounded px-2 py-1"
          >
            <div className="flex items-center gap-2">
              <span className={`w-5 h-5 flex items-center justify-center rounded text-xs font-bold ${
                index === 0 ? 'bg-yellow-500 text-black' :
                index === 1 ? 'bg-gray-400 text-black' :
                index === 2 ? 'bg-amber-700' :
                'bg-gray-600'
              }`}>
                {index + 1}
              </span>
              <span className="text-sm">{country.name_fr}</span>
            </div>
            <span className="text-sm font-bold text-yellow-400">
              {country.power_score.toFixed(0)}
            </span>
          </div>
        ))}
      </div>

      {/* Influence Rankings */}
      {!loadingInfluence && influenceRankings.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-sm text-gray-300">Top 3 Influence Mondiale</h3>
            {onShowInfluence && (
              <button
                onClick={onShowInfluence}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Voir tout
              </button>
            )}
          </div>
          <div className="space-y-1">
            {influenceRankings.slice(0, 3).map((ranking, index) => (
              <div
                key={ranking.power_id}
                className="flex items-center justify-between bg-gray-700 rounded px-2 py-1"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-5 h-5 flex items-center justify-center rounded text-xs font-bold ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-gray-400 text-black' :
                    'bg-amber-700'
                  }`}>
                    {index + 1}
                  </span>
                  <span className="text-sm">
                    {COUNTRY_FLAGS[ranking.power_id] || ''} {ranking.power_id}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-purple-400">
                    {ranking.total_influence}
                  </span>
                  <span className="text-xs text-gray-500 ml-1">
                    ({ranking.zones_dominated} zones)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contested Zones */}
      {contestedZones.length > 0 && (
        <div className="mt-4">
          <h3 className="font-bold text-sm text-orange-400 mb-2">
            Zones Contestees ({contestedZones.length})
          </h3>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {contestedZones.slice(0, 5).map(zone => (
              <div
                key={zone.id}
                className="bg-orange-900/30 rounded px-2 py-1 text-xs cursor-pointer hover:bg-orange-900/50"
                onClick={onShowInfluence}
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium">{zone.name_fr}</span>
                  <span className="text-orange-400">
                    {zone.contested_by?.length || 0} contestants
                  </span>
                </div>
                {zone.dominant_power && (
                  <div className="text-gray-400 mt-0.5">
                    Dominant: {COUNTRY_FLAGS[zone.dominant_power] || ''} {zone.dominant_power}
                  </div>
                )}
              </div>
            ))}
            {contestedZones.length > 5 && (
              <button
                onClick={onShowInfluence}
                className="w-full text-center text-xs text-gray-500 hover:text-gray-400 py-1"
              >
                +{contestedZones.length - 5} autres zones...
              </button>
            )}
          </div>
        </div>
      )}

      {/* Active conflicts */}
      {world.active_conflicts.length > 0 && (
        <div className="mt-4">
          <h3 className="font-bold text-sm text-red-400 mb-2">Conflits en cours</h3>
          <div className="space-y-1">
            {world.active_conflicts.map(conflict => (
              <div
                key={conflict.id}
                className="bg-red-900/30 rounded px-2 py-1 text-xs"
              >
                <div className="flex justify-between">
                  <span>{conflict.attackers.join(', ')}</span>
                  <span className="text-red-400">vs</span>
                  <span>{conflict.defenders.join(', ')}</span>
                </div>
                <div className="text-gray-400 mt-0.5">
                  Intensite: {conflict.intensity}/10 | Duree: {conflict.duration} ans
                  {conflict.nuclear_risk > 0 && (
                    <span className="text-yellow-400 ml-2">
                      Risque nucleaire: {conflict.nuclear_risk}%
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
