'use client';

import { useState, useEffect } from 'react';
import {
  Country,
  TIER_NAMES,
  REGIME_NAMES,
  COUNTRY_FLAGS,
  PowerGlobalInfluence,
  MilitaryBase,
  Leader,
} from '@/lib/types';
import { StatBar } from './StatBar';
import { getPowerGlobalInfluence, getBasesByOwner, getLeader, getCombinedStatsHistory, HistoricalDataPoint } from '@/lib/api';
import { InfluenceBreakdownMini } from './InfluenceBreakdownChart';
import { PowerScoreCard } from './PowerScoreCard';
import LeaderCard from './LeaderCard';
import StatsChart from './StatsChart';

interface CountryPanelProps {
  country: Country;
  allCountries: Country[];
  onClose: () => void;
}

export function CountryPanel({ country, allCountries, onClose }: CountryPanelProps) {
  const [influenceData, setInfluenceData] = useState<PowerGlobalInfluence | null>(null);
  const [basesData, setBasesData] = useState<{ bases: MilitaryBase[]; total_personnel: number } | null>(null);
  const [loadingInfluence, setLoadingInfluence] = useState(true);
  const [leader, setLeader] = useState<Leader | null>(null);
  const [statsHistory, setStatsHistory] = useState<HistoricalDataPoint[]>([]);

  useEffect(() => {
    // Only load influence data for major powers (tier 1-2)
    if (country.tier <= 2) {
      loadInfluenceData();
    } else {
      setLoadingInfluence(false);
    }
    // Load leader data for all countries
    loadLeaderData();
    // Load stats history
    loadStatsHistory();
  }, [country.id]);

  const loadStatsHistory = async () => {
    try {
      const history = await getCombinedStatsHistory(country.id, 24);
      setStatsHistory(history);
    } catch (error) {
      console.error('Failed to load stats history:', error);
      setStatsHistory([]);
    }
  };

  const loadLeaderData = async () => {
    try {
      const leaderData = await getLeader(country.id);
      setLeader(leaderData);
    } catch (error) {
      console.error('Failed to load leader data:', error);
      setLeader(null);
    }
  };

  const loadInfluenceData = async () => {
    try {
      const [influence, bases] = await Promise.all([
        getPowerGlobalInfluence(country.id),
        getBasesByOwner(country.id),
      ]);
      setInfluenceData(influence);
      setBasesData({ bases: bases.bases, total_personnel: bases.total_personnel });
    } catch (error) {
      console.error('Failed to load influence data:', error);
    } finally {
      setLoadingInfluence(false);
    }
  };

  const getCountryName = (id: string) => {
    const c = allCountries.find(c => c.id === id);
    return c?.name_fr || id;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold">{country.name_fr}</h2>
          <p className="text-gray-400">
            {TIER_NAMES[country.tier]} | {REGIME_NAMES[country.regime] || country.regime}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-2xl"
        >
          X
        </button>
      </div>

      {/* Leader */}
      {leader && (
        <div className="mb-6">
          <LeaderCard
            leader={leader}
            countryId={country.id}
            countryName={country.name_fr}
          />
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="space-y-2">
          <h3 className="font-bold text-gray-300 mb-2">Statistiques</h3>
          <StatBar label="Population" value={country.population} color="bg-purple-500" />
          <StatBar label="Economie" value={country.economy} color="bg-green-500" />
          <StatBar label="Militaire" value={country.military} color="bg-red-500" />
          <StatBar label="Nucleaire" value={country.nuclear} color="bg-yellow-500" />
        </div>
        <div className="space-y-2">
          <h3 className="font-bold text-gray-300 mb-2">Capacites</h3>
          <StatBar label="Technologie" value={country.technology} color="bg-blue-500" />
          <StatBar label="Stabilite" value={country.stability} color="auto" />
          <StatBar label="Soft Power" value={country.soft_power} color="bg-pink-500" />
          <StatBar label="Ressources" value={country.resources} color="bg-amber-500" />
        </div>
      </div>

      {/* Power Scores - New Scoring System */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-300 mb-2">Scores de Puissance</h3>
        <PowerScoreCard countryId={country.id} />
      </div>

      {/* Stats History Chart */}
      {statsHistory.length > 0 && (
        <div className="mb-6">
          <StatsChart
            data={statsHistory}
            countryName={country.name_fr}
            showReputation={country.is_player}
            showTension={country.is_player}
          />
        </div>
      )}

      {/* Personality */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-300 mb-2">Personnalite IA</h3>
        <div className="grid grid-cols-2 gap-2">
          <StatBar label="Agressivite" value={country.personality.aggression} color="bg-red-400" />
          <StatBar label="Expansionnisme" value={country.personality.expansionism} color="bg-orange-400" />
          <StatBar label="Diplomatie" value={country.personality.diplomacy} color="bg-blue-400" />
          <StatBar label="Prise de risque" value={country.personality.risk_tolerance} color="bg-purple-400" />
        </div>
      </div>

      {/* Blocs */}
      {country.blocs.length > 0 && (
        <div className="mb-4">
          <h3 className="font-bold text-gray-300 mb-2">Blocs et alliances</h3>
          <div className="flex flex-wrap gap-2">
            {country.blocs.map(bloc => (
              <span key={bloc} className="px-3 py-1 bg-blue-600 rounded-full text-sm">
                {bloc}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Allies */}
      {country.allies.length > 0 && (
        <div className="mb-4">
          <h3 className="font-bold text-gray-300 mb-2">Allies</h3>
          <div className="flex flex-wrap gap-2">
            {country.allies.map(id => (
              <span key={id} className="px-3 py-1 bg-green-600 rounded-full text-sm">
                {getCountryName(id)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Rivals */}
      {country.rivals.length > 0 && (
        <div className="mb-4">
          <h3 className="font-bold text-gray-300 mb-2">Rivaux</h3>
          <div className="flex flex-wrap gap-2">
            {country.rivals.map(id => (
              <span key={id} className="px-3 py-1 bg-red-600 rounded-full text-sm">
                {getCountryName(id)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* At War */}
      {country.at_war.length > 0 && (
        <div className="mb-4">
          <h3 className="font-bold text-red-400 mb-2">En guerre avec</h3>
          <div className="flex flex-wrap gap-2">
            {country.at_war.map(id => (
              <span key={id} className="px-3 py-1 bg-red-800 rounded-full text-sm">
                {getCountryName(id)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sanctions */}
      {country.sanctions_on.length > 0 && (
        <div className="mb-4">
          <h3 className="font-bold text-orange-400 mb-2">Sanctions imposees a</h3>
          <div className="flex flex-wrap gap-2">
            {country.sanctions_on.map(id => (
              <span key={id} className="px-3 py-1 bg-orange-700 rounded-full text-sm">
                {getCountryName(id)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Global Influence - Only for major powers */}
      {country.tier <= 2 && !loadingInfluence && influenceData && (
        <div className="mb-6">
          <h3 className="font-bold text-purple-400 mb-3">Influence Mondiale</h3>
          <div className="bg-gray-700 rounded-lg p-4">
            {/* Summary stats */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {influenceData.total_influence}
                </div>
                <div className="text-xs text-gray-400">Influence totale</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {influenceData.zones_dominated}
                </div>
                <div className="text-xs text-gray-400">Zones dominees</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400">
                  {influenceData.zones_contested}
                </div>
                <div className="text-xs text-gray-400">Zones contestees</div>
              </div>
            </div>

            {/* Global influence breakdown */}
            {influenceData.global_breakdown && (
              <div className="mb-4">
                <div className="text-xs text-gray-400 mb-1">Repartition de l&apos;influence:</div>
                <InfluenceBreakdownMini breakdown={influenceData.global_breakdown} />
              </div>
            )}

            {/* Top zones */}
            {influenceData.top_zones && influenceData.top_zones.length > 0 && (
              <div>
                <div className="text-xs text-gray-400 mb-2">Principales zones d&apos;influence:</div>
                <div className="space-y-1">
                  {influenceData.top_zones.slice(0, 5).map(zone => (
                    <div
                      key={zone.zone_id}
                      className="flex items-center justify-between bg-gray-800 rounded px-2 py-1"
                    >
                      <span className="text-sm">{zone.zone_name_fr}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-purple-400">
                          {zone.influence}
                        </span>
                        {zone.is_dominant && (
                          <span className="text-xs px-1.5 py-0.5 bg-green-600 rounded">
                            Dominant
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Military Bases Abroad - Only for major powers */}
      {country.tier <= 2 && basesData && basesData.bases.length > 0 && (
        <div className="mb-6">
          <h3 className="font-bold text-red-400 mb-3">
            Bases Militaires ({basesData.bases.length} | {basesData.total_personnel.toLocaleString()} personnel)
          </h3>
          <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
            {basesData.bases.map(base => (
              <div
                key={base.id}
                className="bg-gray-700 rounded px-2 py-1.5"
              >
                <div className="text-sm font-medium truncate">{base.name}</div>
                <div className="text-xs text-gray-400 flex justify-between">
                  <span>{COUNTRY_FLAGS[base.host_country] || ''} {base.host_country}</span>
                  <span>{base.personnel.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relations */}
      <div>
        <h3 className="font-bold text-gray-300 mb-2">Relations diplomatiques</h3>
        <div className="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto">
          {Object.entries(country.relations)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15)
            .map(([id, value]) => (
              <div
                key={id}
                className={`px-2 py-1 rounded text-xs flex justify-between ${
                  value > 20 ? 'bg-green-800' :
                  value < -20 ? 'bg-red-800' :
                  'bg-gray-700'
                }`}
              >
                <span className="truncate">{getCountryName(id)}</span>
                <span className="font-bold ml-1">{value > 0 ? '+' : ''}{value}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
