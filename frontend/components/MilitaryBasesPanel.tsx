'use client';

import { useState, useEffect } from 'react';
import { MilitaryBase, COUNTRY_FLAGS, BASE_TYPE_NAMES } from '@/lib/types';
import { getMilitaryBases } from '@/lib/api';

type GroupBy = 'owner' | 'zone' | 'type';

// Skeleton loader for bases
function BaseSkeleton() {
  return (
    <div className="px-4 py-3 border-b border-gray-700 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="h-4 bg-gray-700 rounded w-40 mb-2" />
          <div className="h-3 bg-gray-700 rounded w-32" />
        </div>
        <div className="text-right">
          <div className="h-4 bg-gray-700 rounded w-16 mb-2" />
          <div className="h-2 bg-gray-700 rounded w-20" />
        </div>
      </div>
    </div>
  );
}

// Type icons mapping
const TYPE_ICONS: Record<string, string> = {
  air_base: '&#9992;',
  naval_base: '&#9875;',
  army_base: '&#9881;',
  joint_base: '&#9733;',
  logistics: '&#128230;',
  intelligence: '&#128065;',
};

export default function MilitaryBasesPanel() {
  const [bases, setBases] = useState<MilitaryBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [groupBy, setGroupBy] = useState<GroupBy>('owner');
  const [filterOwner, setFilterOwner] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadBases();
  }, []);

  const loadBases = async () => {
    try {
      const data = await getMilitaryBases();
      setBases(data.bases);
    } catch (error) {
      console.error('Failed to load military bases:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique owners
  const owners = [...new Set(bases.map((b) => b.owner))].sort();

  // Filter bases
  const filteredBases = bases.filter((base) => {
    // Owner filter
    if (filterOwner !== 'all' && base.owner !== filterOwner) {
      return false;
    }
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        base.name.toLowerCase().includes(query) ||
        base.host_country.toLowerCase().includes(query) ||
        base.zone.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Group bases
  const groupedBases = filteredBases.reduce((acc, base) => {
    let key: string;
    switch (groupBy) {
      case 'owner':
        key = base.owner;
        break;
      case 'zone':
        key = base.zone;
        break;
      case 'type':
        key = base.type;
        break;
    }
    if (!acc[key]) acc[key] = [];
    acc[key].push(base);
    return acc;
  }, {} as Record<string, MilitaryBase[]>);

  // Calculate stats
  const totalPersonnel = filteredBases.reduce((sum, b) => sum + b.personnel, 0);
  const totalBases = bases.length;
  const avgStrategicValue = filteredBases.length > 0
    ? Math.round(filteredBases.reduce((sum, b) => sum + b.strategic_value, 0) / filteredBases.length)
    : 0;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-red-900/50 to-gray-700 cursor-pointer hover:from-red-900/70 transition-all"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center">
            <span className="text-sm">&#9876;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Bases Militaires</span>
            <div className="text-xs text-gray-400">
              {totalBases} bases | {totalPersonnel.toLocaleString()} personnel
            </div>
          </div>
        </div>
        <button
          className="text-gray-400 hover:text-white transition-transform duration-200"
          style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
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
              placeholder="Rechercher une base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded-lg pl-8 pr-3 py-2 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500"
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

          {/* Filter and Group */}
          <div className="flex flex-wrap gap-2 items-center">
            {/* Owner filter */}
            <select
              value={filterOwner}
              onChange={(e) => setFilterOwner(e.target.value)}
              className="bg-gray-700 text-white text-sm rounded-lg px-3 py-1.5 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="all">&#127758; Tous ({totalBases})</option>
              {owners.map((owner) => {
                const count = bases.filter(b => b.owner === owner).length;
                return (
                  <option key={owner} value={owner}>
                    {COUNTRY_FLAGS[owner] || ''} {owner} ({count})
                  </option>
                );
              })}
            </select>

            {/* Group by */}
            <div className="flex gap-1 ml-auto items-center">
              <span className="text-xs text-gray-500 mr-1">Grouper:</span>
              {([
                { key: 'owner', label: 'Pays', icon: '&#127463;' },
                { key: 'zone', label: 'Zone', icon: '&#127758;' },
                { key: 'type', label: 'Type', icon: '&#9881;' },
              ] as const).map(({ key, label, icon }) => (
                <button
                  key={key}
                  onClick={() => setGroupBy(key)}
                  className={`px-2.5 py-1.5 text-xs rounded-lg flex items-center gap-1 transition-all ${
                    groupBy === key
                      ? 'bg-red-600 text-white shadow-lg shadow-red-600/30'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <span dangerouslySetInnerHTML={{ __html: icon }} />
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Bases list */}
        <div className="max-h-[400px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
          {loading ? (
            <>
              <BaseSkeleton />
              <BaseSkeleton />
              <BaseSkeleton />
              <BaseSkeleton />
            </>
          ) : filteredBases.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <span className="text-3xl mb-2 block">&#128269;</span>
              Aucune base trouvee
            </div>
          ) : (
            Object.entries(groupedBases)
              .sort(([, a], [, b]) => b.length - a.length)
              .map(([group, groupBases], groupIndex) => (
                <div
                  key={group}
                  className="border-b border-gray-700 last:border-0"
                  style={{ animationDelay: `${groupIndex * 50}ms` }}
                >
                  {/* Group header */}
                  <div className="px-4 py-2.5 bg-gradient-to-r from-gray-750 to-gray-800 flex items-center justify-between sticky top-0 z-10">
                    <div className="flex items-center gap-2">
                      {groupBy === 'owner' && (
                        <>
                          <span className="text-lg">{COUNTRY_FLAGS[group] || ''}</span>
                          <span className="font-semibold">{group}</span>
                        </>
                      )}
                      {groupBy === 'zone' && (
                        <>
                          <span className="w-6 h-6 rounded bg-purple-900/50 flex items-center justify-center text-xs">&#127758;</span>
                          <span className="font-semibold">{group}</span>
                        </>
                      )}
                      {groupBy === 'type' && (
                        <>
                          <span
                            className="w-6 h-6 rounded bg-blue-900/50 flex items-center justify-center text-xs"
                            dangerouslySetInnerHTML={{ __html: TYPE_ICONS[group] || '&#9881;' }}
                          />
                          <span className="font-semibold">
                            {BASE_TYPE_NAMES[group] || group}
                          </span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs px-2 py-0.5 bg-gray-700 rounded-full">
                        {groupBases.length} bases
                      </span>
                      <span className="text-sm text-gray-400">
                        {groupBases.reduce((sum, b) => sum + b.personnel, 0).toLocaleString()} pers.
                      </span>
                    </div>
                  </div>

                  {/* Bases in group */}
                  <div className="divide-y divide-gray-700/50">
                    {groupBases
                      .sort((a, b) => b.personnel - a.personnel)
                      .map((base, index) => (
                        <BaseRow
                          key={base.id}
                          base={base}
                          groupBy={groupBy}
                          index={index}
                        />
                      ))}
                  </div>
                </div>
              ))
          )}
        </div>

        {/* Footer stats */}
        {!loading && filteredBases.length > 0 && (
          <div className="px-4 py-2 bg-gray-750 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
            <span>Affichage: {filteredBases.length}/{totalBases} bases</span>
            <span>Valeur strategique moyenne: {avgStrategicValue}/100</span>
          </div>
        )}
      </div>
    </div>
  );
}

function BaseRow({
  base,
  groupBy,
  index,
}: {
  base: MilitaryBase;
  groupBy: GroupBy;
  index: number;
}) {
  // Strategic value color
  const getStrategicColor = (value: number) => {
    if (value >= 80) return 'from-green-600 to-green-400';
    if (value >= 60) return 'from-yellow-600 to-yellow-400';
    if (value >= 40) return 'from-orange-600 to-orange-400';
    return 'from-red-600 to-red-400';
  };

  return (
    <div
      className="px-4 py-2.5 hover:bg-gray-700/50 transition-all duration-200 group cursor-default"
      style={{ animationDelay: `${index * 30}ms` }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span
              className="w-5 h-5 rounded bg-gray-700 flex items-center justify-center text-xs group-hover:bg-gray-600 transition-colors"
              dangerouslySetInnerHTML={{ __html: TYPE_ICONS[base.type] || '&#9881;' }}
              title={BASE_TYPE_NAMES[base.type] || base.type}
            />
            <span className="font-medium text-sm group-hover:text-red-400 transition-colors">
              {base.name}
            </span>
          </div>
          <div className="text-xs text-gray-400 flex items-center gap-2 mt-1 ml-7">
            {groupBy !== 'owner' && (
              <span className="flex items-center gap-1">
                <span>{COUNTRY_FLAGS[base.owner] || ''}</span>
                <span>{base.owner}</span>
              </span>
            )}
            {groupBy !== 'type' && (
              <span className="px-1.5 py-0.5 bg-gray-700 rounded text-xs">
                {BASE_TYPE_NAMES[base.type] || base.type}
              </span>
            )}
            {groupBy !== 'zone' && (
              <span className="text-gray-500">{base.zone}</span>
            )}
            <span className="flex items-center gap-1">
              <span>@</span>
              <span>{COUNTRY_FLAGS[base.host_country] || ''}</span>
              <span>{base.host_country}</span>
            </span>
          </div>
        </div>
        <div className="text-right ml-4">
          <div className="font-semibold text-sm">
            {base.personnel.toLocaleString()}
            <span className="text-xs text-gray-500 font-normal ml-1">pers.</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${getStrategicColor(base.strategic_value)} transition-all duration-500`}
                style={{ width: `${base.strategic_value}%` }}
              />
            </div>
            <span className="text-xs text-gray-400 w-6">{base.strategic_value}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
