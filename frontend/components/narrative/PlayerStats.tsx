"use client";

/**
 * PlayerStats - Cold War Status Panel
 *
 * Displays player statistics with military-style gauges
 */

import React from "react";

interface PlayerState {
  political_capital: number;
  domestic_stability: number;
  international_reputation: number;
  intel_exposure: number;
  action_capacity?: number;
  available_capital?: number;
}

interface PlayerStatsProps {
  player: PlayerState;
}

export default function PlayerStats({ player }: PlayerStatsProps) {
  return (
    <div className="bg-[#0d1420] border border-cyan-900/30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 border-b border-cyan-900/30 bg-[#0a0e17]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-gradient-to-r from-blue-600 via-white to-red-600 rounded-sm" />
          <span className="text-xs font-mono tracking-wider text-slate-400 uppercase">
            Etats-Unis d'Amerique
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="p-4 space-y-4">
        {/* Political Capital - Main Resource */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">
              Capital Politique
            </span>
            <span className="text-lg font-mono font-bold text-cyan-400">
              {player.available_capital ?? player.political_capital}
              {player.available_capital !== undefined && player.available_capital !== player.political_capital && (
                <span className="text-xs text-slate-500 ml-1">/ {player.political_capital}</span>
              )}
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 transition-all duration-500"
              style={{ width: `${player.political_capital}%` }}
            />
          </div>
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-2 gap-3">
          {/* Domestic Stability */}
          <StatGauge
            label="Stabilite"
            value={player.domestic_stability}
            color={getStabilityColor(player.domestic_stability)}
            warning={player.domestic_stability < 30}
          />

          {/* International Reputation */}
          <StatGauge
            label="Reputation"
            value={player.international_reputation}
            color={getReputationColor(player.international_reputation)}
          />
        </div>

        {/* Action Capacity */}
        {player.action_capacity && (
          <div className="pt-3 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-600 uppercase">
                Capacite d'action
              </span>
              <span className="text-sm font-mono text-slate-400">
                {player.action_capacity} max
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Warnings */}
      {(player.domestic_stability < 30 || player.political_capital < 20) && (
        <div className="px-4 py-2 border-t border-red-900/30 bg-red-500/5">
          {player.domestic_stability < 30 && (
            <div className="flex items-center gap-2 text-xs text-red-400 font-mono">
              <span className="animate-pulse">!</span>
              <span>ALERTE: Instabilite critique</span>
            </div>
          )}
          {player.political_capital < 20 && (
            <div className="flex items-center gap-2 text-xs text-amber-400 font-mono">
              <span className="animate-pulse">!</span>
              <span>Capital politique faible</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatGauge({
  label,
  value,
  color,
  warning = false
}: {
  label: string;
  value: number;
  color: string;
  warning?: boolean;
}) {
  return (
    <div className={warning ? "animate-pulse" : ""}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-mono text-slate-600">{label}</span>
        <span className={`text-xs font-mono ${color}`}>{value}%</span>
      </div>
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${color.replace("text-", "bg-")}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function getStabilityColor(value: number): string {
  if (value >= 60) return "text-green-500";
  if (value >= 30) return "text-yellow-500";
  return "text-red-500";
}

function getReputationColor(value: number): string {
  if (value >= 60) return "text-blue-400";
  if (value >= 30) return "text-yellow-500";
  return "text-red-500";
}
