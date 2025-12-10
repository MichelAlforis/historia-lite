'use client';

import { InfluenceBreakdown, INFLUENCE_TYPE_HEX, INFLUENCE_TYPE_NAMES } from '@/lib/types';

interface InfluenceBreakdownChartProps {
  breakdown: InfluenceBreakdown | Record<string, number>;
  showLegend?: boolean;
  height?: number;
  showValues?: boolean;
}

const INFLUENCE_TYPES = [
  'military',
  'economic',
  'monetary',
  'cultural',
  'religious',
  'petro',
  'colonial',
  'diplomatic',
] as const;

export default function InfluenceBreakdownChart({
  breakdown,
  showLegend = true,
  height = 24,
  showValues = false,
}: InfluenceBreakdownChartProps) {
  const total = INFLUENCE_TYPES.reduce((sum, type) => sum + (breakdown[type] || 0), 0);

  if (total === 0) {
    return (
      <div
        className="w-full bg-gray-700 rounded"
        style={{ height }}
      >
        <div className="h-full flex items-center justify-center text-gray-500 text-xs">
          Aucune influence
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Stacked bar */}
      <div
        className="w-full flex rounded overflow-hidden"
        style={{ height }}
      >
        {INFLUENCE_TYPES.map((type) => {
          const value = breakdown[type] || 0;
          if (value === 0) return null;
          const percentage = (value / total) * 100;

          return (
            <div
              key={type}
              className="relative group"
              style={{
                width: `${percentage}%`,
                backgroundColor: INFLUENCE_TYPE_HEX[type],
                minWidth: value > 0 ? '4px' : 0,
              }}
            >
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                  {INFLUENCE_TYPE_NAMES[type]}: {value}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Values display */}
      {showValues && (
        <div className="flex justify-between mt-1 text-xs text-gray-400">
          <span>Total: {total}</span>
          <span>
            {INFLUENCE_TYPES.filter((t) => breakdown[t] > 0).length} facteurs
          </span>
        </div>
      )}

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
          {INFLUENCE_TYPES.map((type) => {
            const value = breakdown[type] || 0;
            if (value === 0) return null;

            return (
              <div key={type} className="flex items-center gap-1 text-xs">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: INFLUENCE_TYPE_HEX[type] }}
                />
                <span className="text-gray-300">
                  {INFLUENCE_TYPE_NAMES[type]}
                </span>
                <span className="text-gray-500">{value}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Mini version for compact displays
export function InfluenceBreakdownMini({
  breakdown,
}: {
  breakdown: InfluenceBreakdown | Record<string, number>;
}) {
  const total = INFLUENCE_TYPES.reduce((sum, type) => sum + (breakdown[type] || 0), 0);

  if (total === 0) {
    return <div className="w-full h-2 bg-gray-700 rounded" />;
  }

  return (
    <div className="w-full h-2 flex rounded overflow-hidden">
      {INFLUENCE_TYPES.map((type) => {
        const value = breakdown[type] || 0;
        if (value === 0) return null;
        const percentage = (value / total) * 100;

        return (
          <div
            key={type}
            style={{
              width: `${percentage}%`,
              backgroundColor: INFLUENCE_TYPE_HEX[type],
              minWidth: value > 0 ? '2px' : 0,
            }}
          />
        );
      })}
    </div>
  );
}
