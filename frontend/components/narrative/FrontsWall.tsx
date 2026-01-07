"use client";

/**
 * FrontsWall - Mur des Fronts Vivants (v2)
 *
 * Affiche les fronts actifs base sur les ACTIONS, pas les metriques.
 *
 * Chaque front montre:
 * - Beat: le dernier signe marquant (action loggee)
 * - Mode dominant: soft/hard/covert/standoff (deduit des actions recentes)
 * - Omen: signal faible avant la crise
 * - Badge: etiquette visuelle (CRISE, OPERATION, SOMMET, RUMEUR)
 *
 * Selection dynamique:
 * 1. Toujours: fronts en crise
 * 2. Fronts avec spotlight (action recente joueur/IA)
 * 3. Completer avec zones strategiques
 *
 * Le mur se rafraichit:
 * - A chaque tour
 * - Apres chaque beat du playback
 * - Apres un TEST choice
 */

import React, { useEffect, useState, useCallback } from "react";

// =============================================================================
// TYPES
// =============================================================================

export interface FrontBeat {
  kind: string;       // "speech", "troops", "covert_op", "leak", "summit", "riot"
  actor: string;      // "usa", "ussr", "local", "unknown"
  payload: string;    // Mini-phrase brute
  freshness: number;  // 0 = ce tour, 1 = tour precedent
}

export interface FrontState {
  zone_id: string;
  zone_name_fr: string;
  dominant_mode: string;      // "soft", "hard", "covert", "standoff"
  tension_band: string;       // "low", "medium", "high", "critical"
  spotlight: boolean;
  has_crisis: boolean;
  beat: FrontBeat | null;
  surface_phrase: string;
  omen: string | null;
  badge: string | null;
}

export interface FrontsResponse {
  fronts: FrontState[];
  count: number;
  turn: number;
  game_phase: string;
}

interface FrontsWallProps {
  className?: string;
  onFrontClick?: (front: FrontState) => void;
  maxDisplay?: number;
  compact?: boolean;
}

// =============================================================================
// API
// =============================================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchFronts(maxDisplay: number = 6): Promise<FrontsResponse> {
  const response = await fetch(
    `${API_BASE}/api/narrative/fronts?max_display=${maxDisplay}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch fronts: ${response.statusText}`);
  }
  return response.json();
}

// =============================================================================
// STYLING UTILITIES
// =============================================================================

const TENSION_COLORS: Record<string, string> = {
  low: "border-slate-700 bg-slate-900/30",
  medium: "border-yellow-500/30 bg-yellow-950/20",
  high: "border-orange-500/50 bg-orange-950/30",
  critical: "border-red-500/70 bg-red-950/40 animate-pulse",
};

const MODE_ICONS: Record<string, string> = {
  soft: "\uD83D\uDCF0",     // newspaper
  hard: "\uD83D\uDEE1\uFE0F",     // shield
  covert: "\uD83D\uDD75\uFE0F",   // detective
  standoff: "\u2696\uFE0F", // balance
};

const BADGE_STYLES: Record<string, string> = {
  CRISE: "bg-red-500/20 text-red-400",
  OPERATION: "bg-purple-500/20 text-purple-400",
  SOMMET: "bg-cyan-500/20 text-cyan-400",
  RUMEUR: "bg-amber-500/20 text-amber-400",
  DEPLOIEMENT: "bg-orange-500/20 text-orange-400",
  SANCTIONS: "bg-yellow-500/20 text-yellow-400",
  TENSIONS: "bg-pink-500/20 text-pink-400",
  FRAPPE: "bg-red-600/20 text-red-500",
};

// =============================================================================
// FRONT CARD COMPONENT
// =============================================================================

interface FrontCardProps {
  front: FrontState;
  isSelected?: boolean;
  onClick?: () => void;
  compact?: boolean;
}

function FrontCard({ front, isSelected, onClick, compact }: FrontCardProps) {
  const tensionClass = TENSION_COLORS[front.tension_band] || TENSION_COLORS.low;
  const modeIcon = MODE_ICONS[front.dominant_mode] || MODE_ICONS.standoff;
  const badgeStyle = front.badge ? BADGE_STYLES[front.badge] || "" : "";

  return (
    <div
      className={`
        ${compact ? "p-2" : "p-3"}
        border rounded cursor-pointer transition-all duration-300
        ${tensionClass}
        ${isSelected ? "ring-1 ring-cyan-500" : ""}
        ${front.spotlight ? "ring-1 ring-amber-500/50" : ""}
        hover:brightness-110
      `}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-2">
        <span
          className={`font-mono ${compact ? "text-[10px]" : "text-xs"} text-slate-300 font-semibold uppercase tracking-wide`}
        >
          {front.zone_name_fr}
        </span>
        <div className="flex items-center gap-2">
          <span title={front.dominant_mode} className="text-sm">
            {modeIcon}
          </span>
          {front.badge && (
            <span
              className={`text-[9px] px-1.5 py-0.5 rounded uppercase font-mono font-bold ${badgeStyle}`}
            >
              {front.badge}
            </span>
          )}
        </div>
      </div>

      {/* Surface phrase (generee depuis beat) */}
      <p
        className={`${compact ? "text-xs" : "text-sm"} text-slate-300 font-mono italic leading-snug`}
      >
        "{front.surface_phrase}"
      </p>

      {/* Beat info (optional, for debug/detail) */}
      {front.beat && !compact && (
        <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500">
          <span className="uppercase">{front.beat.actor}</span>
          <span>-</span>
          <span>{front.beat.kind}</span>
          {front.beat.freshness > 0 && (
            <span className="text-slate-600">
              (il y a {front.beat.freshness} tour{front.beat.freshness > 1 ? "s" : ""})
            </span>
          )}
        </div>
      )}

      {/* Omen (signal faible) */}
      {front.omen && (
        <p
          className={`${compact ? "text-[9px] mt-1" : "text-[10px] mt-2"} text-amber-500/70 font-mono uppercase tracking-wide`}
        >
          {"\u26A0"} {front.omen}
        </p>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function FrontsWall({
  className = "",
  onFrontClick,
  maxDisplay = 6,
  compact = false,
}: FrontsWallProps) {
  const [fronts, setFronts] = useState<FrontState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [turn, setTurn] = useState(0);

  const loadFronts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchFronts(maxDisplay);
      setFronts(data.fronts);
      setTurn(data.turn);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [maxDisplay]);

  useEffect(() => {
    loadFronts();
  }, [loadFronts]);

  const handleFrontClick = (front: FrontState) => {
    setSelectedZone(front.zone_id === selectedZone ? null : front.zone_id);
    onFrontClick?.(front);
  };

  // Refresh function exposed for parent components
  const refresh = useCallback(() => {
    loadFronts();
  }, [loadFronts]);

  // Expose refresh via ref or callback
  useEffect(() => {
    // Store refresh function in window for easy access from other components
    (window as unknown as { refreshFrontsWall?: () => void }).refreshFrontsWall = refresh;
    return () => {
      delete (window as unknown as { refreshFrontsWall?: () => void }).refreshFrontsWall;
    };
  }, [refresh]);

  if (loading && fronts.length === 0) {
    return (
      <div
        className={`${className} flex items-center justify-center text-slate-500 font-mono text-sm`}
      >
        Chargement des fronts...
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`${className} flex items-center justify-center text-red-500 font-mono text-sm`}
      >
        {error}
      </div>
    );
  }

  if (fronts.length === 0) {
    return (
      <div
        className={`${className} flex items-center justify-center text-slate-500 font-mono text-sm italic`}
      >
        Aucun front actif. Le monde est calme.
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-mono text-xs text-slate-400 uppercase tracking-widest">
          Fronts Mondiaux
        </h3>
        <span className="font-mono text-[10px] text-slate-600">
          Tour {turn}
        </span>
      </div>

      {/* Grid of fronts */}
      <div
        className={`grid gap-2 ${compact ? "grid-cols-2" : "grid-cols-1 md:grid-cols-2"}`}
      >
        {fronts.map((front) => (
          <FrontCard
            key={front.zone_id}
            front={front}
            isSelected={selectedZone === front.zone_id}
            onClick={() => handleFrontClick(front)}
            compact={compact}
          />
        ))}
      </div>

      {/* Refresh indicator */}
      {loading && (
        <div className="mt-2 text-center text-[10px] text-slate-600 font-mono animate-pulse">
          Mise a jour...
        </div>
      )}
    </div>
  );
}

// =============================================================================
// HOOK FOR MANUAL REFRESH
// =============================================================================

export function useFrontsRefresh() {
  const refresh = useCallback(() => {
    const refreshFn = (window as unknown as { refreshFrontsWall?: () => void }).refreshFrontsWall;
    if (refreshFn) {
      refreshFn();
    }
  }, []);

  return { refreshFronts: refresh };
}
