'use client';

import { useState, useEffect } from 'react';
import { Tier4Country, Tier4Summary, REGION_NAMES, ALIGNMENT_NAMES, ALIGNMENT_COLORS } from '@/lib/types';
import * as api from '@/lib/api';

interface Tier4ListProps {
  onSelectCountry?: (country: Tier4Country) => void;
}

export function Tier4List({ onSelectCountry }: Tier4ListProps) {
  const [countries, setCountries] = useState<Tier4Country[]>([]);
  const [summary, setSummary] = useState<Tier4Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [alignmentFilter, setAlignmentFilter] = useState<string>('all');
  const [showCrisisOnly, setShowCrisisOnly] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadCountries();
  }, [regionFilter, alignmentFilter, showCrisisOnly]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [countriesData, summaryData] = await Promise.all([
        api.getTier4Countries(),
        api.getTier4Summary()
      ]);
      setCountries(countriesData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Error loading Tier 4 data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCountries = async () => {
    try {
      const params: { region?: string; alignment?: string; in_crisis?: boolean } = {};
      if (regionFilter !== 'all') params.region = regionFilter;
      if (alignmentFilter !== 'all') params.alignment = alignmentFilter;
      if (showCrisisOnly) params.in_crisis = true;

      const data = await api.getTier4Countries(params);
      setCountries(data);
    } catch (error) {
      console.error('Error loading filtered countries:', error);
    }
  };

  const getAlignmentBar = (alignment: number) => {
    // -100 to +100, center at 50%
    const position = ((alignment + 100) / 200) * 100;
    return (
      <div className="relative w-full h-2 bg-gradient-to-r from-blue-500 via-gray-400 to-red-500 rounded">
        <div
          className="absolute w-2 h-4 bg-white border border-gray-800 rounded -top-1"
          style={{ left: `calc(${position}% - 4px)` }}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-2">Etats Secondaires (Tier 4)</h3>
        <div className="text-center text-gray-400 py-4">Chargement...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Header with toggle */}
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="text-lg font-semibold">
          Etats Secondaires (Tier 4)
          <span className="text-sm font-normal text-gray-400 ml-2">
            {summary?.total || 0} pays
          </span>
        </h3>
        <button className="text-gray-400 hover:text-white">
          {expanded ? '[-]' : '[+]'}
        </button>
      </div>

      {/* Summary stats (always visible) */}
      {summary && (
        <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
          <div className="bg-blue-900/30 rounded p-2 text-center">
            <div className="text-blue-400 font-semibold">{summary.pro_west}</div>
            <div className="text-gray-400 text-xs">Pro-Occident</div>
          </div>
          <div className="bg-gray-700/30 rounded p-2 text-center">
            <div className="text-gray-300 font-semibold">{summary.neutral}</div>
            <div className="text-gray-400 text-xs">Neutres</div>
          </div>
          <div className="bg-red-900/30 rounded p-2 text-center">
            <div className="text-red-400 font-semibold">{summary.pro_east}</div>
            <div className="text-gray-400 text-xs">Pro-Est</div>
          </div>
        </div>
      )}

      {/* Crisis indicator */}
      {summary && summary.in_crisis > 0 && (
        <div className="mt-2 text-sm text-orange-400">
          {summary.in_crisis} pays en crise
        </div>
      )}

      {/* Expanded content */}
      {expanded && (
        <div className="mt-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-2 mb-4">
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="bg-gray-700 text-sm rounded px-2 py-1"
            >
              <option value="all">Toutes regions</option>
              {Object.entries(REGION_NAMES).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>

            <select
              value={alignmentFilter}
              onChange={(e) => setAlignmentFilter(e.target.value)}
              className="bg-gray-700 text-sm rounded px-2 py-1"
            >
              <option value="all">Tous alignements</option>
              {Object.entries(ALIGNMENT_NAMES).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>

            <label className="flex items-center text-sm text-gray-400">
              <input
                type="checkbox"
                checked={showCrisisOnly}
                onChange={(e) => setShowCrisisOnly(e.target.checked)}
                className="mr-1"
              />
              En crise
            </label>
          </div>

          {/* Countries list */}
          <div className="max-h-96 overflow-y-auto space-y-1">
            {countries.length === 0 ? (
              <div className="text-gray-400 text-sm text-center py-4">
                Aucun pays ne correspond aux filtres
              </div>
            ) : (
              countries.map((country) => (
                <div
                  key={country.id}
                  className={`p-2 rounded cursor-pointer transition-colors ${
                    country.in_crisis
                      ? 'bg-orange-900/30 hover:bg-orange-900/50'
                      : 'bg-gray-700/50 hover:bg-gray-700'
                  }`}
                  onClick={() => onSelectCountry?.(country)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{country.name_fr}</span>
                        <span className="text-xs text-gray-500">{country.id}</span>
                        {country.in_crisis && (
                          <span className="text-xs bg-orange-600 px-1 rounded">
                            {country.crisis_type?.replace('_', ' ')}
                          </span>
                        )}
                        {country.strategic_resource && (
                          <span className="text-xs bg-yellow-700 px-1 rounded">
                            {country.strategic_resource}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {REGION_NAMES[country.region] || country.region}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xs px-2 py-0.5 rounded ${ALIGNMENT_COLORS[country.alignment_label] || 'bg-gray-500'}`}>
                        {ALIGNMENT_NAMES[country.alignment_label] || country.alignment_label}
                      </div>
                    </div>
                  </div>

                  {/* Stats bar */}
                  <div className="mt-2 grid grid-cols-4 gap-1 text-xs">
                    <div>
                      <span className="text-gray-500">Eco:</span>
                      <span className="ml-1">{country.economy}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Stab:</span>
                      <span className={`ml-1 ${country.stability < 30 ? 'text-red-400' : ''}`}>
                        {country.stability}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Mil:</span>
                      <span className="ml-1">{country.military}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Pop:</span>
                      <span className="ml-1">{country.population}</span>
                    </div>
                  </div>

                  {/* Alignment bar */}
                  <div className="mt-2">
                    {getAlignmentBar(country.alignment)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
