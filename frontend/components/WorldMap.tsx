'use client';

import { useState, useMemo } from 'react';
import { InfluenceZone, COUNTRY_FLAGS, INFLUENCE_TYPE_COLORS } from '@/lib/types';

interface WorldMapProps {
  zones: InfluenceZone[];
  onZoneClick?: (zone: InfluenceZone) => void;
  selectedZoneId?: string;
  highlightPower?: string;
}

// Realistic zone positions based on actual geography (Mercator-style projection)
const ZONE_POSITIONS: Record<string, { x: number; y: number; width: number; height: number }> = {
  // Americas
  north_america: { x: 3, y: 12, width: 22, height: 22 },
  central_america: { x: 8, y: 36, width: 14, height: 12 },
  south_america: { x: 14, y: 50, width: 16, height: 32 },
  // Europe
  western_europe: { x: 40, y: 16, width: 12, height: 16 },
  eastern_europe: { x: 52, y: 14, width: 10, height: 16 },
  nordic: { x: 46, y: 6, width: 12, height: 10 },
  // Russia & FSU
  caucasus: { x: 56, y: 26, width: 8, height: 8 },
  central_asia: { x: 60, y: 22, width: 14, height: 12 },
  // Middle East
  middle_east_gulf: { x: 54, y: 34, width: 14, height: 12 },
  levant: { x: 50, y: 30, width: 6, height: 10 },
  // Africa
  north_africa: { x: 38, y: 32, width: 16, height: 12 },
  west_africa: { x: 34, y: 44, width: 14, height: 16 },
  east_africa: { x: 50, y: 48, width: 12, height: 18 },
  southern_africa: { x: 46, y: 66, width: 14, height: 16 },
  // Asia
  south_asia: { x: 64, y: 34, width: 14, height: 16 },
  southeast_asia: { x: 74, y: 42, width: 14, height: 18 },
  east_asia: { x: 76, y: 20, width: 18, height: 20 },
  // Pacific
  oceania: { x: 80, y: 62, width: 16, height: 18 },
  // Poles
  arctic: { x: 35, y: 1, width: 30, height: 6 },
};

// Zone names in French with accurate geopolitical descriptions
const ZONE_LABELS: Record<string, string> = {
  north_america: 'Amerique du Nord',
  central_america: 'Am. Centrale',
  south_america: 'Amerique du Sud',
  western_europe: 'Europe Occ.',
  eastern_europe: 'Europe Est',
  nordic: 'Pays Nordiques',
  caucasus: 'Caucase',
  central_asia: 'Asie Centrale',
  middle_east_gulf: 'Golfe Persique',
  levant: 'Levant',
  north_africa: 'Maghreb',
  west_africa: 'Afrique Ouest',
  east_africa: 'Corne Afrique',
  southern_africa: 'Afrique Aust.',
  south_asia: 'Sous-continent',
  southeast_asia: 'Asie Sud-Est',
  east_asia: 'Asie Est',
  oceania: 'Oceanie',
  arctic: 'Arctique',
};

// Real geopolitical data 2025 - strategic resources and conflicts
const ZONE_STRATEGIC_INFO: Record<string, {
  conflicts: string[];
  militaryBases: { power: string; count: number }[];
  strategicAssets: string[];
  tensions: number; // 0-100
}> = {
  north_america: {
    conflicts: [],
    militaryBases: [{ power: 'USA', count: 450 }],
    strategicAssets: ['Petrole schiste', 'Tech Silicon Valley', 'NORAD'],
    tensions: 5,
  },
  central_america: {
    conflicts: ['Migration', 'Narcotrafic'],
    militaryBases: [{ power: 'USA', count: 12 }],
    strategicAssets: ['Canal Panama', 'Corridor migratoire'],
    tensions: 35,
  },
  south_america: {
    conflicts: ['Venezuela instabilite', 'Cartels'],
    militaryBases: [{ power: 'USA', count: 3 }, { power: 'CHN', count: 0 }],
    strategicAssets: ['Lithium triangle', 'Amazonie', 'Petrole Venezuela'],
    tensions: 40,
  },
  western_europe: {
    conflicts: [],
    militaryBases: [{ power: 'USA', count: 45 }, { power: 'FRA', count: 20 }, { power: 'GBR', count: 15 }],
    strategicAssets: ['UE economie', 'OTAN QG', 'Tech avancee'],
    tensions: 25,
  },
  eastern_europe: {
    conflicts: ['Guerre Ukraine-Russie'],
    militaryBases: [{ power: 'USA', count: 15 }, { power: 'RUS', count: 5 }],
    strategicAssets: ['Transit gaz', 'Industrie defense', 'Cereales Ukraine'],
    tensions: 95,
  },
  nordic: {
    conflicts: [],
    militaryBases: [{ power: 'USA', count: 8 }],
    strategicAssets: ['Petrole Norvege', 'Terres rares Groenland', 'Route arctique'],
    tensions: 20,
  },
  caucasus: {
    conflicts: ['Tensions Armenie-Azerbaidjan', 'Georgie occupee'],
    militaryBases: [{ power: 'RUS', count: 8 }, { power: 'TUR', count: 2 }],
    strategicAssets: ['Pipeline BTC', 'Route transit'],
    tensions: 70,
  },
  central_asia: {
    conflicts: ['Instabilite Afghanistan'],
    militaryBases: [{ power: 'RUS', count: 6 }, { power: 'CHN', count: 1 }],
    strategicAssets: ['Uranium Kazakhstan', 'Gaz Turkmenistan', 'Route soie'],
    tensions: 45,
  },
  middle_east_gulf: {
    conflicts: ['Tensions Iran-Israel', 'Guerre Yemen'],
    militaryBases: [{ power: 'USA', count: 35 }, { power: 'FRA', count: 3 }, { power: 'GBR', count: 2 }],
    strategicAssets: ['Petrole 60% reserves', 'Detroits Ormuz', 'GNL Qatar'],
    tensions: 80,
  },
  levant: {
    conflicts: ['Conflit Israel-Palestine', 'Guerre Syrie', 'Hezbollah Liban'],
    militaryBases: [{ power: 'USA', count: 5 }, { power: 'RUS', count: 3 }, { power: 'IRN', count: 4 }],
    strategicAssets: ['Gaz Mediterranee Est', 'Position strategique'],
    tensions: 95,
  },
  north_africa: {
    conflicts: ['Instabilite Libye', 'Sahara Occidental', 'Terrorisme Sahel'],
    militaryBases: [{ power: 'FRA', count: 4 }, { power: 'USA', count: 3 }],
    strategicAssets: ['Gaz Algerie', 'Phosphates Maroc', 'Canal Suez'],
    tensions: 55,
  },
  west_africa: {
    conflicts: ['Coups militaires', 'Wagner/Africa Corps', 'Jihadisme Sahel'],
    militaryBases: [{ power: 'FRA', count: 2 }, { power: 'USA', count: 4 }, { power: 'RUS', count: 3 }],
    strategicAssets: ['Or', 'Uranium Niger', 'Cacao', 'Zone franc CFA'],
    tensions: 75,
  },
  east_africa: {
    conflicts: ['Guerre Soudan', 'Tigre Ethiopie', 'Piraterie'],
    militaryBases: [{ power: 'USA', count: 4 }, { power: 'CHN', count: 1 }, { power: 'FRA', count: 2 }],
    strategicAssets: ['Bab-el-Mandeb', 'Nil', 'Djibouti hub'],
    tensions: 70,
  },
  southern_africa: {
    conflicts: ['Instabilite Mozambique'],
    militaryBases: [{ power: 'USA', count: 1 }],
    strategicAssets: ['Platine', 'Diamants', 'Chrome', 'Cap Bonne-Esperance'],
    tensions: 30,
  },
  south_asia: {
    conflicts: ['Tensions Inde-Pakistan', 'Cachemire', 'Instabilite Bangladesh'],
    militaryBases: [{ power: 'USA', count: 2 }, { power: 'CHN', count: 1 }],
    strategicAssets: ['Population 2Mds', 'Tech Inde', 'Nucleaire'],
    tensions: 60,
  },
  southeast_asia: {
    conflicts: ['Mer de Chine Sud', 'Myanmar guerre civile'],
    militaryBases: [{ power: 'USA', count: 8 }, { power: 'CHN', count: 3 }],
    strategicAssets: ['Detroit Malacca', 'Semi-conducteurs', 'ASEAN economie'],
    tensions: 65,
  },
  east_asia: {
    conflicts: ['Taiwan tensions', 'Coree du Nord'],
    militaryBases: [{ power: 'USA', count: 85 }, { power: 'CHN', count: 50 }, { power: 'JPN', count: 30 }],
    strategicAssets: ['Semiconducteurs Taiwan', 'Tech Japon/Coree', 'Commerce mondial'],
    tensions: 85,
  },
  oceania: {
    conflicts: ['Competition Chine-USA Pacifique'],
    militaryBases: [{ power: 'USA', count: 5 }, { power: 'AUS', count: 10 }],
    strategicAssets: ['Minerais Australie', 'Routes maritimes', 'AUKUS'],
    tensions: 40,
  },
  arctic: {
    conflicts: ['Revendications territoriales', 'Routes maritimes'],
    militaryBases: [{ power: 'RUS', count: 15 }, { power: 'USA', count: 5 }, { power: 'CAN', count: 4 }],
    strategicAssets: ['Petrole offshore', 'Route Nord', 'Ressources inexploitees'],
    tensions: 50,
  },
};

export default function WorldMap({
  zones,
  onZoneClick,
  selectedZoneId,
  highlightPower,
}: WorldMapProps) {
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'dominant' | 'tensions' | 'resources' | 'influence'>('dominant');

  // Get zone color based on view mode - using real geopolitical data
  const getZoneColor = (zone: InfluenceZone): string => {
    const strategicInfo = ZONE_STRATEGIC_INFO[zone.id];

    switch (viewMode) {
      case 'dominant':
        if (!zone.dominant_power) return 'rgba(75, 85, 99, 0.5)';
        // Realistic power colors based on traditional geopolitical representation
        const powerColors: Record<string, string> = {
          USA: 'rgba(30, 64, 175, 0.65)',   // Dark blue - US
          CHN: 'rgba(185, 28, 28, 0.65)',   // Deep red - China
          RUS: 'rgba(22, 101, 52, 0.65)',   // Forest green - Russia
          FRA: 'rgba(79, 70, 229, 0.6)',    // Indigo - France
          GBR: 'rgba(194, 65, 12, 0.6)',    // Burnt orange - UK
          IND: 'rgba(234, 88, 12, 0.6)',    // Orange - India
          DEU: 'rgba(64, 64, 64, 0.6)',     // Charcoal - Germany
          BRA: 'rgba(21, 128, 61, 0.6)',    // Bright green - Brazil
          TUR: 'rgba(153, 27, 27, 0.6)',    // Crimson - Turkey
          SAU: 'rgba(74, 222, 128, 0.6)',   // Lime - Saudi
          IRN: 'rgba(126, 34, 206, 0.6)',   // Purple - Iran
          ISR: 'rgba(59, 130, 246, 0.6)',   // Blue - Israel
          AUS: 'rgba(251, 146, 60, 0.6)',   // Light orange - Australia
          JPN: 'rgba(244, 63, 94, 0.6)',    // Rose - Japan
          ZAF: 'rgba(245, 158, 11, 0.6)',   // Amber - South Africa
        };
        return powerColors[zone.dominant_power] || 'rgba(156, 163, 175, 0.5)';

      case 'tensions':
        // Use real tension data from ZONE_STRATEGIC_INFO
        const tensions = strategicInfo?.tensions || 0;
        if (tensions >= 80) return 'rgba(220, 38, 38, 0.8)';   // Critical - bright red
        if (tensions >= 60) return 'rgba(234, 88, 12, 0.7)';   // High - orange
        if (tensions >= 40) return 'rgba(234, 179, 8, 0.6)';   // Moderate - yellow
        if (tensions >= 20) return 'rgba(132, 204, 22, 0.5)';  // Low - lime
        return 'rgba(34, 197, 94, 0.4)';                        // Stable - green

      case 'resources':
        // Combined view: oil + strategic resources + strategic chokepoints
        const hasChokepoint = strategicInfo?.strategicAssets.some(a =>
          a.includes('Detroit') || a.includes('Canal') || a.includes('Bab') || a.includes('Ormuz')
        );
        if (zone.has_oil && zone.has_strategic_resources && hasChokepoint) {
          return 'rgba(234, 179, 8, 0.9)';  // Gold - maximum strategic value
        }
        if (zone.has_oil && zone.has_strategic_resources) {
          return 'rgba(234, 179, 8, 0.7)';  // Bright yellow
        }
        if (zone.has_oil) return 'rgba(23, 23, 23, 0.75)';  // Dark (petroleum)
        if (zone.has_strategic_resources) return 'rgba(59, 130, 246, 0.6)';  // Blue
        if (hasChokepoint) return 'rgba(168, 85, 247, 0.6)';  // Purple for chokepoints
        return 'rgba(75, 85, 99, 0.25)';

      case 'influence':
        if (!highlightPower) return 'rgba(75, 85, 99, 0.3)';
        const level = zone.influence_levels[highlightPower] || 0;
        if (level >= 80) return 'rgba(34, 197, 94, 0.8)';
        if (level >= 60) return 'rgba(132, 204, 22, 0.65)';
        if (level >= 40) return 'rgba(234, 179, 8, 0.55)';
        if (level >= 20) return 'rgba(249, 115, 22, 0.45)';
        return 'rgba(75, 85, 99, 0.25)';

      default:
        return 'rgba(75, 85, 99, 0.5)';
    }
  };

  // Get zone border style
  const getZoneBorder = (zone: InfluenceZone): string => {
    if (selectedZoneId === zone.id) return '3px solid #a855f7';
    if (hoveredZone === zone.id) return '2px solid #60a5fa';
    if (zone.contested_by.length > 0) return '1px dashed rgba(234, 179, 8, 0.5)';
    return '1px solid rgba(75, 85, 99, 0.3)';
  };

  // Legend items based on view mode - with real geopolitical labels
  const legendItems = useMemo(() => {
    switch (viewMode) {
      case 'dominant':
        return [
          { color: 'rgba(30, 64, 175, 0.65)', label: 'Etats-Unis' },
          { color: 'rgba(185, 28, 28, 0.65)', label: 'Chine' },
          { color: 'rgba(22, 101, 52, 0.65)', label: 'Russie' },
          { color: 'rgba(79, 70, 229, 0.6)', label: 'France' },
          { color: 'rgba(194, 65, 12, 0.6)', label: 'Royaume-Uni' },
          { color: 'rgba(234, 88, 12, 0.6)', label: 'Inde' },
          { color: 'rgba(75, 85, 99, 0.5)', label: 'Autre' },
        ];
      case 'tensions':
        return [
          { color: 'rgba(220, 38, 38, 0.8)', label: 'Critique (80%+)' },
          { color: 'rgba(234, 88, 12, 0.7)', label: 'Eleve (60-79%)' },
          { color: 'rgba(234, 179, 8, 0.6)', label: 'Modere (40-59%)' },
          { color: 'rgba(132, 204, 22, 0.5)', label: 'Faible (20-39%)' },
          { color: 'rgba(34, 197, 94, 0.4)', label: 'Stable (<20%)' },
        ];
      case 'resources':
        return [
          { color: 'rgba(234, 179, 8, 0.9)', label: 'Petrole + Strat. + Verrou' },
          { color: 'rgba(234, 179, 8, 0.7)', label: 'Petrole + Strategique' },
          { color: 'rgba(23, 23, 23, 0.75)', label: 'Petrole/Gaz' },
          { color: 'rgba(59, 130, 246, 0.6)', label: 'Minerais strategiques' },
          { color: 'rgba(168, 85, 247, 0.6)', label: 'Verrou maritime' },
        ];
      case 'influence':
        return [
          { color: 'rgba(34, 197, 94, 0.8)', label: 'Hegemonie (80%+)' },
          { color: 'rgba(132, 204, 22, 0.65)', label: 'Forte (60-79%)' },
          { color: 'rgba(234, 179, 8, 0.55)', label: 'Significative (40-59%)' },
          { color: 'rgba(249, 115, 22, 0.45)', label: 'Presence (20-39%)' },
          { color: 'rgba(75, 85, 99, 0.25)', label: 'Marginale (<20%)' },
        ];
      default:
        return [];
    }
  }, [viewMode]);

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-900/50 to-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <span className="text-sm">&#127758;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Carte Mondiale</span>
            <div className="text-xs text-gray-400">
              {zones.length} zones | Cliquez pour details
            </div>
          </div>
        </div>

        {/* View mode selector */}
        <div className="flex gap-1">
          {([
            { key: 'dominant', label: 'Dominance', icon: '&#127760;' },
            { key: 'tensions', label: 'Tensions', icon: '&#9888;' },
            { key: 'resources', label: 'Ressources', icon: '&#9981;' },
            { key: 'influence', label: 'Influence', icon: '&#128200;' },
          ] as const).map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setViewMode(key)}
              className={`px-2 py-1 text-xs rounded transition-all flex items-center gap-1 ${
                viewMode === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
              }`}
            >
              <span dangerouslySetInnerHTML={{ __html: icon }} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Map container */}
      <div className="relative bg-gray-900 p-4">
        {/* SVG Map */}
        <div className="relative w-full" style={{ paddingBottom: '50%' }}>
          <svg
            viewBox="0 0 100 85"
            className="absolute inset-0 w-full h-full"
            style={{ background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)' }}
          >
            {/* Grid lines */}
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(75, 85, 99, 0.2)" strokeWidth="0.1"/>
              </pattern>
            </defs>
            <rect width="100" height="85" fill="url(#grid)" />

            {/* Zones */}
            {zones.map(zone => {
              const pos = ZONE_POSITIONS[zone.id];
              if (!pos) return null;

              return (
                <g key={zone.id}>
                  {/* Zone rectangle */}
                  <rect
                    x={pos.x}
                    y={pos.y}
                    width={pos.width}
                    height={pos.height}
                    rx={1}
                    fill={getZoneColor(zone)}
                    style={{
                      border: getZoneBorder(zone),
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    stroke={
                      selectedZoneId === zone.id ? '#a855f7' :
                      hoveredZone === zone.id ? '#60a5fa' :
                      zone.contested_by.length > 0 ? 'rgba(234, 179, 8, 0.5)' :
                      'rgba(75, 85, 99, 0.3)'
                    }
                    strokeWidth={selectedZoneId === zone.id ? 0.5 : 0.2}
                    strokeDasharray={zone.contested_by.length > 0 && selectedZoneId !== zone.id ? '1,1' : 'none'}
                    onClick={() => onZoneClick?.(zone)}
                    onMouseEnter={() => setHoveredZone(zone.id)}
                    onMouseLeave={() => setHoveredZone(null)}
                  />

                  {/* Zone label */}
                  <text
                    x={pos.x + pos.width / 2}
                    y={pos.y + pos.height / 2}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize={pos.width > 12 ? 2 : 1.5}
                    fill="white"
                    style={{ pointerEvents: 'none', fontWeight: 500 }}
                  >
                    {ZONE_LABELS[zone.id]?.substring(0, 12) || zone.id}
                  </text>

                  {/* Dominant power flag */}
                  {zone.dominant_power && (
                    <text
                      x={pos.x + pos.width - 1.5}
                      y={pos.y + 2}
                      fontSize={2.5}
                      style={{ pointerEvents: 'none' }}
                    >
                      {COUNTRY_FLAGS[zone.dominant_power] || ''}
                    </text>
                  )}

                  {/* Oil indicator */}
                  {zone.has_oil && (
                    <text
                      x={pos.x + 1}
                      y={pos.y + 2}
                      fontSize={1.5}
                      style={{ pointerEvents: 'none' }}
                    >
                      &#9981;
                    </text>
                  )}

                  {/* Active conflict indicator - pulsing for hot zones */}
                  {(() => {
                    const strategicInfo = ZONE_STRATEGIC_INFO[zone.id];
                    const hasActiveConflict = strategicInfo && strategicInfo.conflicts.length > 0;
                    const isCritical = strategicInfo && strategicInfo.tensions >= 80;

                    if (hasActiveConflict) {
                      return (
                        <g>
                          {/* Conflict marker */}
                          <text
                            x={pos.x + pos.width / 2}
                            y={pos.y + pos.height - 1.5}
                            textAnchor="middle"
                            fontSize={isCritical ? 2.5 : 2}
                            fill={isCritical ? '#ef4444' : '#fbbf24'}
                            style={{ pointerEvents: 'none' }}
                            className={isCritical ? 'animate-pulse' : ''}
                          >
                            {isCritical ? '&#9876;' : '&#9888;'}
                          </text>
                          {/* Red border for critical zones */}
                          {isCritical && (
                            <rect
                              x={pos.x - 0.3}
                              y={pos.y - 0.3}
                              width={pos.width + 0.6}
                              height={pos.height + 0.6}
                              rx={1.5}
                              fill="none"
                              stroke="#ef4444"
                              strokeWidth={0.3}
                              strokeDasharray="1,0.5"
                              style={{ pointerEvents: 'none' }}
                            />
                          )}
                        </g>
                      );
                    }
                    return null;
                  })()}
                </g>
              );
            })}
          </svg>
        </div>

        {/* Enhanced tooltip with real geopolitical data */}
        {hoveredZone && (
          <div className="absolute top-4 left-4 bg-gray-800/95 border border-gray-600 rounded-lg p-3 shadow-xl z-10 min-w-64 max-w-80">
            {(() => {
              const zone = zones.find(z => z.id === hoveredZone);
              const strategicInfo = ZONE_STRATEGIC_INFO[hoveredZone];
              if (!zone) return null;
              return (
                <>
                  <div className="font-bold mb-2 text-sm border-b border-gray-700 pb-2">
                    {zone.name_fr}
                    {strategicInfo && strategicInfo.tensions >= 70 && (
                      <span className="ml-2 px-1.5 py-0.5 bg-red-600/80 rounded text-xs animate-pulse">
                        Zone chaude
                      </span>
                    )}
                  </div>

                  <div className="text-xs space-y-2 text-gray-400">
                    {/* Dominant Power & Contest */}
                    <div className="flex justify-between items-center">
                      <span>Puissance dominante:</span>
                      <span className="text-white font-medium">
                        {zone.dominant_power ? (
                          <>{COUNTRY_FLAGS[zone.dominant_power]} {zone.dominant_power}</>
                        ) : 'Contestee'}
                      </span>
                    </div>

                    {zone.contested_by.length > 0 && (
                      <div className="flex justify-between items-center">
                        <span>Contestee par:</span>
                        <span className="text-yellow-400">
                          {zone.contested_by.map(c => `${COUNTRY_FLAGS[c] || ''} ${c}`).join(', ')}
                        </span>
                      </div>
                    )}

                    {/* Tension Level with color bar */}
                    {strategicInfo && (
                      <div className="mt-2">
                        <div className="flex justify-between mb-1">
                          <span>Niveau de tension:</span>
                          <span className={
                            strategicInfo.tensions >= 80 ? 'text-red-400' :
                            strategicInfo.tensions >= 60 ? 'text-orange-400' :
                            strategicInfo.tensions >= 40 ? 'text-yellow-400' :
                            'text-green-400'
                          }>{strategicInfo.tensions}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-gray-700 rounded overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              strategicInfo.tensions >= 80 ? 'bg-red-500' :
                              strategicInfo.tensions >= 60 ? 'bg-orange-500' :
                              strategicInfo.tensions >= 40 ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${strategicInfo.tensions}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Active Conflicts */}
                    {strategicInfo && strategicInfo.conflicts.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-700">
                        <div className="text-red-400 font-medium mb-1">Conflits actifs:</div>
                        <div className="flex flex-wrap gap-1">
                          {strategicInfo.conflicts.map((conflict, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-red-900/40 rounded text-red-300 text-xs">
                              {conflict}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Military Bases */}
                    {strategicInfo && strategicInfo.militaryBases.filter(b => b.count > 0).length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-700">
                        <div className="text-blue-400 font-medium mb-1">Bases militaires:</div>
                        <div className="flex flex-wrap gap-2">
                          {strategicInfo.militaryBases.filter(b => b.count > 0).map((base, i) => (
                            <span key={i} className="flex items-center gap-1">
                              {COUNTRY_FLAGS[base.power] || base.power}
                              <span className="text-white">{base.count}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Strategic Assets */}
                    {strategicInfo && strategicInfo.strategicAssets.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-700">
                        <div className="text-cyan-400 font-medium mb-1">Enjeux strategiques:</div>
                        <div className="flex flex-wrap gap-1">
                          {strategicInfo.strategicAssets.map((asset, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-cyan-900/40 rounded text-cyan-300 text-xs">
                              {asset}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Resources */}
                    <div className="flex gap-2 mt-2 pt-2 border-t border-gray-700">
                      {zone.has_oil && (
                        <span className="px-1.5 py-0.5 bg-yellow-900/50 rounded text-yellow-300 flex items-center gap-1">
                          <span>&#9981;</span> Petrole
                        </span>
                      )}
                      {zone.has_strategic_resources && (
                        <span className="px-1.5 py-0.5 bg-blue-900/50 rounded text-blue-300 flex items-center gap-1">
                          <span>&#9878;</span> Ressources
                        </span>
                      )}
                      {zone.former_colonial_power && (
                        <span className="px-1.5 py-0.5 bg-gray-700/50 rounded text-gray-300">
                          Ex-{COUNTRY_FLAGS[zone.former_colonial_power] || zone.former_colonial_power}
                        </span>
                      )}
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-gray-800/90 border border-gray-700 rounded-lg p-2">
          <div className="text-xs font-medium mb-1 text-gray-400">Legende</div>
          <div className="space-y-1">
            {legendItems.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <div
                  className="w-4 h-3 rounded"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-gray-300">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
