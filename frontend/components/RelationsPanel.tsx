'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { COUNTRY_FLAGS, Country } from '@/lib/types';
import {
  X,
  Users,
  Handshake,
  Swords,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  Target,
} from 'lucide-react';

interface RelationsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// Relation level categories
function getRelationLevel(value: number): {
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
} {
  if (value >= 70) return {
    label: 'Allie',
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-50 border-emerald-200',
    icon: <Handshake className="w-4 h-4 text-emerald-500" />,
  };
  if (value >= 40) return {
    label: 'Amical',
    color: 'text-sky-700',
    bgColor: 'bg-sky-50 border-sky-200',
    icon: <TrendingUp className="w-4 h-4 text-sky-500" />,
  };
  if (value >= -20) return {
    label: 'Neutre',
    color: 'text-stone-600',
    bgColor: 'bg-stone-50 border-stone-200',
    icon: <Minus className="w-4 h-4 text-stone-400" />,
  };
  if (value >= -50) return {
    label: 'Tendu',
    color: 'text-amber-700',
    bgColor: 'bg-amber-50 border-amber-200',
    icon: <TrendingDown className="w-4 h-4 text-amber-500" />,
  };
  return {
    label: 'Hostile',
    color: 'text-red-700',
    bgColor: 'bg-red-50 border-red-200',
    icon: <AlertTriangle className="w-4 h-4 text-red-500" />,
  };
}

// Relation bar component
function RelationBar({ value }: { value: number }) {
  const normalized = Math.max(-100, Math.min(100, value));
  const isPositive = normalized >= 0;
  const width = Math.abs(normalized);

  return (
    <div className="flex items-center gap-2 w-32">
      <div className="flex-1 h-2 bg-stone-200 rounded-full relative overflow-hidden">
        {isPositive ? (
          <div
            className="absolute left-1/2 h-full bg-emerald-400 rounded-r-full"
            style={{ width: `${width / 2}%` }}
          />
        ) : (
          <div
            className="absolute right-1/2 h-full bg-red-400 rounded-l-full"
            style={{ width: `${width / 2}%` }}
          />
        )}
        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-stone-400" />
      </div>
      <span className={`text-xs font-medium w-8 text-right ${
        isPositive ? 'text-emerald-600' : 'text-red-600'
      }`}>
        {normalized > 0 ? '+' : ''}{normalized}
      </span>
    </div>
  );
}

// Country card in relations list
function CountryRelationCard({
  country,
  relation,
  isAlly,
  isRival,
  isAtWar,
}: {
  country: Country;
  relation: number;
  isAlly: boolean;
  isRival: boolean;
  isAtWar: boolean;
}) {
  const level = getRelationLevel(relation);

  return (
    <div className={`rounded-xl border p-3 ${level.bgColor} transition hover:shadow-sm`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{COUNTRY_FLAGS[country.id] || ''}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-stone-800">
                {country.name_fr || country.name}
              </span>
              {isAtWar && (
                <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full flex items-center gap-1">
                  <Swords className="w-3 h-3" />
                  Guerre
                </span>
              )}
              {isAlly && !isAtWar && (
                <span className="px-1.5 py-0.5 bg-emerald-500 text-white text-xs rounded-full flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  Allie
                </span>
              )}
              {isRival && !isAtWar && (
                <span className="px-1.5 py-0.5 bg-amber-500 text-white text-xs rounded-full flex items-center gap-1">
                  <Target className="w-3 h-3" />
                  Rival
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              {level.icon}
              <span className={`text-xs ${level.color}`}>{level.label}</span>
            </div>
          </div>
        </div>
        <RelationBar value={relation} />
      </div>
    </div>
  );
}

export default function RelationsPanel({ isOpen, onClose }: RelationsPanelProps) {
  const { world, playerCountryId } = useGameStore();

  // Get player country and sort relations
  const { playerCountry, sortedRelations, stats } = useMemo(() => {
    if (!world || !playerCountryId) {
      return { playerCountry: null, sortedRelations: [], stats: null };
    }

    const player = world.countries.find(c => c.id === playerCountryId);
    if (!player) {
      return { playerCountry: null, sortedRelations: [], stats: null };
    }

    // Build relations list with country data
    const relationsWithCountry = Object.entries(player.relations || {})
      .map(([countryId, relationValue]) => {
        const country = world.countries.find(c => c.id === countryId);
        if (!country) return null;
        return {
          country,
          relation: relationValue,
          isAlly: player.allies?.includes(countryId) || false,
          isRival: player.rivals?.includes(countryId) || false,
          isAtWar: player.at_war?.includes(countryId) || false,
        };
      })
      .filter((r): r is NonNullable<typeof r> => r !== null)
      .sort((a, b) => b.relation - a.relation);

    // Calculate stats
    const allies = relationsWithCountry.filter(r => r.isAlly).length;
    const rivals = relationsWithCountry.filter(r => r.isRival).length;
    const wars = relationsWithCountry.filter(r => r.isAtWar).length;
    const friendly = relationsWithCountry.filter(r => r.relation >= 40 && !r.isAlly).length;
    const hostile = relationsWithCountry.filter(r => r.relation <= -50 && !r.isAtWar).length;

    return {
      playerCountry: player,
      sortedRelations: relationsWithCountry,
      stats: { allies, rivals, wars, friendly, hostile },
    };
  }, [world, playerCountryId]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-stone-900/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-lg bg-white shadow-2xl
        transform transition-transform duration-300 ease-out overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-100 bg-gradient-to-r from-indigo-500 to-purple-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-white">
              <Users className="w-6 h-6" />
              <div>
                <h2 className="text-lg font-semibold">Relations Diplomatiques</h2>
                {playerCountry && (
                  <p className="text-indigo-100 text-sm flex items-center gap-2">
                    <span className="text-lg">{COUNTRY_FLAGS[playerCountryId!]}</span>
                    {playerCountry.name_fr}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-xl transition text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stats summary */}
        {stats && (
          <div className="px-6 py-4 bg-stone-50 border-b border-stone-100">
            <div className="grid grid-cols-5 gap-2">
              <StatBadge icon={<Swords className="w-4 h-4" />} value={stats.wars} label="Guerres" color="red" />
              <StatBadge icon={<Shield className="w-4 h-4" />} value={stats.allies} label="Allies" color="emerald" />
              <StatBadge icon={<Target className="w-4 h-4" />} value={stats.rivals} label="Rivaux" color="amber" />
              <StatBadge icon={<TrendingUp className="w-4 h-4" />} value={stats.friendly} label="Amicaux" color="sky" />
              <StatBadge icon={<AlertTriangle className="w-4 h-4" />} value={stats.hostile} label="Hostiles" color="rose" />
            </div>
          </div>
        )}

        {/* Relations list */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {!playerCountry ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-stone-500">Selectionnez un pays pour voir ses relations</p>
            </div>
          ) : sortedRelations.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-stone-500">Aucune relation diplomatique</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Wars first */}
              {sortedRelations.filter(r => r.isAtWar).length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-red-600 uppercase tracking-wide mb-2 px-1">
                    En guerre
                  </h3>
                  <div className="space-y-2">
                    {sortedRelations
                      .filter(r => r.isAtWar)
                      .map(r => (
                        <CountryRelationCard key={r.country.id} {...r} />
                      ))}
                  </div>
                </div>
              )}

              {/* Allies */}
              {sortedRelations.filter(r => r.isAlly && !r.isAtWar).length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-2 px-1">
                    Allies
                  </h3>
                  <div className="space-y-2">
                    {sortedRelations
                      .filter(r => r.isAlly && !r.isAtWar)
                      .map(r => (
                        <CountryRelationCard key={r.country.id} {...r} />
                      ))}
                  </div>
                </div>
              )}

              {/* Rivals */}
              {sortedRelations.filter(r => r.isRival && !r.isAtWar).length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-2 px-1">
                    Rivaux
                  </h3>
                  <div className="space-y-2">
                    {sortedRelations
                      .filter(r => r.isRival && !r.isAtWar)
                      .map(r => (
                        <CountryRelationCard key={r.country.id} {...r} />
                      ))}
                  </div>
                </div>
              )}

              {/* Others */}
              {sortedRelations.filter(r => !r.isAlly && !r.isRival && !r.isAtWar).length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-2 px-1">
                    Autres nations
                  </h3>
                  <div className="space-y-2">
                    {sortedRelations
                      .filter(r => !r.isAlly && !r.isRival && !r.isAtWar)
                      .map(r => (
                        <CountryRelationCard key={r.country.id} {...r} />
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-stone-100 bg-stone-50">
          <button
            onClick={onClose}
            className="w-full py-2 text-stone-600 hover:text-stone-800 text-sm transition"
          >
            Fermer
          </button>
        </div>
      </div>
    </>
  );
}

// Stat badge component
function StatBadge({
  icon,
  value,
  label,
  color,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    red: 'bg-red-100 text-red-700',
    emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    sky: 'bg-sky-100 text-sky-700',
    rose: 'bg-rose-100 text-rose-700',
  };

  return (
    <div className={`flex flex-col items-center p-2 rounded-lg ${colorClasses[color]}`}>
      {icon}
      <span className="text-lg font-bold mt-0.5">{value}</span>
      <span className="text-xs">{label}</span>
    </div>
  );
}
