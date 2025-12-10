'use client';

import { useState, useEffect } from 'react';
import {
  InfluenceZone,
  ZONE_TYPE_NAMES,
  COUNTRY_FLAGS,
} from '@/lib/types';
import { getInfluenceZonesAdvanced } from '@/lib/api';
import StatBar from './StatBar';
import { InfluenceBreakdownMini } from './InfluenceBreakdownChart';

interface InfluencePanelProps {
  onZoneSelect?: (zone: InfluenceZone) => void;
}

type FilterType = 'all' | 'contested' | 'oil' | 'strategic';
type SortType = 'name' | 'strength' | 'contested';

// Skeleton loader for zones
function ZoneSkeleton() {
  return (
    <div className="px-4 py-3 border-b border-gray-700 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="h-4 bg-gray-700 rounded w-32" />
        <div className="h-4 bg-gray-700 rounded w-16" />
      </div>
      <div className="h-2 bg-gray-700 rounded w-full mb-2" />
      <div className="flex justify-between">
        <div className="h-3 bg-gray-700 rounded w-24" />
        <div className="h-3 bg-gray-700 rounded w-20" />
      </div>
    </div>
  );
}

export default function InfluencePanel({ onZoneSelect }: InfluencePanelProps) {
  const [zones, setZones] = useState<InfluenceZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [sort, setSort] = useState<SortType>('contested');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadZones();
  }, []);

  const loadZones = async () => {
    try {
      const data = await getInfluenceZonesAdvanced();
      setZones(data.zones);
    } catch (error) {
      console.error('Failed to load influence zones:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter zones
  const filteredZones = zones.filter((zone) => {
    // Search filter
    if (searchQuery && !zone.name_fr.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    // Type filter
    switch (filter) {
      case 'contested':
        return zone.contested_by.length > 0;
      case 'oil':
        return zone.has_oil;
      case 'strategic':
        return zone.has_strategic_resources;
      default:
        return true;
    }
  });

  // Sort zones
  const sortedZones = [...filteredZones].sort((a, b) => {
    switch (sort) {
      case 'name':
        return a.name_fr.localeCompare(b.name_fr);
      case 'strength':
        return b.strength - a.strength;
      case 'contested':
        return b.contested_by.length - a.contested_by.length;
      default:
        return 0;
    }
  });

  // Stats summary
  const contestedCount = zones.filter((z) => z.contested_by.length > 0).length;
  const oilZones = zones.filter((z) => z.has_oil).length;
  const strategicZones = zones.filter((z) => z.has_strategic_resources).length;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-900/50 to-gray-700 cursor-pointer hover:from-purple-900/70 transition-all"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
            <span className="text-sm">&#127760;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Zones d&apos;Influence</span>
            <div className="text-xs text-gray-400">
              {zones.length} zones | {contestedCount} contestees | {oilZones} petrole
            </div>
          </div>
        </div>
        <button className="text-gray-400 hover:text-white transition-transform duration-200" style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)' }}>
          &#9650;
        </button>
      </div>

      <div className={`transition-all duration-300 ease-in-out overflow-hidden ${expanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'}`}>
        {/* Search and Filters */}
        <div className="px-4 py-3 bg-gray-750 border-b border-gray-700 space-y-2">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Rechercher une zone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded-lg pl-8 pr-3 py-2 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <span className="absolute left-2.5 top-2.5 text-gray-500 text-sm">&#128269;</span>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-gray-500 hover:text-white text-sm"
              >
                &#10005;
              </button>
            )}
          </div>

          {/* Filter and Sort */}
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex gap-1">
              {([
                { key: 'all', label: 'Toutes', icon: '&#127758;' },
                { key: 'contested', label: `Contestees`, count: contestedCount, icon: '&#9876;' },
                { key: 'oil', label: `Petrole`, count: oilZones, icon: '&#9981;' },
                { key: 'strategic', label: 'Strategiques', count: strategicZones, icon: '&#9889;' },
              ] as const).map(({ key, label, count, icon }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`px-2.5 py-1.5 text-xs rounded-lg flex items-center gap-1 transition-all ${
                    filter === key
                      ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <span dangerouslySetInnerHTML={{ __html: icon }} />
                  {label}
                  {count !== undefined && <span className="opacity-70">({count})</span>}
                </button>
              ))}
            </div>
            <div className="flex gap-1 ml-auto items-center">
              <span className="text-xs text-gray-500 mr-1">Tri:</span>
              {([
                { key: 'contested', label: 'Tension' },
                { key: 'strength', label: 'Force' },
                { key: 'name', label: 'A-Z' },
              ] as const).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setSort(key)}
                  className={`px-2 py-1 text-xs rounded transition-all ${
                    sort === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Zone list */}
        <div className="max-h-[450px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
          {loading ? (
            <>
              <ZoneSkeleton />
              <ZoneSkeleton />
              <ZoneSkeleton />
              <ZoneSkeleton />
            </>
          ) : sortedZones.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <span className="text-3xl mb-2 block">&#128269;</span>
              Aucune zone trouvee
            </div>
          ) : (
            sortedZones.map((zone, index) => (
              <ZoneCard
                key={zone.id}
                zone={zone}
                onClick={() => onZoneSelect?.(zone)}
                index={index}
              />
            ))
          )}
        </div>

        {/* Footer stats */}
        {!loading && sortedZones.length > 0 && (
          <div className="px-4 py-2 bg-gray-750 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
            <span>Affichage: {sortedZones.length}/{zones.length} zones</span>
            <span>Cliquez sur une zone pour plus de details</span>
          </div>
        )}
      </div>
    </div>
  );
}

// Individual zone card
function ZoneCard({
  zone,
  onClick,
  index,
}: {
  zone: InfluenceZone;
  onClick: () => void;
  index: number;
}) {
  const dominantFlag = zone.dominant_power
    ? COUNTRY_FLAGS[zone.dominant_power] || zone.dominant_power
    : null;

  const isHighlyContested = zone.contested_by.length >= 2;
  const isContested = zone.contested_by.length > 0;

  // Determine status color
  const statusColor = isHighlyContested
    ? 'border-l-orange-500'
    : isContested
    ? 'border-l-yellow-500'
    : zone.dominant_power
    ? 'border-l-green-500'
    : 'border-l-gray-600';

  return (
    <div
      className={`px-4 py-3 border-b border-gray-700 border-l-4 ${statusColor} hover:bg-gray-700/50 cursor-pointer transition-all duration-200 group`}
      onClick={onClick}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      {/* Zone name and type */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold group-hover:text-purple-400 transition-colors">{zone.name_fr}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            zone.influence_type === 'hegemonic' ? 'bg-red-900/50 text-red-300' :
            zone.influence_type === 'economic' ? 'bg-green-900/50 text-green-300' :
            zone.influence_type === 'military' ? 'bg-gray-600 text-gray-200' :
            'bg-gray-700 text-gray-400'
          }`}>
            {ZONE_TYPE_NAMES[zone.influence_type] || zone.influence_type}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {zone.has_oil && (
            <span className="w-5 h-5 rounded bg-yellow-900/50 flex items-center justify-center text-xs" title="Petrole">
              &#9981;
            </span>
          )}
          {zone.has_strategic_resources && (
            <span className="w-5 h-5 rounded bg-blue-900/50 flex items-center justify-center text-xs" title="Ressources strategiques">
              &#9889;
            </span>
          )}
          <span className="text-gray-500 group-hover:text-white transition-colors">&#8250;</span>
        </div>
      </div>

      {/* Strength bar with value */}
      <div className="mb-2">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                zone.strength >= 70 ? 'bg-gradient-to-r from-green-600 to-green-400' :
                zone.strength >= 40 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                'bg-gradient-to-r from-red-600 to-red-400'
              }`}
              style={{ width: `${zone.strength}%` }}
            />
          </div>
          <span className="text-xs font-medium w-8 text-right">{zone.strength}</span>
        </div>
      </div>

      {/* Dominant power and contestation */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {dominantFlag ? (
            <div className="flex items-center gap-1.5 bg-gray-700/50 rounded-full px-2 py-0.5">
              <span className="text-base">{dominantFlag}</span>
              <span className="text-xs font-medium">{zone.dominant_power}</span>
            </div>
          ) : (
            <span className="text-gray-500 text-xs italic">Aucun dominant</span>
          )}
        </div>

        {isContested && (
          <div className="flex items-center gap-1">
            <span className={`text-xs px-1.5 py-0.5 rounded ${isHighlyContested ? 'bg-orange-900/50 text-orange-300' : 'bg-yellow-900/50 text-yellow-300'}`}>
              {isHighlyContested ? 'Forte tension' : 'Contestee'}
            </span>
            <div className="flex -space-x-1">
              {zone.contested_by.slice(0, 3).map((c) => (
                <span key={c} className="text-sm" title={c}>
                  {COUNTRY_FLAGS[c] || c}
                </span>
              ))}
            </div>
            {zone.contested_by.length > 3 && (
              <span className="text-xs text-gray-500">
                +{zone.contested_by.length - 3}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Influence breakdown mini - only show on hover effect area */}
      {zone.influence_breakdown && zone.dominant_power && (
        <div className="mt-2 pt-2 border-t border-gray-700/50">
          <InfluenceBreakdownMini
            breakdown={zone.influence_breakdown[zone.dominant_power] || {}}
          />
        </div>
      )}

      {/* Countries count */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <span>{zone.countries_in_zone.length} pays</span>
        {zone.former_colonial_power && (
          <span>Ex-colonie: {COUNTRY_FLAGS[zone.former_colonial_power] || zone.former_colonial_power}</span>
        )}
      </div>
    </div>
  );
}
