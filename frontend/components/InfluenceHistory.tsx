'use client';

import { useState, useEffect, useMemo } from 'react';
import { COUNTRY_FLAGS, InfluenceZone, PowerGlobalInfluence } from '@/lib/types';
import { getInfluenceRankings, getPowerGlobalInfluence } from '@/lib/api';

interface InfluenceHistoryProps {
  currentYear: number;
  zones: InfluenceZone[];
}

interface HistoryPoint {
  year: number;
  data: Record<string, number>;
  events?: Record<string, string>; // Key events that affected influence
}

// Extended list of powers for comprehensive ranking
const ALL_POWERS = [
  'USA', 'CHN', 'RUS', 'FRA', 'GBR', 'IND', 'DEU', 'JPN', 'BRA', 'TUR',
  'SAU', 'IRN', 'ISR', 'AUS', 'KOR', 'ITA', 'PAK', 'EGY', 'IDN', 'ZAF'
];

const MAJOR_POWERS = ['USA', 'CHN', 'RUS', 'FRA', 'GBR', 'IND', 'DEU', 'JPN', 'TUR', 'BRA'];

const POWER_NAMES: Record<string, string> = {
  USA: 'Etats-Unis',
  CHN: 'Chine',
  RUS: 'Russie',
  FRA: 'France',
  GBR: 'Royaume-Uni',
  IND: 'Inde',
  DEU: 'Allemagne',
  JPN: 'Japon',
  BRA: 'Bresil',
  TUR: 'Turquie',
  SAU: 'Arabie Saoudite',
  IRN: 'Iran',
  ISR: 'Israel',
  AUS: 'Australie',
  KOR: 'Coree du Sud',
  ITA: 'Italie',
  PAK: 'Pakistan',
  EGY: 'Egypte',
  IDN: 'Indonesie',
  ZAF: 'Afrique du Sud',
};

const POWER_COLORS: Record<string, string> = {
  USA: '#3b82f6', // Blue
  CHN: '#ef4444', // Red
  RUS: '#22c55e', // Green
  FRA: '#8b5cf6', // Purple
  GBR: '#f97316', // Orange
  IND: '#f59e0b', // Amber
  DEU: '#6b7280', // Gray
  JPN: '#ec4899', // Pink
  BRA: '#10b981', // Emerald
  TUR: '#dc2626', // Deep red
  SAU: '#059669', // Dark green
  IRN: '#7c3aed', // Violet
  ISR: '#0ea5e9', // Sky blue
  AUS: '#fbbf24', // Yellow
  KOR: '#6366f1', // Indigo
  ITA: '#14b8a6', // Teal
  PAK: '#84cc16', // Lime
  EGY: '#a855f7', // Fuchsia
  IDN: '#f43f5e', // Rose
  ZAF: '#eab308', // Yellow
};

// Real historical influence trends 2015-2025 with key events
const HISTORICAL_TRENDS: Record<string, { base: number; trend: number[]; events: Record<number, string> }> = {
  USA: {
    base: 850,
    trend: [1.0, 0.98, 0.97, 0.95, 0.94, 0.93, 0.92, 0.91, 0.90, 0.89, 0.88],
    events: {
      2016: 'Election Trump - Retrait accords internationaux',
      2020: 'COVID-19 - Affaiblissement soft power',
      2021: 'Retrait Afghanistan',
      2024: 'Election presidentielle',
    }
  },
  CHN: {
    base: 620,
    trend: [0.75, 0.78, 0.82, 0.85, 0.88, 0.90, 0.93, 0.95, 0.98, 1.00, 1.02],
    events: {
      2015: 'Lancement Nouvelles Routes de la Soie',
      2019: 'Tensions Hong Kong',
      2020: 'Diplomatie du masque COVID',
      2023: 'Mediation Arabie-Iran',
    }
  },
  RUS: {
    base: 450,
    trend: [0.95, 0.97, 0.98, 0.99, 1.00, 0.98, 0.96, 0.85, 0.80, 0.78, 0.75],
    events: {
      2015: 'Intervention Syrie',
      2018: 'Coupe du Monde FIFA',
      2022: 'Invasion Ukraine - Sanctions massives',
      2024: 'Renforcement liens Chine-Iran',
    }
  },
  FRA: {
    base: 380,
    trend: [1.0, 0.99, 0.97, 0.95, 0.93, 0.92, 0.90, 0.88, 0.85, 0.82, 0.80],
    events: {
      2017: 'Election Macron',
      2020: 'Retraits forces Sahel',
      2023: 'Coups d\'Etat Sahel - Perte influence Afrique',
    }
  },
  GBR: {
    base: 320,
    trend: [1.0, 0.98, 0.95, 0.92, 0.90, 0.88, 0.86, 0.85, 0.84, 0.83, 0.82],
    events: {
      2016: 'Brexit - Vote',
      2020: 'Brexit effectif',
      2022: 'AUKUS - Pivot Indo-Pacifique',
    }
  },
  IND: {
    base: 280,
    trend: [0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 0.97, 0.99, 1.01, 1.03, 1.05],
    events: {
      2017: 'Tensions Doklam avec Chine',
      2020: 'Affrontements Galwan',
      2023: 'Presidence G20',
    }
  },
  DEU: {
    base: 290,
    trend: [1.0, 1.01, 1.02, 1.02, 1.01, 1.00, 0.98, 0.95, 0.93, 0.92, 0.90],
    events: {
      2015: 'Crise migrants',
      2021: 'Fin ere Merkel',
      2022: 'Zeitenwende - Rearmement',
    }
  },
  JPN: {
    base: 240,
    trend: [0.95, 0.96, 0.97, 0.98, 0.99, 1.00, 1.01, 1.02, 1.03, 1.04, 1.05],
    events: {
      2020: 'RCEP',
      2022: 'Doublement budget defense',
      2023: 'Rapprochement Coree du Sud',
    }
  },
  TUR: {
    base: 180,
    trend: [0.90, 0.93, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10, 1.12],
    events: {
      2016: 'Coup d\'Etat manque',
      2019: 'Operation Syrie du Nord',
      2020: 'Intervention Libye/Caucase',
    }
  },
  BRA: {
    base: 150,
    trend: [1.0, 0.98, 0.95, 0.92, 0.90, 0.88, 0.87, 0.86, 0.88, 0.90, 0.92],
    events: {
      2016: 'Destitution Rousseff',
      2019: 'Election Bolsonaro',
      2023: 'Retour Lula - BRICS+',
    }
  },
  SAU: {
    base: 160,
    trend: [0.95, 0.96, 0.97, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10, 1.12],
    events: {
      2016: 'Vision 2030',
      2018: 'Affaire Khashoggi',
      2023: 'Normalisation Iran',
    }
  },
  IRN: {
    base: 140,
    trend: [0.95, 0.93, 0.90, 0.85, 0.82, 0.80, 0.82, 0.85, 0.88, 0.90, 0.92],
    events: {
      2015: 'Accord nucleaire JCPOA',
      2018: 'Retrait USA du JCPOA',
      2020: 'Elimination Soleimani',
    }
  },
};

// Medals for top 3
const MEDALS = ['gold', 'silver', 'bronze'] as const;
const MEDAL_STYLES: Record<typeof MEDALS[number], { bg: string; text: string; icon: string; glow: string }> = {
  gold: { bg: 'bg-gradient-to-br from-yellow-400 to-yellow-600', text: 'text-yellow-900', icon: '1', glow: 'shadow-yellow-400/50' },
  silver: { bg: 'bg-gradient-to-br from-gray-300 to-gray-500', text: 'text-gray-900', icon: '2', glow: 'shadow-gray-400/50' },
  bronze: { bg: 'bg-gradient-to-br from-orange-400 to-orange-700', text: 'text-orange-900', icon: '3', glow: 'shadow-orange-400/50' },
};

// Influence type breakdown labels
const INFLUENCE_TYPES = [
  { key: 'military', label: 'Militaire', color: '#ef4444', icon: 'M' },
  { key: 'economic', label: 'Economique', color: '#22c55e', icon: 'E' },
  { key: 'monetary', label: 'Monetaire', color: '#eab308', icon: '$' },
  { key: 'cultural', label: 'Culturel', color: '#8b5cf6', icon: 'C' },
  { key: 'diplomatic', label: 'Diplomatique', color: '#3b82f6', icon: 'D' },
  { key: 'religious', label: 'Religieux', color: '#f97316', icon: 'R' },
];

export default function InfluenceHistory({ currentYear, zones }: InfluenceHistoryProps) {
  const [expanded, setExpanded] = useState(true);
  const [selectedPowers, setSelectedPowers] = useState<string[]>(['USA', 'CHN', 'RUS', 'FRA']);
  const [viewType, setViewType] = useState<'total' | 'zones' | 'comparison'>('total');
  const [hoveredPoint, setHoveredPoint] = useState<{ power: string; year: number; value: number } | null>(null);
  const [selectedPowerDetail, setSelectedPowerDetail] = useState<string | null>(null);
  const [rankings, setRankings] = useState<Array<{
    rank: number;
    power_id: string;
    name_fr: string;
    total_influence: number;
    zones_dominated: number;
    zones_contested: number;
  }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRankings();
  }, []);

  const loadRankings = async () => {
    try {
      const data = await getInfluenceRankings();
      setRankings(data.rankings.slice(0, 10));
    } catch (error) {
      console.error('Failed to load rankings:', error);
      // Generate fallback rankings from zones
      generateFallbackRankings();
    } finally {
      setLoading(false);
    }
  };

  const generateFallbackRankings = () => {
    const powerStats: Record<string, { total: number; dominated: number; contested: number }> = {};

    ALL_POWERS.forEach(power => {
      powerStats[power] = { total: 0, dominated: 0, contested: 0 };
    });

    zones.forEach(zone => {
      Object.entries(zone.influence_levels).forEach(([power, level]) => {
        if (powerStats[power]) {
          powerStats[power].total += level;
        }
      });
      if (zone.dominant_power && powerStats[zone.dominant_power]) {
        powerStats[zone.dominant_power].dominated++;
      }
      zone.contested_by.forEach(power => {
        if (powerStats[power]) {
          powerStats[power].contested++;
        }
      });
    });

    const sorted = Object.entries(powerStats)
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, 10)
      .map(([power, stats], index) => ({
        rank: index + 1,
        power_id: power,
        name_fr: POWER_NAMES[power] || power,
        total_influence: stats.total,
        zones_dominated: stats.dominated,
        zones_contested: stats.contested,
      }));

    setRankings(sorted);
  };

  // Generate realistic history data based on real trends
  const historyData = useMemo(() => {
    const history: HistoryPoint[] = [];
    const startYear = currentYear - 10;

    // Calculate current totals from zones for calibration
    const currentTotals: Record<string, number> = {};
    ALL_POWERS.forEach(power => {
      currentTotals[power] = zones.reduce((sum, zone) => {
        return sum + (zone.influence_levels[power] || 0);
      }, 0);
    });

    // Generate historical data using real trends
    for (let yearOffset = 0; yearOffset <= 10; yearOffset++) {
      const year = startYear + yearOffset;
      const yearData: Record<string, number> = {};
      const events: Record<string, string> = {};

      ALL_POWERS.forEach(power => {
        const trend = HISTORICAL_TRENDS[power];
        if (trend) {
          // Use historical trend data
          const trendValue = trend.trend[yearOffset] || 1;
          const calibrationFactor = currentTotals[power] / (trend.base * (trend.trend[10] || 1));
          yearData[power] = Math.round(trend.base * trendValue * calibrationFactor);

          // Add events
          if (trend.events[year]) {
            events[power] = trend.events[year];
          }
        } else {
          // For powers without detailed trends, use simple interpolation
          const factor = 0.85 + (yearOffset / 10) * 0.3;
          yearData[power] = Math.round(currentTotals[power] * factor);
        }
      });

      history.push({ year, data: yearData, events: Object.keys(events).length > 0 ? events : undefined });
    }

    return history;
  }, [currentYear, zones]);

  // Get max value for chart scaling
  const maxValue = useMemo(() => {
    let max = 0;
    historyData.forEach(point => {
      selectedPowers.forEach(power => {
        if (point.data[power] > max) max = point.data[power];
      });
    });
    return max * 1.15;
  }, [historyData, selectedPowers]);

  // Toggle power selection
  const togglePower = (powerId: string) => {
    setSelectedPowers(prev =>
      prev.includes(powerId)
        ? prev.filter(p => p !== powerId)
        : [...prev, powerId]
    );
  };

  // Calculate detailed zone stats for each power
  const zoneStats = useMemo(() => {
    const stats: Record<string, {
      dominated: number;
      contested: number;
      total: number;
      average: number;
      byType: Record<string, number>;
      topZones: { name: string; level: number }[];
      trend: 'up' | 'down' | 'stable';
      trendValue: number;
    }> = {};

    MAJOR_POWERS.forEach(power => {
      const byType: Record<string, number> = {};
      INFLUENCE_TYPES.forEach(t => byType[t.key] = 0);

      stats[power] = {
        dominated: 0,
        contested: 0,
        total: 0,
        average: 0,
        byType,
        topZones: [],
        trend: 'stable',
        trendValue: 0,
      };
    });

    // Calculate current stats from zones
    const zoneInfluences: Record<string, { name: string; level: number }[]> = {};
    MAJOR_POWERS.forEach(power => zoneInfluences[power] = []);

    zones.forEach(zone => {
      if (zone.dominant_power && stats[zone.dominant_power]) {
        stats[zone.dominant_power].dominated++;
      }
      zone.contested_by.forEach(power => {
        if (stats[power]) {
          stats[power].contested++;
        }
      });
      MAJOR_POWERS.forEach(power => {
        const level = zone.influence_levels[power] || 0;
        stats[power].total += level;
        zoneInfluences[power].push({ name: zone.name_fr, level });

        // Add breakdown if available
        if (zone.influence_breakdown?.[power]) {
          Object.entries(zone.influence_breakdown[power]).forEach(([type, value]) => {
            if (stats[power].byType[type] !== undefined) {
              stats[power].byType[type] += value;
            }
          });
        }
      });
    });

    // Calculate averages and top zones
    MAJOR_POWERS.forEach(power => {
      stats[power].average = zones.length > 0 ? Math.round(stats[power].total / zones.length) : 0;
      stats[power].topZones = zoneInfluences[power]
        .sort((a, b) => b.level - a.level)
        .slice(0, 3);

      // Calculate trend from history
      if (historyData.length >= 3) {
        const recent = historyData[historyData.length - 1].data[power] || 0;
        const older = historyData[historyData.length - 3].data[power] || 0;
        const change = recent - older;
        const percentChange = older > 0 ? (change / older) * 100 : 0;

        stats[power].trendValue = percentChange;
        if (percentChange > 2) stats[power].trend = 'up';
        else if (percentChange < -2) stats[power].trend = 'down';
        else stats[power].trend = 'stable';
      }
    });

    return stats;
  }, [zones, historyData]);

  // Get events for the chart tooltip
  const getEventsForYear = (year: number) => {
    const point = historyData.find(p => p.year === year);
    return point?.events || {};
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-cyan-900/50 to-gray-700 cursor-pointer hover:from-cyan-900/70 transition-all"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-sm">
            {'📊'}
          </div>
          <div>
            <span className="text-lg font-bold">Historique & Statistiques</span>
            <div className="text-xs text-gray-400">
              {currentYear - 10} - {currentYear} | Evolution de l'influence mondiale
            </div>
          </div>
        </div>
        <button
          className="text-gray-400 hover:text-white transition-transform duration-200"
          style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
          {'▲'}
        </button>
      </div>

      <div className={`transition-all duration-300 ease-in-out overflow-hidden ${expanded ? 'max-h-[1200px] opacity-100' : 'max-h-0 opacity-0'}`}>
        {/* View tabs */}
        <div className="flex border-b border-gray-700">
          {([
            { key: 'total', label: 'Evolution 10 ans', icon: '📈' },
            { key: 'zones', label: 'Stats par Puissance', icon: '🌍' },
            { key: 'comparison', label: 'Top 10 Mondial', icon: '🏆' },
          ] as const).map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setViewType(key)}
              className={`flex-1 px-3 py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-all ${
                viewType === key
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-750 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </div>

        <div className="p-4">
          {/* Evolution Chart - 10 Year Line Graph */}
          {viewType === 'total' && (
            <>
              {/* Power selector with colored badges */}
              <div className="flex flex-wrap gap-2 mb-4">
                {MAJOR_POWERS.map(power => {
                  const isSelected = selectedPowers.includes(power);
                  const current = historyData[historyData.length - 1]?.data[power] || 0;
                  const previous = historyData[historyData.length - 2]?.data[power] || 0;
                  const change = current - previous;

                  return (
                    <button
                      key={power}
                      onClick={() => togglePower(power)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all border-2 ${
                        isSelected
                          ? 'border-current shadow-lg'
                          : 'border-transparent opacity-40 hover:opacity-70'
                      }`}
                      style={{
                        backgroundColor: `${POWER_COLORS[power]}20`,
                        color: POWER_COLORS[power],
                        borderColor: isSelected ? POWER_COLORS[power] : 'transparent',
                      }}
                    >
                      <span className="text-base">{COUNTRY_FLAGS[power]}</span>
                      <span>{power}</span>
                      {isSelected && (
                        <span className={`text-[10px] ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {change >= 0 ? '↑' : '↓'}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Enhanced Line chart */}
              <div className="relative h-72 bg-gray-900 rounded-lg p-4 mb-4">
                {/* Y-axis labels */}
                <div className="absolute left-0 top-4 bottom-8 w-12 flex flex-col justify-between text-xs text-gray-500">
                  {[1, 0.75, 0.5, 0.25, 0].map(factor => (
                    <span key={factor} className="text-right pr-2">
                      {Math.round(maxValue * factor)}
                    </span>
                  ))}
                </div>

                {/* Chart area */}
                <div className="absolute left-14 right-4 top-4 bottom-8">
                  {/* Grid lines */}
                  <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                    {[0, 1, 2, 3, 4].map(i => (
                      <div key={i} className="border-t border-gray-700/50 border-dashed" />
                    ))}
                  </div>

                  {/* Vertical grid lines for years */}
                  <div className="absolute inset-0 flex justify-between pointer-events-none">
                    {historyData.map((_, i) => (
                      <div key={i} className="border-l border-gray-800 h-full" style={{ width: 0 }} />
                    ))}
                  </div>

                  {/* SVG for gradient fills and lines */}
                  <svg className="absolute inset-0 w-full h-full overflow-visible" preserveAspectRatio="none">
                    <defs>
                      {selectedPowers.map(power => (
                        <linearGradient key={`grad-${power}`} id={`gradient-${power}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={POWER_COLORS[power]} stopOpacity="0.3" />
                          <stop offset="100%" stopColor={POWER_COLORS[power]} stopOpacity="0" />
                        </linearGradient>
                      ))}
                    </defs>

                    {/* Area fills */}
                    {selectedPowers.map(power => {
                      const points = historyData.map((point, i) => {
                        const x = (i / (historyData.length - 1)) * 100;
                        const y = 100 - (point.data[power] / maxValue) * 100;
                        return `${x},${y}`;
                      });

                      const areaPath = `M0,100 L${points.join(' L')} L100,100 Z`;

                      return (
                        <path
                          key={`area-${power}`}
                          d={areaPath}
                          fill={`url(#gradient-${power})`}
                          opacity="0.5"
                        />
                      );
                    })}

                    {/* Lines with glow effect */}
                    {selectedPowers.map(power => {
                      const points = historyData.map((point, i) => {
                        const x = (i / (historyData.length - 1)) * 100;
                        const y = 100 - (point.data[power] / maxValue) * 100;
                        return `${x},${y}`;
                      }).join(' ');

                      return (
                        <g key={power}>
                          {/* Glow effect */}
                          <polyline
                            points={points}
                            fill="none"
                            stroke={POWER_COLORS[power]}
                            strokeWidth="6"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            vectorEffect="non-scaling-stroke"
                            opacity="0.2"
                            filter="blur(4px)"
                          />
                          {/* Main line */}
                          <polyline
                            points={points}
                            fill="none"
                            stroke={POWER_COLORS[power]}
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            vectorEffect="non-scaling-stroke"
                          />
                        </g>
                      );
                    })}
                  </svg>

                  {/* Interactive data points */}
                  {selectedPowers.map(power => (
                    historyData.map((point, i) => {
                      const x = (i / (historyData.length - 1)) * 100;
                      const y = 100 - (point.data[power] / maxValue) * 100;
                      const isHovered = hoveredPoint?.power === power && hoveredPoint?.year === point.year;
                      const hasEvent = point.events?.[power];

                      return (
                        <div
                          key={`${power}-${i}`}
                          className={`absolute rounded-full transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-200 ${
                            isHovered ? 'scale-150 z-10' : 'hover:scale-125'
                          } ${hasEvent ? 'ring-2 ring-white/50' : ''}`}
                          style={{
                            left: `${x}%`,
                            top: `${y}%`,
                            backgroundColor: POWER_COLORS[power],
                            width: isHovered ? '12px' : '8px',
                            height: isHovered ? '12px' : '8px',
                            boxShadow: isHovered ? `0 0 12px ${POWER_COLORS[power]}` : 'none',
                          }}
                          onMouseEnter={() => setHoveredPoint({ power, year: point.year, value: point.data[power] })}
                          onMouseLeave={() => setHoveredPoint(null)}
                        />
                      );
                    })
                  ))}

                  {/* Tooltip */}
                  {hoveredPoint && (
                    <div
                      className="absolute z-20 bg-gray-900 border border-gray-600 rounded-lg p-3 shadow-xl pointer-events-none transform -translate-x-1/2"
                      style={{
                        left: `${((historyData.findIndex(p => p.year === hoveredPoint.year)) / (historyData.length - 1)) * 100}%`,
                        top: '-80px',
                        minWidth: '180px',
                      }}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">{COUNTRY_FLAGS[hoveredPoint.power]}</span>
                        <span className="font-bold" style={{ color: POWER_COLORS[hoveredPoint.power] }}>
                          {POWER_NAMES[hoveredPoint.power] || hoveredPoint.power}
                        </span>
                      </div>
                      <div className="text-gray-400 text-xs mb-1">Annee {hoveredPoint.year}</div>
                      <div className="text-white font-bold text-lg">{hoveredPoint.value} pts</div>
                      {getEventsForYear(hoveredPoint.year)[hoveredPoint.power] && (
                        <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-yellow-400">
                          {'⚡'} {getEventsForYear(hoveredPoint.year)[hoveredPoint.power]}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* X-axis labels with year */}
                <div className="absolute left-14 right-4 bottom-0 h-6 flex justify-between text-xs text-gray-500">
                  {historyData.map((point, i) => (
                    <span
                      key={point.year}
                      className={`${i % 2 === 0 ? 'opacity-100' : 'opacity-50'}`}
                    >
                      {point.year}
                    </span>
                  ))}
                </div>
              </div>

              {/* Legend with detailed stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {selectedPowers.map(power => {
                  const current = historyData[historyData.length - 1]?.data[power] || 0;
                  const tenYearsAgo = historyData[0]?.data[power] || 0;
                  const totalChange = current - tenYearsAgo;
                  const percentChange = tenYearsAgo > 0 ? ((totalChange / tenYearsAgo) * 100).toFixed(1) : '0';

                  return (
                    <div
                      key={power}
                      className="bg-gray-700/30 rounded-lg p-2 border-l-4"
                      style={{ borderColor: POWER_COLORS[power] }}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span>{COUNTRY_FLAGS[power]}</span>
                        <span className="text-sm font-medium">{power}</span>
                      </div>
                      <div className="text-lg font-bold" style={{ color: POWER_COLORS[power] }}>
                        {current}
                      </div>
                      <div className={`text-xs ${totalChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {totalChange >= 0 ? '+' : ''}{totalChange} ({percentChange}%) sur 10 ans
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* Zone Stats - Detailed power analysis */}
          {viewType === 'zones' && (
            <div className="space-y-4">
              {/* Power selector for detail view */}
              {!selectedPowerDetail ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {MAJOR_POWERS.map(power => {
                    const stats = zoneStats[power];
                    const trend = stats?.trend || 'stable';

                    return (
                      <button
                        key={power}
                        onClick={() => setSelectedPowerDetail(power)}
                        className="bg-gray-700/40 hover:bg-gray-700/60 rounded-lg p-3 transition-all text-left group"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">{COUNTRY_FLAGS[power]}</span>
                            <span className="font-bold">{power}</span>
                          </div>
                          <span className={`text-lg ${
                            trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'
                          }`}>
                            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
                          </span>
                        </div>
                        <div className="text-2xl font-bold mb-1" style={{ color: POWER_COLORS[power] }}>
                          {stats?.total || 0}
                        </div>
                        <div className="text-xs text-gray-400 flex gap-2">
                          <span className="text-green-400">{stats?.dominated || 0}</span> dom.
                          <span className="text-yellow-400">{stats?.contested || 0}</span> cont.
                        </div>
                        <div className="mt-2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(100, (stats?.total || 0) / 8)}%`,
                              backgroundColor: POWER_COLORS[power],
                            }}
                          />
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                // Detailed view for selected power
                <div className="space-y-4">
                  <button
                    onClick={() => setSelectedPowerDetail(null)}
                    className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                  >
                    {'←'} Retour au classement
                  </button>

                  <div className="bg-gray-700/30 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-4xl">{COUNTRY_FLAGS[selectedPowerDetail]}</span>
                        <div>
                          <h3 className="text-xl font-bold">{POWER_NAMES[selectedPowerDetail]}</h3>
                          <p className="text-gray-400 text-sm">Analyse detaillee de l'influence</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold" style={{ color: POWER_COLORS[selectedPowerDetail] }}>
                          {zoneStats[selectedPowerDetail]?.total || 0}
                        </div>
                        <div className="text-xs text-gray-400">points totaux</div>
                      </div>
                    </div>

                    {/* Key metrics */}
                    <div className="grid grid-cols-4 gap-3 mb-4">
                      <div className="bg-gray-800 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {zoneStats[selectedPowerDetail]?.dominated || 0}
                        </div>
                        <div className="text-xs text-gray-500">Zones dominees</div>
                      </div>
                      <div className="bg-gray-800 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-yellow-400">
                          {zoneStats[selectedPowerDetail]?.contested || 0}
                        </div>
                        <div className="text-xs text-gray-500">En contestation</div>
                      </div>
                      <div className="bg-gray-800 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {zoneStats[selectedPowerDetail]?.average || 0}
                        </div>
                        <div className="text-xs text-gray-500">Moyenne/zone</div>
                      </div>
                      <div className="bg-gray-800 rounded-lg p-3 text-center">
                        <div className={`text-2xl font-bold ${
                          zoneStats[selectedPowerDetail]?.trend === 'up' ? 'text-green-400' :
                          zoneStats[selectedPowerDetail]?.trend === 'down' ? 'text-red-400' : 'text-gray-400'
                        }`}>
                          {zoneStats[selectedPowerDetail]?.trendValue?.toFixed(1) || 0}%
                        </div>
                        <div className="text-xs text-gray-500">Tendance</div>
                      </div>
                    </div>

                    {/* Influence breakdown by type */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">Repartition par type d'influence</h4>
                      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                        {INFLUENCE_TYPES.map(type => {
                          const value = zoneStats[selectedPowerDetail]?.byType?.[type.key] || 0;
                          const total = zoneStats[selectedPowerDetail]?.total || 1;
                          const percent = ((value / total) * 100).toFixed(0);

                          return (
                            <div key={type.key} className="bg-gray-800 rounded p-2 text-center">
                              <div
                                className="w-8 h-8 mx-auto rounded-full flex items-center justify-center text-xs font-bold mb-1"
                                style={{ backgroundColor: type.color }}
                              >
                                {type.icon}
                              </div>
                              <div className="text-xs text-gray-400">{type.label}</div>
                              <div className="text-sm font-bold">{value > 0 ? value : '-'}</div>
                              {value > 0 && (
                                <div className="text-[10px] text-gray-500">{percent}%</div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Top zones */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 mb-2">Principales zones d'influence</h4>
                      <div className="space-y-2">
                        {zoneStats[selectedPowerDetail]?.topZones.map((zone, i) => (
                          <div key={zone.name} className="flex items-center gap-3 bg-gray-800 rounded-lg p-2">
                            <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold">
                              {i + 1}
                            </div>
                            <div className="flex-1">{zone.name}</div>
                            <div className="font-bold" style={{ color: POWER_COLORS[selectedPowerDetail] }}>
                              {zone.level}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Rankings with Medals */}
          {viewType === 'comparison' && (
            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-8 text-gray-500">
                  <span className="animate-spin inline-block text-2xl">{'⏳'}</span>
                  <div className="mt-2">Chargement du classement...</div>
                </div>
              ) : (
                <>
                  {/* Podium for top 3 */}
                  <div className="flex justify-center items-end gap-4 mb-6 pt-4">
                    {/* 2nd place */}
                    {rankings[1] && (
                      <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-2 relative">
                          <span className="text-4xl">{COUNTRY_FLAGS[rankings[1].power_id]}</span>
                          <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full ${MEDAL_STYLES.silver.bg} flex items-center justify-center text-xs font-bold ${MEDAL_STYLES.silver.text} shadow-lg ${MEDAL_STYLES.silver.glow}`}>
                            2
                          </div>
                        </div>
                        <div className="bg-gradient-to-t from-gray-400 to-gray-300 rounded-t-lg w-20 h-16 flex flex-col items-center justify-center">
                          <span className="text-sm font-bold text-gray-900">{rankings[1].power_id}</span>
                          <span className="text-xs text-gray-700">{rankings[1].total_influence}</span>
                        </div>
                      </div>
                    )}

                    {/* 1st place */}
                    {rankings[0] && (
                      <div className="text-center">
                        <div className="w-20 h-20 mx-auto mb-2 relative">
                          <span className="text-5xl">{COUNTRY_FLAGS[rankings[0].power_id]}</span>
                          <div className={`absolute -top-2 -right-2 w-8 h-8 rounded-full ${MEDAL_STYLES.gold.bg} flex items-center justify-center text-sm font-bold ${MEDAL_STYLES.gold.text} shadow-lg ${MEDAL_STYLES.gold.glow} animate-pulse`}>
                            {'👑'}
                          </div>
                        </div>
                        <div className="bg-gradient-to-t from-yellow-500 to-yellow-400 rounded-t-lg w-24 h-24 flex flex-col items-center justify-center">
                          <span className="text-lg font-bold text-yellow-900">{rankings[0].power_id}</span>
                          <span className="text-sm text-yellow-800 font-bold">{rankings[0].total_influence}</span>
                          <span className="text-xs text-yellow-700">pts</span>
                        </div>
                      </div>
                    )}

                    {/* 3rd place */}
                    {rankings[2] && (
                      <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-2 relative">
                          <span className="text-4xl">{COUNTRY_FLAGS[rankings[2].power_id]}</span>
                          <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full ${MEDAL_STYLES.bronze.bg} flex items-center justify-center text-xs font-bold ${MEDAL_STYLES.bronze.text} shadow-lg ${MEDAL_STYLES.bronze.glow}`}>
                            3
                          </div>
                        </div>
                        <div className="bg-gradient-to-t from-orange-600 to-orange-500 rounded-t-lg w-20 h-12 flex flex-col items-center justify-center">
                          <span className="text-sm font-bold text-orange-100">{rankings[2].power_id}</span>
                          <span className="text-xs text-orange-200">{rankings[2].total_influence}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Full ranking list */}
                  <div className="space-y-2">
                    {rankings.map((ranking, index) => {
                      const color = POWER_COLORS[ranking.power_id] || '#6b7280';
                      const isTopThree = index < 3;
                      const medal = isTopThree ? MEDALS[index] : null;

                      // Calculate bar width based on max influence
                      const maxInfluence = rankings[0]?.total_influence || 1;
                      const barWidth = (ranking.total_influence / maxInfluence) * 100;

                      return (
                        <div
                          key={ranking.power_id}
                          className={`relative flex items-center gap-3 p-3 rounded-lg transition-all overflow-hidden ${
                            isTopThree ? 'bg-gray-700/60' : 'bg-gray-800/40 hover:bg-gray-800/60'
                          }`}
                        >
                          {/* Background bar */}
                          <div
                            className="absolute inset-y-0 left-0 opacity-10"
                            style={{
                              width: `${barWidth}%`,
                              backgroundColor: color,
                            }}
                          />

                          {/* Rank with medal */}
                          <div className="relative z-10">
                            {medal ? (
                              <div className={`w-10 h-10 rounded-full ${MEDAL_STYLES[medal].bg} flex items-center justify-center font-bold ${MEDAL_STYLES[medal].text} shadow-lg ${MEDAL_STYLES[medal].glow}`}>
                                {ranking.rank}
                              </div>
                            ) : (
                              <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center font-bold text-gray-400">
                                {ranking.rank}
                              </div>
                            )}
                          </div>

                          {/* Country info */}
                          <div className="flex-1 relative z-10">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">{COUNTRY_FLAGS[ranking.power_id]}</span>
                              <span className="font-bold">{ranking.name_fr}</span>
                              {isTopThree && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400">
                                  Top 3
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 flex gap-4 mt-1">
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                {ranking.zones_dominated} dominees
                              </span>
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                                {ranking.zones_contested} contestees
                              </span>
                            </div>
                          </div>

                          {/* Score */}
                          <div className="text-right relative z-10">
                            <div className="text-2xl font-bold" style={{ color }}>
                              {ranking.total_influence}
                            </div>
                            <div className="text-xs text-gray-500">points</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Global stats footer */}
                  <div className="mt-4 pt-4 border-t border-gray-700 grid grid-cols-3 gap-4 text-center text-xs text-gray-400">
                    <div>
                      <div className="text-lg font-bold text-white">{zones.length}</div>
                      <div>Zones mondiales</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-white">{rankings.length}</div>
                      <div>Puissances classees</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-white">
                        {rankings.reduce((sum, r) => sum + r.total_influence, 0)}
                      </div>
                      <div>Points totaux Top 10</div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
