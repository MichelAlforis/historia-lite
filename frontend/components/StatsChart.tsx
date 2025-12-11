'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

interface HistoricalDataPoint {
  date: string;
  year: number;
  month: number;
  economy: number;
  military: number;
  technology: number;
  stability: number;
  soft_power: number;
  reputation?: number;
  global_tension?: number;
}

interface StatsChartProps {
  data: HistoricalDataPoint[];
  countryName: string;
  showReputation?: boolean;
  showTension?: boolean;
  compact?: boolean;
}

// Colors for each metric
const METRIC_COLORS = {
  economy: '#10b981',      // emerald
  military: '#ef4444',     // red
  technology: '#3b82f6',   // blue
  stability: '#f59e0b',    // amber
  soft_power: '#ec4899',   // pink
  reputation: '#8b5cf6',   // violet
  global_tension: '#dc2626', // red-600
};

const METRIC_NAMES_FR = {
  economy: 'Economie',
  military: 'Militaire',
  technology: 'Technologie',
  stability: 'Stabilite',
  soft_power: 'Soft Power',
  reputation: 'Reputation',
  global_tension: 'Tension Mondiale',
};

// Calculate trend from data
function calculateTrend(data: number[]): 'up' | 'down' | 'stable' {
  if (data.length < 2) return 'stable';
  const recent = data.slice(-3);
  const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const older = data.slice(0, 3);
  const oldAvg = older.reduce((a, b) => a + b, 0) / older.length;

  if (avg > oldAvg + 3) return 'up';
  if (avg < oldAvg - 3) return 'down';
  return 'stable';
}

function TrendIcon({ trend }: { trend: 'up' | 'down' | 'stable' }) {
  if (trend === 'up') return <TrendingUp className="w-4 h-4 text-emerald-500" />;
  if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Minus className="w-4 h-4 text-stone-400" />;
}

// Custom tooltip
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-stone-900/95 backdrop-blur-sm border border-stone-700 rounded-lg p-3 shadow-xl">
      <p className="text-stone-300 text-sm font-medium mb-2">{label}</p>
      <div className="space-y-1">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-stone-400">
              {METRIC_NAMES_FR[entry.dataKey as keyof typeof METRIC_NAMES_FR] || entry.dataKey}:
            </span>
            <span className="text-white font-medium">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function StatsChart({
  data,
  countryName,
  showReputation = false,
  showTension = false,
  compact = false
}: StatsChartProps) {
  // Compute trends for each metric
  const trends = useMemo(() => {
    if (data.length < 2) return {};
    return {
      economy: calculateTrend(data.map(d => d.economy)),
      military: calculateTrend(data.map(d => d.military)),
      technology: calculateTrend(data.map(d => d.technology)),
      stability: calculateTrend(data.map(d => d.stability)),
    };
  }, [data]);

  // Get latest values
  const latest = useMemo(() => {
    if (data.length === 0) return null;
    return data[data.length - 1];
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="bg-stone-800/50 rounded-xl p-4 border border-stone-700">
        <div className="flex items-center gap-2 text-stone-400">
          <Activity className="w-5 h-5" />
          <span>Pas de donnees historiques disponibles</span>
        </div>
      </div>
    );
  }

  if (compact) {
    // Mini sparkline version
    return (
      <div className="bg-stone-800/50 rounded-xl p-3 border border-stone-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-stone-300">Evolution</span>
          <span className="text-xs text-stone-500">{data.length} mois</span>
        </div>
        <div className="h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="gradientEconomy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={METRIC_COLORS.economy} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={METRIC_COLORS.economy} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="economy"
                stroke={METRIC_COLORS.economy}
                fill="url(#gradientEconomy)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-between mt-2">
          {(['economy', 'military', 'stability'] as const).map((key) => (
            <div key={key} className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: METRIC_COLORS[key] }}
              />
              <span className="text-xs text-stone-400">
                {latest?.[key] || 0}
              </span>
              <TrendIcon trend={trends[key] || 'stable'} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-stone-800/50 rounded-xl border border-stone-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-stone-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h3 className="font-medium text-stone-200">
            Evolution de {countryName}
          </h3>
        </div>
        <span className="text-xs text-stone-500">
          {data.length} mois de donnees
        </span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-2 p-3 border-b border-stone-700">
        {(['economy', 'military', 'technology', 'stability'] as const).map((key) => (
          <div key={key} className="bg-stone-900/50 rounded-lg p-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-stone-500">
                {METRIC_NAMES_FR[key]}
              </span>
              <TrendIcon trend={trends[key] || 'stable'} />
            </div>
            <div className="flex items-baseline gap-1">
              <span
                className="text-lg font-bold"
                style={{ color: METRIC_COLORS[key] }}
              >
                {latest?.[key] || 0}
              </span>
              <span className="text-xs text-stone-500">/100</span>
            </div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="p-4">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="#9ca3af"
                fontSize={11}
                tickLine={false}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="economy"
                name={METRIC_NAMES_FR.economy}
                stroke={METRIC_COLORS.economy}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="military"
                name={METRIC_NAMES_FR.military}
                stroke={METRIC_COLORS.military}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="technology"
                name={METRIC_NAMES_FR.technology}
                stroke={METRIC_COLORS.technology}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="stability"
                name={METRIC_NAMES_FR.stability}
                stroke={METRIC_COLORS.stability}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              {showReputation && (
                <Line
                  type="monotone"
                  dataKey="reputation"
                  name={METRIC_NAMES_FR.reputation}
                  stroke={METRIC_COLORS.reputation}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
              {showTension && (
                <Line
                  type="monotone"
                  dataKey="global_tension"
                  name={METRIC_NAMES_FR.global_tension}
                  stroke={METRIC_COLORS.global_tension}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// Export types
export type { HistoricalDataPoint };
