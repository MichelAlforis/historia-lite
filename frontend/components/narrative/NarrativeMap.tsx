"use client";

/**
 * NarrativeMap - Cold War Strategic Map
 *
 * Displays 12 geopolitical zones with influence visualization
 * Dark military aesthetic with glowing indicators
 */

import React from "react";

interface Zone {
  id: string;
  name_fr: string;
  influence_us: number;
  influence_ussr: number;
  control_us: number;
  stability: number;
  strategic_value: number;
  dominant: "US" | "USSR" | "contested";
  has_crisis: boolean;
}

interface NarrativeMapProps {
  zones: Record<string, Zone>;
  selectedZone?: string | null;
  onZoneClick?: (zoneId: string) => void;
}

// Zone positions (relative %)
const ZONE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  europe_west: { x: 44, y: 12, w: 11, h: 16 },
  europe_east: { x: 56, y: 10, w: 10, h: 18 },
  scandinavia: { x: 50, y: 2, w: 12, h: 12 },
  turkey_greece: { x: 58, y: 28, w: 9, h: 12 },
  middle_east: { x: 64, y: 35, w: 14, h: 18 },
  north_africa: { x: 40, y: 35, w: 20, h: 14 },
  sub_saharan_africa: { x: 46, y: 52, w: 16, h: 24 },
  south_asia: { x: 72, y: 40, w: 12, h: 18 },
  southeast_asia: { x: 80, y: 52, w: 12, h: 18 },
  far_east: { x: 82, y: 22, w: 14, h: 24 },
  central_america: { x: 16, y: 38, w: 14, h: 18 },
  south_america: { x: 22, y: 58, w: 18, h: 30 },
};

export default function NarrativeMap({
  zones,
  selectedZone,
  onZoneClick,
}: NarrativeMapProps) {
  return (
    <div className="relative w-full h-full bg-[#080c14] overflow-hidden">
      {/* Grid lines */}
      <div className="absolute inset-0 opacity-10">
        <div className="w-full h-full" style={{
          backgroundImage: `
            linear-gradient(to right, #0ea5e9 1px, transparent 1px),
            linear-gradient(to bottom, #0ea5e9 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px'
        }} />
      </div>

      {/* Continental outlines (simplified) */}
      <div className="absolute inset-0 opacity-20">
        <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
          {/* Americas */}
          <path d="M 15 20 Q 25 15, 30 25 L 32 45 Q 28 55, 35 90 L 20 85 Q 15 60, 18 40 Z"
                fill="none" stroke="#0ea5e9" strokeWidth="0.3" />
          {/* Europe/Africa */}
          <path d="M 42 10 L 55 8 Q 62 15, 58 30 L 65 50 Q 55 80, 45 75 L 40 35 Z"
                fill="none" stroke="#0ea5e9" strokeWidth="0.3" />
          {/* Asia */}
          <path d="M 58 5 Q 85 10, 95 30 L 90 60 Q 75 70, 65 50 L 62 25 Z"
                fill="none" stroke="#0ea5e9" strokeWidth="0.3" />
        </svg>
      </div>

      {/* Zone regions */}
      {Object.entries(ZONE_POSITIONS).map(([zoneId, pos]) => {
        const zone = zones[zoneId];
        if (!zone) return null;

        const isSelected = selectedZone === zoneId;
        const dominance = zone.influence_us - zone.influence_ussr;

        return (
          <button
            key={zoneId}
            onClick={() => onZoneClick?.(zoneId)}
            className={`
              absolute rounded-md transition-all duration-300 group
              ${isSelected ? "z-20" : "z-10"}
              ${zone.has_crisis ? "animate-pulse" : ""}
            `}
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              width: `${pos.w}%`,
              height: `${pos.h}%`,
            }}
          >
            {/* Zone Background */}
            <div className={`
              absolute inset-0 rounded-md transition-all duration-300
              ${getZoneBg(dominance)}
              ${isSelected ? "ring-2 ring-cyan-400" : ""}
              border ${zone.has_crisis ? "border-red-500" : "border-slate-700/50"}
              hover:border-cyan-500/50
            `} />

            {/* Content */}
            <div className="relative w-full h-full flex flex-col items-center justify-center p-1">
              {/* Zone Name */}
              <span className="text-[10px] font-mono text-white/90 text-center leading-tight truncate w-full drop-shadow-lg">
                {zone.name_fr}
              </span>

              {/* Influence Bar */}
              <div className="w-full mt-1 px-1">
                <div className="h-1.5 bg-slate-900 rounded-full flex overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${zone.influence_us}%` }}
                  />
                  <div
                    className="h-full bg-red-500 transition-all duration-500"
                    style={{ width: `${zone.influence_ussr}%` }}
                  />
                </div>
              </div>

              {/* Crisis indicator */}
              {zone.has_crisis && (
                <div className="absolute -top-1 -right-1">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-ping absolute" />
                  <div className="w-3 h-3 bg-red-500 rounded-full relative" />
                </div>
              )}

              {/* Instability indicator */}
              {zone.stability < 30 && !zone.has_crisis && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-500 rounded-full" />
              )}
            </div>

            {/* Hover Tooltip */}
            <div className={`
              absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2
              bg-slate-900/95 border border-slate-700 rounded-lg
              opacity-0 group-hover:opacity-100 transition-opacity duration-200
              pointer-events-none z-30 min-w-[140px]
              ${isSelected ? "opacity-100" : ""}
            `}>
              <div className="text-xs font-mono text-white font-bold mb-1">
                {zone.name_fr}
              </div>
              <div className="flex justify-between text-[10px] mb-0.5">
                <span className="text-blue-400">US</span>
                <span className="text-slate-400">{zone.influence_us}%</span>
              </div>
              <div className="flex justify-between text-[10px] mb-0.5">
                <span className="text-red-400">URSS</span>
                <span className="text-slate-400">{zone.influence_ussr}%</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-slate-500">Stabilite</span>
                <span className={zone.stability < 30 ? "text-red-400" : "text-slate-400"}>
                  {zone.stability}%
                </span>
              </div>
              {zone.has_crisis && (
                <div className="mt-1 pt-1 border-t border-slate-700 text-[10px] text-red-400 text-center">
                  CRISE ACTIVE
                </div>
              )}
            </div>
          </button>
        );
      })}

      {/* Legend */}
      <div className="absolute bottom-3 left-3 bg-slate-900/90 border border-slate-700 rounded-lg px-3 py-2">
        <div className="flex items-center gap-4 text-[10px] font-mono">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-1.5 bg-blue-500 rounded-full" />
            <span className="text-slate-400">US</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-1.5 bg-red-500 rounded-full" />
            <span className="text-slate-400">URSS</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-slate-400">Crise</span>
          </div>
        </div>
      </div>

      {/* Selected Zone Detail Panel */}
      {selectedZone && zones[selectedZone] && (
        <div className="absolute top-3 right-3 w-48 bg-slate-900/95 border border-cyan-900/50 rounded-lg overflow-hidden">
          <div className="px-3 py-2 border-b border-slate-800 bg-slate-900">
            <h4 className="text-xs font-mono font-bold text-cyan-400">
              {zones[selectedZone].name_fr}
            </h4>
          </div>
          <div className="p-3 space-y-2">
            <StatRow label="Influence US" value={zones[selectedZone].influence_us} color="text-blue-400" />
            <StatRow label="Influence URSS" value={zones[selectedZone].influence_ussr} color="text-red-400" />
            <StatRow label="Controle US" value={zones[selectedZone].control_us} color="text-slate-400" />
            <StatRow
              label="Stabilite"
              value={zones[selectedZone].stability}
              color={zones[selectedZone].stability < 30 ? "text-red-400" : "text-green-400"}
            />
            <div className="pt-2 border-t border-slate-800">
              <div className="flex justify-between text-[10px]">
                <span className="text-slate-500">Valeur strategique</span>
                <span className="text-amber-400">{zones[selectedZone].strategic_value}/10</span>
              </div>
            </div>
            {zones[selectedZone].has_crisis && (
              <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-center">
                <span className="text-xs font-mono text-red-400">CRISE EN COURS</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[10px] text-slate-500">{label}</span>
      <span className={`text-xs font-mono ${color}`}>{value}%</span>
    </div>
  );
}

function getZoneBg(dominance: number): string {
  if (dominance > 30) return "bg-blue-500/20";
  if (dominance > 10) return "bg-blue-500/10";
  if (dominance > -10) return "bg-slate-700/30";
  if (dominance > -30) return "bg-red-500/10";
  return "bg-red-500/20";
}
