'use client';

import { useState, useEffect } from 'react';
import {
  InfluenceZone,
  MilitaryBase,
  ZONE_TYPE_NAMES,
  RELIGION_NAMES,
  CULTURE_NAMES,
  LANGUAGE_NAMES,
  COUNTRY_FLAGS,
  BASE_TYPE_NAMES,
} from '@/lib/types';
import { getZoneBreakdown } from '@/lib/api';
import InfluenceBreakdownChart from './InfluenceBreakdownChart';

interface ZoneDetailModalProps {
  zone: InfluenceZone;
  onClose: () => void;
}

interface ZoneBreakdownData {
  zone_id: string;
  zone_name_fr: string;
  dominant_power: string | null;
  contested_by: string[];
  strength: number;
  influence_breakdown: Record<string, Record<string, number>>;
  total_by_power: Record<string, number>;
  cultural_factors: {
    dominant_religion: string | null;
    dominant_culture: string | null;
    dominant_language: string | null;
  };
  resources: {
    has_oil: boolean;
    has_strategic_resources: boolean;
  };
  military_bases: MilitaryBase[];
}

// Skeleton loader
function ContentSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-24 bg-gray-700 rounded-lg" />
      <div className="h-32 bg-gray-700 rounded-lg" />
      <div className="h-48 bg-gray-700 rounded-lg" />
    </div>
  );
}

export default function ZoneDetailModal({ zone, onClose }: ZoneDetailModalProps) {
  const [breakdownData, setBreakdownData] = useState<ZoneBreakdownData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'influence' | 'bases' | 'countries'>('influence');
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    loadBreakdown();
    // Handle escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [zone.id]);

  const loadBreakdown = async () => {
    try {
      const data = await getZoneBreakdown(zone.id);
      setBreakdownData(data);
    } catch (error) {
      console.error('Failed to load zone breakdown:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(onClose, 200);
  };

  // Sort powers by total influence
  const sortedPowers = breakdownData
    ? Object.entries(breakdownData.total_by_power)
        .sort(([, a], [, b]) => b - a)
        .filter(([, total]) => total > 0)
    : [];

  const isContested = zone.contested_by.length > 0;
  const isHighlyContested = zone.contested_by.length >= 2;

  return (
    <div
      className={`fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-opacity duration-200 ${isClosing ? 'opacity-0' : 'opacity-100'}`}
      onClick={handleClose}
    >
      <div
        className={`bg-gray-800 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl border border-gray-700 transition-all duration-200 ${isClosing ? 'scale-95 opacity-0' : 'scale-100 opacity-100'}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900/50 to-gray-700 px-6 py-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-bold">{zone.name_fr}</h2>
                {isHighlyContested && (
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/30 animate-pulse">
                    Haute tension
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`text-sm px-3 py-1 rounded-full ${
                  zone.influence_type === 'hegemonic' ? 'bg-red-900/50 text-red-300 border border-red-700' :
                  zone.influence_type === 'economic' ? 'bg-green-900/50 text-green-300 border border-green-700' :
                  zone.influence_type === 'military' ? 'bg-gray-600 text-gray-200 border border-gray-500' :
                  'bg-gray-700 text-gray-300 border border-gray-600'
                }`}>
                  {ZONE_TYPE_NAMES[zone.influence_type] || zone.influence_type}
                </span>
                {zone.has_oil && (
                  <span className="text-sm px-3 py-1 rounded-full bg-yellow-900/30 text-yellow-300 border border-yellow-700/50 flex items-center gap-1">
                    <span>&#9981;</span> Petrole
                  </span>
                )}
                {zone.has_strategic_resources && (
                  <span className="text-sm px-3 py-1 rounded-full bg-blue-900/30 text-blue-300 border border-blue-700/50 flex items-center gap-1">
                    <span>&#9889;</span> Strategique
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={handleClose}
              className="w-10 h-10 rounded-full bg-gray-700/50 hover:bg-gray-600 flex items-center justify-center text-gray-400 hover:text-white transition-all"
            >
              &#10005;
            </button>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-4 gap-3 mt-4">
            <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-center">
              <div className="text-2xl font-bold">{zone.strength}</div>
              <div className="text-xs text-gray-400">Force</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-center">
              <div className="text-2xl font-bold">{zone.countries_in_zone.length}</div>
              <div className="text-xs text-gray-400">Pays</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-center">
              <div className="text-2xl font-bold">{breakdownData?.military_bases.length || 0}</div>
              <div className="text-xs text-gray-400">Bases</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-center">
              <div className="text-2xl font-bold">{sortedPowers.length}</div>
              <div className="text-xs text-gray-400">Puissances</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700 bg-gray-750">
          {([
            { key: 'influence', label: 'Influence', icon: '&#127760;', count: undefined as number | undefined },
            { key: 'bases', label: `Bases`, count: breakdownData?.military_bases.length || 0, icon: '&#127981;' },
            { key: 'countries', label: `Pays`, count: zone.countries_in_zone.length, icon: '&#127988;' },
          ] as const).map(({ key, label, count, icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                activeTab === key
                  ? 'bg-gray-700 text-white border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              <span dangerouslySetInnerHTML={{ __html: icon }} />
              {label}
              {count !== undefined && (
                <span className={`px-1.5 py-0.5 text-xs rounded-full ${activeTab === key ? 'bg-purple-600' : 'bg-gray-600'}`}>
                  {count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[55vh] scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
          {loading ? (
            <ContentSkeleton />
          ) : (
            <div className="transition-all duration-200">
              {activeTab === 'influence' && (
                <InfluenceTab
                  zone={zone}
                  breakdownData={breakdownData}
                  sortedPowers={sortedPowers}
                />
              )}
              {activeTab === 'bases' && (
                <BasesTab bases={breakdownData?.military_bases || []} />
              )}
              {activeTab === 'countries' && (
                <CountriesTab countries={zone.countries_in_zone} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Influence Tab
function InfluenceTab({
  zone,
  breakdownData,
  sortedPowers,
}: {
  zone: InfluenceZone;
  breakdownData: ZoneBreakdownData | null;
  sortedPowers: [string, number][];
}) {
  const maxInfluence = sortedPowers.length > 0 ? sortedPowers[0][1] : 100;

  return (
    <div className="space-y-5">
      {/* Cultural factors */}
      <div className="bg-gradient-to-br from-gray-750 to-gray-800 rounded-xl p-4 border border-gray-700">
        <h3 className="font-semibold mb-4 text-gray-200 flex items-center gap-2">
          <span>&#127983;</span> Facteurs Culturels
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-gray-500 text-xs uppercase tracking-wider">Religion</span>
            <div className="font-medium mt-1 flex items-center gap-2">
              {zone.dominant_religion ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-orange-500" />
                  {RELIGION_NAMES[zone.dominant_religion] || zone.dominant_religion}
                </>
              ) : (
                <span className="text-gray-500 italic">Aucune dominante</span>
              )}
            </div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-gray-500 text-xs uppercase tracking-wider">Culture</span>
            <div className="font-medium mt-1 flex items-center gap-2">
              {zone.dominant_culture ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-purple-500" />
                  {CULTURE_NAMES[zone.dominant_culture] || zone.dominant_culture}
                </>
              ) : (
                <span className="text-gray-500 italic">Aucune dominante</span>
              )}
            </div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-gray-500 text-xs uppercase tracking-wider">Langue</span>
            <div className="font-medium mt-1 flex items-center gap-2">
              {zone.dominant_language ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  {LANGUAGE_NAMES[zone.dominant_language] || zone.dominant_language}
                </>
              ) : (
                <span className="text-gray-500 italic">Aucune dominante</span>
              )}
            </div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-gray-500 text-xs uppercase tracking-wider">Ex-Colonisateur</span>
            <div className="font-medium mt-1">
              {zone.former_colonial_power ? (
                <span className="flex items-center gap-2">
                  <span className="text-lg">{COUNTRY_FLAGS[zone.former_colonial_power] || ''}</span>
                  {zone.former_colonial_power}
                </span>
              ) : (
                <span className="text-gray-500 italic">Aucun</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Dominant and Contestation */}
      <div className="bg-gradient-to-br from-gray-750 to-gray-800 rounded-xl p-4 border border-gray-700">
        <h3 className="font-semibold mb-4 text-gray-200 flex items-center gap-2">
          <span>&#9876;</span> Controle de la Zone
        </h3>
        <div className="flex items-center gap-4">
          <div className="flex-1 bg-gray-800/50 rounded-lg p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Puissance Dominante</div>
            {zone.dominant_power ? (
              <div className="flex items-center gap-3">
                <span className="text-3xl">{COUNTRY_FLAGS[zone.dominant_power] || ''}</span>
                <div>
                  <div className="font-bold text-lg">{zone.dominant_power}</div>
                  <div className="text-xs text-green-400">Controle actif</div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 italic">Zone non dominee</div>
            )}
          </div>

          {zone.contested_by.length > 0 && (
            <div className="flex-1 bg-orange-900/20 rounded-lg p-4 border border-orange-700/30">
              <div className="text-xs text-orange-400 uppercase tracking-wider mb-2">Contestants ({zone.contested_by.length})</div>
              <div className="flex flex-wrap gap-2">
                {zone.contested_by.map((c) => (
                  <div key={c} className="flex items-center gap-1 bg-gray-800 rounded-full px-2 py-1">
                    <span className="text-lg">{COUNTRY_FLAGS[c] || ''}</span>
                    <span className="text-sm">{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Influence by power */}
      <div className="bg-gradient-to-br from-gray-750 to-gray-800 rounded-xl p-4 border border-gray-700">
        <h3 className="font-semibold mb-4 text-gray-200 flex items-center gap-2">
          <span>&#128202;</span> Influence par Puissance
        </h3>
        <div className="space-y-3">
          {sortedPowers.map(([powerId, total], index) => (
            <div
              key={powerId}
              className={`rounded-lg p-3 transition-all ${
                powerId === zone.dominant_power
                  ? 'bg-green-900/20 border border-green-700/30'
                  : zone.contested_by.includes(powerId)
                  ? 'bg-orange-900/10 border border-orange-700/20'
                  : 'bg-gray-800/50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-medium text-gray-500">#{index + 1}</span>
                  <span className="text-2xl">{COUNTRY_FLAGS[powerId] || ''}</span>
                  <span className="font-semibold">{powerId}</span>
                  {powerId === zone.dominant_power && (
                    <span className="text-xs px-2 py-0.5 bg-green-600 rounded-full font-medium">Dominant</span>
                  )}
                  {zone.contested_by.includes(powerId) && (
                    <span className="text-xs px-2 py-0.5 bg-orange-600 rounded-full font-medium">Contestant</span>
                  )}
                </div>
                <div className="text-right">
                  <span className="font-bold text-xl">{total}</span>
                  <span className="text-xs text-gray-500 ml-1">pts</span>
                </div>
              </div>

              {/* Power bar */}
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    powerId === zone.dominant_power
                      ? 'bg-gradient-to-r from-green-600 to-green-400'
                      : zone.contested_by.includes(powerId)
                      ? 'bg-gradient-to-r from-orange-600 to-orange-400'
                      : 'bg-gradient-to-r from-blue-600 to-blue-400'
                  }`}
                  style={{ width: `${(total / maxInfluence) * 100}%` }}
                />
              </div>

              {breakdownData?.influence_breakdown[powerId] && (
                <InfluenceBreakdownChart
                  breakdown={breakdownData.influence_breakdown[powerId]}
                  showLegend={index === 0}
                  height={16}
                />
              )}
            </div>
          ))}
          {sortedPowers.length === 0 && (
            <div className="text-gray-500 text-center py-8">
              <span className="text-3xl mb-2 block">&#128683;</span>
              Aucune puissance n&apos;a d&apos;influence significative dans cette zone
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Bases Tab
function BasesTab({ bases }: { bases: MilitaryBase[] }) {
  // Group by owner
  const basesByOwner = bases.reduce((acc, base) => {
    if (!acc[base.owner]) acc[base.owner] = [];
    acc[base.owner].push(base);
    return acc;
  }, {} as Record<string, MilitaryBase[]>);

  // Sort owners by number of bases
  const sortedOwners = Object.entries(basesByOwner).sort(([, a], [, b]) => b.length - a.length);

  // Calculate total personnel
  const totalPersonnel = bases.reduce((sum, b) => sum + b.personnel, 0);

  return (
    <div className="space-y-4">
      {/* Summary */}
      {bases.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-gray-750 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-400">{bases.length}</div>
            <div className="text-xs text-gray-400">Bases</div>
          </div>
          <div className="bg-gray-750 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-400">{sortedOwners.length}</div>
            <div className="text-xs text-gray-400">Puissances</div>
          </div>
          <div className="bg-gray-750 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">{totalPersonnel.toLocaleString()}</div>
            <div className="text-xs text-gray-400">Personnel</div>
          </div>
        </div>
      )}

      {sortedOwners.map(([owner, ownerBases]) => {
        const ownerPersonnel = ownerBases.reduce((sum, b) => sum + b.personnel, 0);
        return (
          <div key={owner} className="bg-gradient-to-br from-gray-750 to-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{COUNTRY_FLAGS[owner] || ''}</span>
                <div>
                  <span className="font-semibold">{owner}</span>
                  <div className="text-xs text-gray-400">
                    {ownerBases.length} base{ownerBases.length > 1 ? 's' : ''} | {ownerPersonnel.toLocaleString()} personnel
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-red-400">{Math.round((ownerPersonnel / totalPersonnel) * 100)}%</div>
                <div className="text-xs text-gray-500">presence</div>
              </div>
            </div>
            <div className="space-y-2">
              {ownerBases.map((base) => (
                <div
                  key={base.id}
                  className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2 hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded flex items-center justify-center text-sm ${
                      base.type === 'naval_base' ? 'bg-blue-900/50 text-blue-300' :
                      base.type === 'air_base' ? 'bg-sky-900/50 text-sky-300' :
                      base.type === 'army_base' ? 'bg-green-900/50 text-green-300' :
                      'bg-gray-700 text-gray-300'
                    }`}>
                      {base.type === 'naval_base' ? '&#9875;' :
                       base.type === 'air_base' ? '&#9992;' :
                       base.type === 'army_base' ? '&#127981;' : '&#128737;'}
                    </div>
                    <div>
                      <div className="font-medium text-sm">{base.name}</div>
                      <div className="text-xs text-gray-400 flex items-center gap-1">
                        <span className="text-base">{COUNTRY_FLAGS[base.host_country] || ''}</span>
                        {base.host_country}
                        <span className="mx-1">|</span>
                        {BASE_TYPE_NAMES[base.type] || base.type}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{base.personnel.toLocaleString()}</div>
                    <div className="text-xs text-gray-500">personnel</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {bases.length === 0 && (
        <div className="text-gray-500 text-center py-12">
          <span className="text-4xl mb-3 block">&#127981;</span>
          <div className="text-lg mb-1">Aucune base militaire</div>
          <div className="text-sm">Cette zone n&apos;a pas de presence militaire etrangere</div>
        </div>
      )}
    </div>
  );
}

// Countries Tab
function CountriesTab({ countries }: { countries: string[] }) {
  return (
    <div>
      {countries.length > 0 && (
        <div className="mb-4 text-sm text-gray-400">
          {countries.length} pays composent cette zone d&apos;influence
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {countries.map((country, index) => (
          <div
            key={country}
            className="bg-gradient-to-br from-gray-750 to-gray-800 rounded-lg px-3 py-2.5 flex items-center gap-2 border border-gray-700 hover:border-gray-600 transition-all cursor-default"
            style={{ animationDelay: `${index * 20}ms` }}
          >
            <span className="text-xl">{COUNTRY_FLAGS[country] || '&#127988;'}</span>
            <span className="font-medium text-sm">{country}</span>
          </div>
        ))}
      </div>
      {countries.length === 0 && (
        <div className="text-gray-500 text-center py-12">
          <span className="text-4xl mb-3 block">&#127988;</span>
          <div className="text-lg">Aucun pays dans cette zone</div>
        </div>
      )}
    </div>
  );
}
