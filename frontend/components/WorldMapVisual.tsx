'use client';

/**
 * WorldMapVisual - Historia-lite
 *
 * Carte avec systeme visuel emotionnel.
 * Design document: docs/VISUAL_DESIGN_ZONES.md
 *
 * Principe: Le joueur RESSENT avant de comprendre.
 * La carte EST le score.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { InfluenceZone, COUNTRY_FLAGS } from '@/lib/types';
import { useZoneHistoryStore } from '@/stores/zoneHistoryStore';
import {
  ZONE_COLORS,
  ZONE_TRANSITIONS,
  SVG_PATTERNS,
  getZoneVisualState,
  getZoneSVGStyles,
  ZoneVisualState,
  ZoneTransitionType,
} from '@/lib/zoneVisuals';

// =============================================================================
// TYPES & CONSTANTS
// =============================================================================

interface WorldMapVisualProps {
  zones: InfluenceZone[];
  playerPower?: string;
  onZoneClick?: (zone: InfluenceZone) => void;
  selectedZoneId?: string;
  currentTurn?: number;
}

// Zone positions (unchanged from WorldMap.tsx)
const ZONE_POSITIONS: Record<string, { x: number; y: number; width: number; height: number }> = {
  north_america: { x: 3, y: 12, width: 22, height: 22 },
  central_america: { x: 8, y: 36, width: 14, height: 12 },
  south_america: { x: 14, y: 50, width: 16, height: 32 },
  western_europe: { x: 40, y: 16, width: 12, height: 16 },
  eastern_europe: { x: 52, y: 14, width: 10, height: 16 },
  nordic: { x: 46, y: 6, width: 12, height: 10 },
  caucasus: { x: 56, y: 26, width: 8, height: 8 },
  central_asia: { x: 60, y: 22, width: 14, height: 12 },
  middle_east_gulf: { x: 54, y: 34, width: 14, height: 12 },
  levant: { x: 50, y: 30, width: 6, height: 10 },
  north_africa: { x: 38, y: 32, width: 16, height: 12 },
  west_africa: { x: 34, y: 44, width: 14, height: 16 },
  east_africa: { x: 50, y: 48, width: 12, height: 18 },
  southern_africa: { x: 46, y: 66, width: 14, height: 16 },
  south_asia: { x: 64, y: 34, width: 14, height: 16 },
  southeast_asia: { x: 74, y: 42, width: 14, height: 18 },
  east_asia: { x: 76, y: 20, width: 18, height: 20 },
  oceania: { x: 80, y: 62, width: 16, height: 18 },
  arctic: { x: 35, y: 1, width: 30, height: 6 },
};

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

// =============================================================================
// COMPONENT
// =============================================================================

export default function WorldMapVisual({
  zones,
  playerPower = 'USA',
  onZoneClick,
  selectedZoneId,
  currentTurn = 0,
}: WorldMapVisualProps) {
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);
  const [transitioningZone, setTransitioningZone] = useState<string | null>(null);
  const [worldDimmed, setWorldDimmed] = useState(false);

  // Zone history store
  const {
    setPlayerPower,
    updateZones,
    getZoneHistory,
    getZoneDegradation,
    consumeNextTransition,
    completeActiveTransition,
    activeTransition,
  } = useZoneHistoryStore();

  // Initialize player power
  useEffect(() => {
    setPlayerPower(playerPower);
  }, [playerPower, setPlayerPower]);

  // Update zone histories when zones change
  useEffect(() => {
    if (zones.length > 0) {
      updateZones(zones, currentTurn);
    }
  }, [zones, currentTurn, updateZones]);

  // Process pending transitions
  useEffect(() => {
    const processTransition = async () => {
      const transition = consumeNextTransition();
      if (!transition) return;

      setTransitioningZone(transition.zoneId);

      const config = ZONE_TRANSITIONS[transition.type as keyof typeof ZONE_TRANSITIONS];
      if (!config) {
        completeActiveTransition();
        setTransitioningZone(null);
        return;
      }

      // Historic gain: dim world, focus zone
      if (transition.type === 'historic_gain' && 'dimWorld' in config) {
        setWorldDimmed(true);
      }

      // Wait for transition duration
      const duration = 'duration' in config ? config.duration : 300;
      await new Promise(resolve => setTimeout(resolve, duration));

      // Restore world
      setWorldDimmed(false);
      setTransitioningZone(null);
      completeActiveTransition();
    };

    if (!activeTransition) {
      processTransition();
    }
  }, [activeTransition, consumeNextTransition, completeActiveTransition]);

  // Get visual state for a zone
  const getVisualState = useCallback((zone: InfluenceZone): ZoneVisualState => {
    const history = getZoneHistory(zone.id);
    return getZoneVisualState(zone, playerPower, history);
  }, [playerPower, getZoneHistory]);

  // Get fill color based on visual state
  const getZoneFill = useCallback((zone: InfluenceZone): string => {
    const state = getVisualState(zone);
    const degradation = getZoneDegradation(zone.id);
    const isTransitioning = transitioningZone === zone.id;

    // During historic transition, highlight
    if (isTransitioning && activeTransition?.type === 'historic_gain') {
      return 'rgba(59, 130, 246, 0.8)'; // Bright blue
    }

    // Degradation (perte insidieuse en cours)
    if (degradation > 0 && state === 'controlled') {
      return ZONE_COLORS.degradation[Math.min(degradation, 3)];
    }

    // Standard states
    switch (state) {
      case 'controlled':
        return ZONE_COLORS.controlled.fill;
      case 'adverse':
        return ZONE_COLORS.adverse.fill;
      case 'reconquered':
        return ZONE_COLORS.reconquered.fill;
      default:
        return zone.contested_by.length > 0
          ? ZONE_COLORS.contested.fill
          : ZONE_COLORS.neutral.fill;
    }
  }, [getVisualState, getZoneDegradation, transitioningZone, activeTransition]);

  // Get stroke style
  const getZoneStroke = useCallback((zone: InfluenceZone): { stroke: string; strokeWidth: number; strokeDasharray: string } => {
    const state = getVisualState(zone);
    const history = getZoneHistory(zone.id);
    const isSelected = selectedZoneId === zone.id;
    const isHovered = hoveredZone === zone.id;
    const isContested = zone.contested_by.length > 0;

    // Selection/hover override
    if (isSelected) {
      return { stroke: '#a855f7', strokeWidth: 0.5, strokeDasharray: 'none' };
    }
    if (isHovered) {
      return { stroke: '#60a5fa', strokeWidth: 0.3, strokeDasharray: 'none' };
    }

    // Contested zones: dashed border
    if (isContested && state !== 'controlled' && state !== 'reconquered') {
      return {
        stroke: ZONE_COLORS.contested.stroke,
        strokeWidth: 0.2,
        strokeDasharray: ZONE_COLORS.contested.strokeDasharray || '2,1',
      };
    }

    // Reconquered: thicker border (scar)
    if (state === 'reconquered' || history?.wasReconquered) {
      return {
        stroke: ZONE_COLORS.reconquered.stroke,
        strokeWidth: 0.4,
        strokeDasharray: 'none',
      };
    }

    // Standard states
    const colors = ZONE_COLORS[state] || ZONE_COLORS.neutral;
    return {
      stroke: colors.stroke,
      strokeWidth: 0.2,
      strokeDasharray: 'none',
    };
  }, [getVisualState, getZoneHistory, selectedZoneId, hoveredZone]);

  // CSS class for zone animation
  const getZoneClass = useCallback((zone: InfluenceZone): string => {
    const state = getVisualState(zone);
    const degradation = getZoneDegradation(zone.id);
    const isTransitioning = transitioningZone === zone.id;

    const classes: string[] = [];

    // Breathing animation for controlled zones
    if (state === 'controlled' || state === 'reconquered') {
      classes.push('zone-controlled');
    }

    // Trembling for degrading zones
    if (degradation > 0) {
      classes.push('zone-degrading');
    }

    // Transition animations
    if (isTransitioning && activeTransition) {
      if (activeTransition.type === 'brutal_loss') {
        classes.push('zone-brutal-loss');
      } else if (activeTransition.type === 'historic_gain') {
        classes.push('zone-historic-gain');
      }
    }

    return classes.join(' ');
  }, [getVisualState, getZoneDegradation, transitioningZone, activeTransition]);

  // Legend based on current state
  const legendItems = useMemo(() => [
    { color: ZONE_COLORS.controlled.fill, label: 'Sous controle' },
    { color: ZONE_COLORS.adverse.fill, label: 'Adversaire' },
    { color: ZONE_COLORS.contested.fill, label: 'Contestee' },
    { color: ZONE_COLORS.neutral.fill, label: 'Neutre' },
    { color: ZONE_COLORS.reconquered.fill, label: 'Reconquise', hasScar: true },
  ], []);

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-900/50 to-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <span className="text-sm">&#127758;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Situation Mondiale</span>
            <div className="text-xs text-gray-400">
              {zones.filter(z => z.dominant_power === playerPower).length} zones sous controle
            </div>
          </div>
        </div>
      </div>

      {/* Map container */}
      <div className={`relative bg-gray-900 p-4 transition-opacity duration-500 ${worldDimmed ? 'opacity-70' : 'opacity-100'}`}>
        {/* SVG Map */}
        <div className="relative w-full" style={{ paddingBottom: '50%' }}>
          <svg
            viewBox="0 0 100 85"
            className="absolute inset-0 w-full h-full"
            style={{ background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)' }}
          >
            {/* Definitions */}
            <defs>
              {/* Grid pattern */}
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(75, 85, 99, 0.2)" strokeWidth="0.1"/>
              </pattern>

              {/* Scar pattern for reconquered zones */}
              <pattern id="scar-pattern" patternUnits="userSpaceOnUse" width="4" height="4">
                <line x1="0" y1="4" x2="4" y2="0" stroke="rgba(127, 29, 29, 0.2)" strokeWidth="0.3"/>
              </pattern>

              {/* Breathing glow for controlled zones */}
              <filter id="breathing-glow">
                <feGaussianBlur stdDeviation="0.5" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Grid background */}
            <rect width="100" height="85" fill="url(#grid)" />

            {/* Zones */}
            {zones.map(zone => {
              const pos = ZONE_POSITIONS[zone.id];
              if (!pos) return null;

              const fill = getZoneFill(zone);
              const { stroke, strokeWidth, strokeDasharray } = getZoneStroke(zone);
              const cssClass = getZoneClass(zone);
              const state = getVisualState(zone);
              const history = getZoneHistory(zone.id);
              const hasScar = history?.wasReconquered === true;
              const isTransitioning = transitioningZone === zone.id;

              return (
                <g key={zone.id} className={cssClass}>
                  {/* Scar underlay for reconquered zones */}
                  {hasScar && (
                    <rect
                      x={pos.x}
                      y={pos.y}
                      width={pos.width}
                      height={pos.height}
                      rx={1}
                      fill="url(#scar-pattern)"
                      style={{ pointerEvents: 'none' }}
                    />
                  )}

                  {/* Main zone rectangle */}
                  <rect
                    x={pos.x}
                    y={pos.y}
                    width={pos.width}
                    height={pos.height}
                    rx={1}
                    fill={fill}
                    stroke={stroke}
                    strokeWidth={strokeWidth}
                    strokeDasharray={strokeDasharray}
                    style={{
                      cursor: 'pointer',
                      transition: isTransitioning ? 'none' : 'fill 0.3s ease, stroke 0.2s ease',
                    }}
                    filter={(state === 'controlled' || state === 'reconquered') ? 'url(#breathing-glow)' : 'none'}
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

                  {/* Dominant power indicator (small) */}
                  {zone.dominant_power && (
                    <text
                      x={pos.x + pos.width - 1.5}
                      y={pos.y + 2}
                      fontSize={2}
                      style={{ pointerEvents: 'none', opacity: 0.8 }}
                    >
                      {COUNTRY_FLAGS[zone.dominant_power] || ''}
                    </text>
                  )}

                  {/* Scar indicator for reconquered zones */}
                  {hasScar && (
                    <line
                      x1={pos.x + 1}
                      y1={pos.y + pos.height - 1}
                      x2={pos.x + 3}
                      y2={pos.y + pos.height - 1}
                      stroke="rgba(127, 29, 29, 0.6)"
                      strokeWidth={0.5}
                      style={{ pointerEvents: 'none' }}
                    />
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        {/* Tooltip */}
        {hoveredZone && (
          <div className="absolute top-4 left-4 bg-gray-800/95 border border-gray-600 rounded-lg p-3 shadow-xl z-10 min-w-48">
            {(() => {
              const zone = zones.find(z => z.id === hoveredZone);
              if (!zone) return null;
              const state = getVisualState(zone);
              const history = getZoneHistory(zone.id);

              return (
                <>
                  <div className="font-bold mb-2 text-sm border-b border-gray-700 pb-2">
                    {zone.name_fr}
                    {history?.wasReconquered && (
                      <span className="ml-2 px-1.5 py-0.5 bg-amber-900/50 rounded text-xs text-amber-300">
                        Reconquise
                      </span>
                    )}
                  </div>
                  <div className="text-xs space-y-1 text-gray-400">
                    <div className="flex justify-between">
                      <span>Statut:</span>
                      <span className={
                        state === 'controlled' ? 'text-blue-400' :
                        state === 'adverse' ? 'text-red-400' :
                        state === 'reconquered' ? 'text-amber-400' :
                        'text-gray-300'
                      }>
                        {state === 'controlled' ? 'Sous controle' :
                         state === 'adverse' ? 'Adversaire' :
                         state === 'reconquered' ? 'Reconquise' :
                         zone.contested_by.length > 0 ? 'Contestee' : 'Neutre'}
                      </span>
                    </div>
                    {zone.dominant_power && (
                      <div className="flex justify-between">
                        <span>Puissance:</span>
                        <span className="text-white">
                          {COUNTRY_FLAGS[zone.dominant_power]} {zone.dominant_power}
                        </span>
                      </div>
                    )}
                    {zone.contested_by.length > 0 && (
                      <div className="flex justify-between">
                        <span>Contestee par:</span>
                        <span className="text-yellow-400">
                          {zone.contested_by.map(c => COUNTRY_FLAGS[c] || c).join(' ')}
                        </span>
                      </div>
                    )}
                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-gray-800/90 border border-gray-700 rounded-lg p-2">
          <div className="text-xs font-medium mb-1 text-gray-400">Situation</div>
          <div className="space-y-1">
            {legendItems.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <div
                  className="w-4 h-3 rounded relative"
                  style={{ backgroundColor: item.color }}
                >
                  {item.hasScar && (
                    <div className="absolute inset-0 bg-gradient-to-br from-transparent via-red-900/20 to-transparent" />
                  )}
                </div>
                <span className="text-gray-300">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes zone-breathing {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.92; }
        }
        .zone-controlled rect:first-of-type {
          animation: zone-breathing 4s ease-in-out infinite;
        }
        @keyframes zone-trembling {
          0%, 100% { transform: translate(0, 0); }
          25% { transform: translate(0.1px, 0); }
          75% { transform: translate(-0.1px, 0); }
        }
        .zone-degrading {
          animation: zone-trembling 0.5s ease-in-out infinite;
        }
        @keyframes zone-brutal-loss {
          0% { fill: rgba(30, 58, 138, 0.65); }
          15% { fill: rgba(220, 38, 38, 0.8); }
          100% { fill: rgba(127, 29, 29, 0.65); }
        }
        .zone-brutal-loss rect:nth-of-type(2) {
          animation: zone-brutal-loss 0.8s ease-out;
        }
      `}</style>
    </div>
  );
}
