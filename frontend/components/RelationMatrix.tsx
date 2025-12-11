'use client';

import { useMemo, useState } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { COUNTRY_FLAGS, Country } from '@/lib/types';
import {
  X,
  Grid3X3,
  Swords,
  Shield,
  Target,
  Filter,
} from 'lucide-react';

interface RelationMatrixProps {
  isOpen: boolean;
  onClose: () => void;
  onCountrySelect?: (countryId: string) => void;
}

// Get color for relation value
function getRelationColor(value: number): string {
  if (value >= 70) return 'bg-emerald-500';
  if (value >= 40) return 'bg-emerald-300';
  if (value >= 20) return 'bg-emerald-100';
  if (value >= -20) return 'bg-stone-200';
  if (value >= -50) return 'bg-red-200';
  if (value >= -70) return 'bg-red-400';
  return 'bg-red-600';
}

// Get text color for relation value
function getRelationTextColor(value: number): string {
  if (value >= 70) return 'text-white';
  if (value >= 40) return 'text-emerald-900';
  if (value >= 20) return 'text-emerald-800';
  if (value >= -20) return 'text-stone-600';
  if (value >= -50) return 'text-red-800';
  if (value >= -70) return 'text-white';
  return 'text-white';
}

// Cell component for matrix
function MatrixCell({
  value,
  isAlly,
  isRival,
  isAtWar,
  isSelf,
  fromCountry,
  toCountry,
  onClick,
}: {
  value: number;
  isAlly: boolean;
  isRival: boolean;
  isAtWar: boolean;
  isSelf: boolean;
  fromCountry: string;
  toCountry: string;
  onClick?: () => void;
}) {
  if (isSelf) {
    return (
      <div className="w-10 h-10 bg-stone-800 flex items-center justify-center">
        <span className="text-stone-500 text-xs">-</span>
      </div>
    );
  }

  const bgColor = getRelationColor(value);
  const textColor = getRelationTextColor(value);

  return (
    <div
      className={`w-10 h-10 ${bgColor} flex items-center justify-center cursor-pointer
        hover:ring-2 hover:ring-indigo-500 hover:z-10 relative group transition-all`}
      onClick={onClick}
      title={`${fromCountry} -> ${toCountry}: ${value}`}
    >
      {isAtWar ? (
        <Swords className="w-4 h-4 text-white" />
      ) : isAlly ? (
        <Shield className="w-3 h-3 text-emerald-900" />
      ) : isRival ? (
        <Target className="w-3 h-3 text-red-900" />
      ) : (
        <span className={`text-xs font-medium ${textColor}`}>
          {value > 0 ? '+' : ''}{value}
        </span>
      )}

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1
        bg-stone-900 text-white text-xs rounded opacity-0 group-hover:opacity-100
        transition-opacity pointer-events-none whitespace-nowrap z-50">
        {fromCountry} {'->'} {toCountry}: {value}
        {isAtWar && ' (Guerre)'}
        {isAlly && ' (Allie)'}
        {isRival && ' (Rival)'}
      </div>
    </div>
  );
}

export default function RelationMatrix({ isOpen, onClose, onCountrySelect }: RelationMatrixProps) {
  const { world } = useGameStore();
  const [tierFilter, setTierFilter] = useState<number | null>(null);

  // Get Tier 1-3 countries and build matrix data
  const { countries, matrix } = useMemo(() => {
    if (!world) {
      return { countries: [], matrix: {} };
    }

    // Filter to Tier 1-3 only
    let filtered = world.countries.filter(c => c.tier && c.tier <= 3);

    // Apply tier filter if set
    if (tierFilter !== null) {
      filtered = filtered.filter(c => c.tier === tierFilter);
    }

    // Sort by tier then by name
    filtered.sort((a, b) => {
      if (a.tier !== b.tier) return (a.tier || 99) - (b.tier || 99);
      return (a.name_fr || a.name).localeCompare(b.name_fr || b.name);
    });

    // Build matrix lookup
    const matrixData: Record<string, Record<string, {
      value: number;
      isAlly: boolean;
      isRival: boolean;
      isAtWar: boolean;
    }>> = {};

    filtered.forEach(country => {
      matrixData[country.id] = {};
      filtered.forEach(other => {
        if (country.id === other.id) {
          matrixData[country.id][other.id] = {
            value: 0,
            isAlly: false,
            isRival: false,
            isAtWar: false,
          };
        } else {
          const relationValue = country.relations?.[other.id] ?? 0;
          matrixData[country.id][other.id] = {
            value: relationValue,
            isAlly: country.allies?.includes(other.id) || false,
            isRival: country.rivals?.includes(other.id) || false,
            isAtWar: country.at_war?.includes(other.id) || false,
          };
        }
      });
    });

    return { countries: filtered, matrix: matrixData };
  }, [world, tierFilter]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-stone-900/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed inset-4 z-50 bg-white shadow-2xl rounded-2xl
        overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-100 bg-gradient-to-r from-violet-500 to-purple-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-white">
              <Grid3X3 className="w-6 h-6" />
              <div>
                <h2 className="text-lg font-semibold">Matrice des Relations</h2>
                <p className="text-violet-100 text-sm">
                  {countries.length} pays - Cliquez sur une cellule pour voir les details
                </p>
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

        {/* Filter bar */}
        <div className="px-6 py-3 bg-stone-50 border-b border-stone-100 flex items-center gap-4">
          <div className="flex items-center gap-2 text-stone-600">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">Filtrer par tier:</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setTierFilter(null)}
              className={`px-3 py-1 rounded-lg text-sm transition ${
                tierFilter === null
                  ? 'bg-violet-500 text-white'
                  : 'bg-stone-200 text-stone-600 hover:bg-stone-300'
              }`}
            >
              Tous
            </button>
            {[1, 2, 3].map(tier => (
              <button
                key={tier}
                onClick={() => setTierFilter(tier)}
                className={`px-3 py-1 rounded-lg text-sm transition ${
                  tierFilter === tier
                    ? 'bg-violet-500 text-white'
                    : 'bg-stone-200 text-stone-600 hover:bg-stone-300'
                }`}
              >
                Tier {tier}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="ml-auto flex items-center gap-4 text-xs text-stone-500">
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 bg-emerald-500 rounded" />
              <span>Allie</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 bg-red-500 rounded" />
              <span>Hostile</span>
            </div>
            <div className="flex items-center gap-1">
              <Swords className="w-4 h-4" />
              <span>Guerre</span>
            </div>
            <div className="flex items-center gap-1">
              <Shield className="w-4 h-4" />
              <span>Allie</span>
            </div>
            <div className="flex items-center gap-1">
              <Target className="w-4 h-4" />
              <span>Rival</span>
            </div>
          </div>
        </div>

        {/* Matrix container */}
        <div className="flex-1 overflow-auto p-4">
          {countries.length === 0 ? (
            <div className="text-center py-12">
              <Grid3X3 className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-stone-500">Aucun pays disponible</p>
            </div>
          ) : (
            <div className="inline-block">
              {/* Header row with country names */}
              <div className="flex">
                {/* Empty corner cell */}
                <div className="w-24 h-10 flex-shrink-0" />
                {/* Column headers */}
                {countries.map(country => (
                  <div
                    key={`col-${country.id}`}
                    className="w-10 h-10 flex items-center justify-center text-lg"
                    title={country.name_fr || country.name}
                  >
                    {COUNTRY_FLAGS[country.id] || country.id.slice(0, 2)}
                  </div>
                ))}
              </div>

              {/* Data rows */}
              {countries.map(rowCountry => (
                <div key={`row-${rowCountry.id}`} className="flex">
                  {/* Row header */}
                  <div
                    className="w-24 h-10 flex-shrink-0 flex items-center gap-2 pr-2
                      text-sm font-medium text-stone-700 cursor-pointer hover:bg-stone-100 rounded-l"
                    onClick={() => onCountrySelect?.(rowCountry.id)}
                    title={rowCountry.name_fr || rowCountry.name}
                  >
                    <span className="text-lg">{COUNTRY_FLAGS[rowCountry.id] || ''}</span>
                    <span className="truncate text-xs">
                      {(rowCountry.name_fr || rowCountry.name).slice(0, 8)}
                    </span>
                  </div>

                  {/* Matrix cells */}
                  {countries.map(colCountry => {
                    const cellData = matrix[rowCountry.id]?.[colCountry.id];
                    if (!cellData) return null;

                    return (
                      <MatrixCell
                        key={`${rowCountry.id}-${colCountry.id}`}
                        value={cellData.value}
                        isAlly={cellData.isAlly}
                        isRival={cellData.isRival}
                        isAtWar={cellData.isAtWar}
                        isSelf={rowCountry.id === colCountry.id}
                        fromCountry={rowCountry.name_fr || rowCountry.name}
                        toCountry={colCountry.name_fr || colCountry.name}
                        onClick={() => onCountrySelect?.(rowCountry.id)}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-stone-100 bg-stone-50">
          <div className="flex items-center justify-between">
            <p className="text-xs text-stone-500">
              Ligne = pays observateur, Colonne = pays cible.
              Valeurs de -100 (hostile) a +100 (allie).
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 text-stone-600 hover:text-stone-800 text-sm transition"
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
