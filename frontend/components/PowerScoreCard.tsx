'use client';

import { useState, useEffect } from 'react';
import { getCountryScores } from '@/lib/api';
import { SCORING_CATEGORY_COLORS, SCORING_CATEGORY_NAMES } from '@/lib/types';

interface CategoryScoreData {
  category: string;
  score: number;
  confidence: string;
  breakdown: Record<string, number>;
}

interface CountryScoresData {
  country_id: string;
  global_score: number;
  world_rank: number;
  intel_quality: string;
  military: CategoryScoreData;
  economic: CategoryScoreData;
  stability: CategoryScoreData;
  influence: CategoryScoreData;
  intelligence: CategoryScoreData;
  resources: CategoryScoreData;
  leadership: CategoryScoreData;
  nuclear_info?: {
    status: string;
    display: string;
    display_fr: string;
    warheads: number | null;
    confidence: string;
  };
}

interface PowerScoreCardProps {
  countryId: string;
  observerId?: string;
}

const INTEL_QUALITY_LABELS: Record<string, { label: string; color: string }> = {
  perfect: { label: 'Parfait', color: 'bg-green-600' },
  excellent: { label: 'Excellent', color: 'bg-green-500' },
  very_good: { label: 'Tres bon', color: 'bg-lime-500' },
  good: { label: 'Bon', color: 'bg-yellow-500' },
  partial: { label: 'Partiel', color: 'bg-orange-500' },
  none: { label: 'Aucun', color: 'bg-red-600' },
};

const CONFIDENCE_STYLES: Record<string, { bar: string; text: string }> = {
  exact: { bar: '', text: '' },
  estimate: { bar: 'opacity-70', text: 'text-yellow-400' },
  unknown: { bar: 'bg-gray-600', text: 'text-gray-500' },
};

export function PowerScoreCard({ countryId, observerId }: PowerScoreCardProps) {
  const [scores, setScores] = useState<CountryScoresData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  useEffect(() => {
    loadScores();
  }, [countryId, observerId]);

  const loadScores = async () => {
    try {
      setLoading(true);
      const data = await getCountryScores(countryId, observerId);
      setScores(data as unknown as CountryScoresData);
    } catch (error) {
      console.error('Failed to load scores:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!scores) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-gray-400">
        Impossible de charger les scores
      </div>
    );
  }

  const categories = [
    { key: 'military', data: scores.military },
    { key: 'economic', data: scores.economic },
    { key: 'stability', data: scores.stability },
    { key: 'influence', data: scores.influence },
    { key: 'intelligence', data: scores.intelligence },
    { key: 'resources', data: scores.resources },
    { key: 'leadership', data: scores.leadership },
  ];

  const intelQuality = INTEL_QUALITY_LABELS[scores.intel_quality] || INTEL_QUALITY_LABELS.none;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Header with global score and intel quality */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-2xl font-bold text-amber-400">
            {scores.global_score}
          </div>
          <div className="text-xs text-gray-400">
            Score global (#{scores.world_rank})
          </div>
        </div>

        {/* Intel quality badge */}
        {observerId && observerId !== countryId && (
          <div className={`px-2 py-1 rounded text-xs ${intelQuality.color}`}>
            Intel: {intelQuality.label}
          </div>
        )}
      </div>

      {/* Category scores */}
      <div className="space-y-3">
        {categories.map(({ key, data }) => (
          <CategoryBar
            key={key}
            category={key}
            score={data.score}
            confidence={data.confidence}
            breakdown={data.breakdown}
            isExpanded={expandedCategory === key}
            onToggle={() => setExpandedCategory(expandedCategory === key ? null : key)}
          />
        ))}
      </div>

      {/* Nuclear info */}
      {scores.nuclear_info && (
        <div className="mt-4 pt-3 border-t border-gray-700">
          <NuclearInfo info={scores.nuclear_info} />
        </div>
      )}
    </div>
  );
}

interface CategoryBarProps {
  category: string;
  score: number;
  confidence: string;
  breakdown: Record<string, number>;
  isExpanded: boolean;
  onToggle: () => void;
}

function CategoryBar({ category, score, confidence, breakdown, isExpanded, onToggle }: CategoryBarProps) {
  const colorClass = SCORING_CATEGORY_COLORS[category] || 'bg-gray-500';
  const name = SCORING_CATEGORY_NAMES[category] || category;
  const styles = CONFIDENCE_STYLES[confidence] || CONFIDENCE_STYLES.exact;

  const isUnknown = confidence === 'unknown';
  const isEstimate = confidence === 'estimate';

  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between text-sm mb-1 hover:bg-gray-700/50 rounded px-1 -mx-1"
        disabled={isUnknown}
      >
        <span className={`flex items-center gap-2 ${styles.text}`}>
          {name}
          {isEstimate && <span className="text-xs text-yellow-500">~</span>}
          {isUnknown && <span className="text-xs">{'[Classifie]'}</span>}
        </span>
        <span className={`font-medium ${styles.text}`}>
          {isUnknown ? '?' : score}
        </span>
      </button>

      {/* Progress bar */}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        {isUnknown ? (
          <div className="h-full bg-gray-600 flex items-center justify-center">
            <div className="w-full h-full bg-gradient-to-r from-gray-600 via-gray-500 to-gray-600 animate-pulse"></div>
          </div>
        ) : (
          <div className="relative h-full">
            {/* Main bar */}
            <div
              className={`h-full ${colorClass} ${styles.bar} transition-all duration-300`}
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
            />
            {/* Uncertainty range for estimates */}
            {isEstimate && (
              <>
                <div
                  className={`absolute top-0 h-full ${colorClass} opacity-30`}
                  style={{
                    left: `${Math.max(0, score - 15)}%`,
                    width: `${Math.min(30, 100 - score + 15)}%`
                  }}
                />
              </>
            )}
          </div>
        )}
      </div>

      {/* Expanded breakdown */}
      {isExpanded && !isUnknown && Object.keys(breakdown).length > 0 && (
        <div className="mt-2 pl-4 border-l-2 border-gray-600 space-y-1">
          {Object.entries(breakdown).map(([key, value]) => (
            <div key={key} className="flex justify-between text-xs text-gray-400">
              <span>{formatBreakdownKey(key)}</span>
              <span className={value >= 0 ? 'text-green-400' : 'text-red-400'}>
                {value >= 0 ? '+' : ''}{value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface NuclearInfoProps {
  info: {
    status: string;
    display: string;
    display_fr: string;
    warheads: number | null;
    confidence: string;
  };
}

function NuclearInfo({ info }: NuclearInfoProps) {
  const statusColors: Record<string, string> = {
    unknown: 'text-gray-500 bg-gray-700',
    none: 'text-gray-400 bg-gray-700',
    confirmed: 'text-yellow-400 bg-yellow-900/30',
  };

  const colorClass = statusColors[info.status] || statusColors.unknown;

  return (
    <div className={`flex items-center justify-between px-3 py-2 rounded ${colorClass}`}>
      <div className="flex items-center gap-2">
        <span className="text-lg">{'[N]'}</span>
        <span className="text-sm">{info.display_fr}</span>
      </div>
      {info.confidence === 'estimate' && (
        <span className="text-xs text-yellow-500">~</span>
      )}
      {info.confidence === 'unknown' && (
        <span className="text-xs text-gray-500">{'[?]'}</span>
      )}
    </div>
  );
}

function formatBreakdownKey(key: string): string {
  const labels: Record<string, string> = {
    base_military: 'Force de base',
    base_economy: 'Economie de base',
    base_stability: 'Stabilite de base',
    base_resources: 'Ressources de base',
    nuclear_bonus: 'Bonus nucleaire',
    tech_bonus: 'Bonus techno',
    stability_bonus: 'Bonus stabilite',
    economy_factor: 'Facteur eco',
    soft_power: 'Soft power',
    sphere_size: 'Sphere influence',
    allies_count: 'Nombre allies',
    tech_base: 'Base techno',
    soft_power_base: 'Base soft power',
    tier_bonus: 'Bonus tier',
    regime_base: 'Base regime',
    stability_factor: 'Facteur stabilite',
  };
  return labels[key] || key.replace(/_/g, ' ');
}
