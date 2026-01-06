"use client";

/**
 * CostBreakdown - Dynamic Cost Display
 *
 * Shows why an action costs what it does.
 * Attacking China is NOT the same as influencing Belgium!
 */

import React, { useState } from "react";

// =============================================================================
// TYPES
// =============================================================================

interface CostMultiplier {
  label: string;
  value: number;
  explanation?: string;
  type: "increase" | "decrease" | "neutral";
}

interface CostBreakdownData {
  baseCost: number;
  finalCost: number;
  multipliers: CostMultiplier[];
  risk: "low" | "medium" | "high" | "extreme";
  warnings?: string[];
}

// =============================================================================
// COST CALCULATION (Frontend estimation - mirrors backend logic)
// =============================================================================

// Strategic value multipliers
const STRATEGIC_MULTIPLIERS: Record<number, number> = {
  1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0,
  6: 1.1, 7: 1.25, 8: 1.4, 9: 1.6, 10: 2.0,
};

// DEFCON multipliers
const DEFCON_MULTIPLIERS: Record<number, number> = {
  5: 0.85, 4: 1.0, 3: 1.15, 2: 1.4, 1: 1.8,
};

// Base costs by action type
const BASE_COSTS: Record<string, number> = {
  DIPLO_ALLIANCE: 8, DIPLO_THREAT: 12, DIPLO_NEGOTIATE: 6,
  DIPLO_CONCEDE: 4, DIPLO_SANCTION: 10, DIPLO_SUMMIT: 15, DIPLO_BACKCHANNEL: 8,
  MIL_REINFORCE: 18, MIL_WITHDRAW: 5, MIL_DEMO: 20,
  MIL_PROXY: 25, MIL_BLOCKADE: 30, MIL_BASE: 35,
  COV_DESTAB: 15, COV_COUP: 40, COV_SABOTAGE: 20,
  COV_ASSASSIN: 50, COV_PROPAGANDA: 10,
  INTEL_COLLECT: 5, INTEL_VERIFY: 3, INTEL_COUNTER: 8, INTEL_DISINFO: 12,
  ECO_AID: 12, ECO_TRADE: 8, ECO_EMBARGO: 15, ECO_INVEST: 20,
  DOM_SPEECH: 3, DOM_REFORM: 10, DOM_REPRESS: 8, DOM_ELECTION: 12,
};

// Category multipliers
const CATEGORY_MULTIPLIERS: Record<string, number> = {
  DIPLO: 1.0, MIL: 1.4, COV: 1.3, INTEL: 0.9, ECO: 1.1, DOM: 0.7,
};

// =============================================================================
// DYNAMIC IMPORTANCE CALCULATION (Option 4 - mirrors backend logic)
// =============================================================================

interface ZoneData {
  id?: string;
  strategic_value?: number;
  control_us?: number;
  control_ussr?: number;
  stability?: number;
  has_crisis?: boolean;
  crisis_intensity?: number;
}

/**
 * Calculate effective importance based on context.
 * Cuba 1959 = Tier 4, Cuba 1962 (missiles) = Tier 1!
 */
export function calculateEffectiveImportance(zone: ZoneData): number {
  let importance = zone.strategic_value || 5;

  // Crisis active = high importance (+1 to +5)
  if (zone.has_crisis) {
    const crisisBonus = Math.floor((zone.crisis_intensity || 0) / 20);
    importance = Math.min(10, importance + crisisBonus);
  }

  // Unstable zone = more risk = more important (+1)
  if ((zone.stability || 50) < 30) {
    importance = Math.min(10, importance + 1);
  }

  // Contested (close to 50/50) = strategic (+1)
  const controlDiff = Math.abs((zone.control_us || 50) - (zone.control_ussr || 50));
  if (controlDiff < 20) {
    importance = Math.min(10, importance + 1);
  }

  return importance;
}

export function estimateCost(
  intentionType: string,
  zone: ZoneData | null,
  defcon: number,
  worldTension: number
): CostBreakdownData {
  const multipliers: CostMultiplier[] = [];
  const baseCost = BASE_COSTS[intentionType] || 15;

  // Category multiplier
  const category = intentionType.split("_")[0];
  const categoryMult = CATEGORY_MULTIPLIERS[category] || 1.0;
  if (categoryMult !== 1.0) {
    multipliers.push({
      label: `Type ${category}`,
      value: categoryMult,
      type: categoryMult > 1 ? "increase" : "decrease",
    });
  }

  // Zone multipliers
  let zoneMult = 1.0;
  if (zone) {
    // Strategic value - USE DYNAMIC IMPORTANCE (Option 4)
    const baseValue = zone.strategic_value || 5;
    const effectiveValue = calculateEffectiveImportance(zone);
    const stratMult = STRATEGIC_MULTIPLIERS[effectiveValue] || 1.0;

    if (stratMult !== 1.0) {
      zoneMult *= stratMult;

      // Show dynamic change if different from base
      if (effectiveValue !== baseValue) {
        multipliers.push({
          label: "Importance dynamique",
          value: stratMult,
          explanation: `${baseValue}→${effectiveValue}/10`,
          type: stratMult > 1 ? "increase" : "decrease",
        });
      } else {
        multipliers.push({
          label: effectiveValue >= 7 ? "Zone strategique" : "Zone secondaire",
          value: stratMult,
          explanation: `Valeur: ${effectiveValue}/10`,
          type: stratMult > 1 ? "increase" : "decrease",
        });
      }
    }

    // Control situation
    const ourControl = zone.control_us || 50;
    const theirControl = zone.control_ussr || 50;
    if (ourControl >= 70) {
      zoneMult *= 0.7;
      multipliers.push({
        label: "Territoire controle",
        value: 0.7,
        type: "decrease",
      });
    } else if (theirControl >= 70) {
      zoneMult *= 1.5;
      multipliers.push({
        label: "Territoire hostile",
        value: 1.5,
        explanation: "Zone sous controle adverse",
        type: "increase",
      });
    } else if (theirControl >= 50) {
      zoneMult *= 1.25;
      multipliers.push({
        label: "Position adverse forte",
        value: 1.25,
        type: "increase",
      });
    }

    // Stability
    const stability = zone.stability || 50;
    if (stability < 30) {
      zoneMult *= 1.3;
      multipliers.push({
        label: "Zone instable",
        value: 1.3,
        explanation: "Imprevisible",
        type: "increase",
      });
    } else if (stability > 80) {
      zoneMult *= 0.9;
      multipliers.push({
        label: "Zone stable",
        value: 0.9,
        type: "decrease",
      });
    }
  }

  // DEFCON multiplier
  const defconMult = DEFCON_MULTIPLIERS[defcon] || 1.0;
  if (defcon <= 2) {
    multipliers.push({
      label: `DEFCON ${defcon}`,
      value: defconMult,
      explanation: "Crise nucleaire",
      type: "increase",
    });
  } else if (defcon === 5) {
    multipliers.push({
      label: "DEFCON 5",
      value: defconMult,
      explanation: "Periode de paix",
      type: "decrease",
    });
  }

  // Tension multiplier
  let tensionMult = 1.0;
  if (worldTension >= 80) {
    tensionMult = 1.3;
    multipliers.push({
      label: "Tension critique",
      value: 1.3,
      type: "increase",
    });
  } else if (worldTension >= 60) {
    tensionMult = 1.15;
    multipliers.push({
      label: "Tension elevee",
      value: 1.15,
      type: "increase",
    });
  } else if (worldTension <= 25) {
    tensionMult = 0.85;
    multipliers.push({
      label: "Tension basse",
      value: 0.85,
      type: "decrease",
    });
  }

  // Calculate final cost
  const totalMult = categoryMult * zoneMult * defconMult * tensionMult;
  const finalCost = Math.max(1, Math.round(baseCost * totalMult));

  // Determine risk
  let risk: "low" | "medium" | "high" | "extreme" = "medium";
  const isCovert = category === "COV";
  const isMilitary = category === "MIL";
  if (isCovert || ["MIL_BLOCKADE", "COV_COUP", "COV_ASSASSIN"].includes(intentionType)) {
    risk = "extreme";
  } else if (isMilitary || defcon <= 2) {
    risk = "high";
  } else if (worldTension >= 60) {
    risk = "high";
  } else if (category === "DIPLO" || category === "DOM") {
    risk = "low";
  }

  // Warnings
  const warnings: string[] = [];
  if (defcon <= 2) warnings.push("DEFCON critique - risque d'escalade");
  if (zone && (zone.control_ussr || 0) >= 70) warnings.push("Zone sous controle adverse");
  if (["COV_COUP", "COV_ASSASSIN", "MIL_BLOCKADE"].includes(intentionType)) {
    warnings.push("Operation tres risquee");
  }

  return { baseCost, finalCost, multipliers, risk, warnings };
}

// =============================================================================
// COMPONENT
// =============================================================================

interface CostBreakdownProps {
  breakdown: CostBreakdownData;
  compact?: boolean;
}

export function CostBreakdown({ breakdown, compact = false }: CostBreakdownProps) {
  const [expanded, setExpanded] = useState(false);

  const riskColors = {
    low: "text-green-400",
    medium: "text-yellow-400",
    high: "text-orange-400",
    extreme: "text-red-400",
  };

  const riskLabels = {
    low: "FAIBLE",
    medium: "MOYEN",
    high: "ELEVE",
    extreme: "EXTREME",
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-mono text-amber-400">
          {breakdown.finalCost} PTS
        </span>
        {breakdown.finalCost !== breakdown.baseCost && (
          <span className="text-[9px] font-mono text-slate-600 line-through">
            {breakdown.baseCost}
          </span>
        )}
        <span className={`text-[10px] font-mono ${riskColors[breakdown.risk]}`}>
          {riskLabels[breakdown.risk]}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[#080c14] border border-slate-800 rounded-md p-3">
      {/* Header - Click to expand */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-mono text-amber-400 font-bold">
            {breakdown.finalCost} PTS
          </span>
          {breakdown.finalCost !== breakdown.baseCost && (
            <span className="text-xs font-mono text-slate-600">
              (base: {breakdown.baseCost})
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono ${riskColors[breakdown.risk]}`}>
            RISQUE: {riskLabels[breakdown.risk]}
          </span>
          <svg
            className={`w-4 h-4 text-slate-500 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">
            Detail du cout
          </div>

          {/* Multipliers list */}
          <div className="space-y-1.5">
            {breakdown.multipliers.map((mult, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] ${
                    mult.type === "increase" ? "text-red-400" :
                    mult.type === "decrease" ? "text-green-400" :
                    "text-slate-400"
                  }`}>
                    {mult.type === "increase" ? "▲" : mult.type === "decrease" ? "▼" : "●"}
                  </span>
                  <span className="text-xs text-slate-400">{mult.label}</span>
                  {mult.explanation && (
                    <span className="text-[10px] text-slate-600">({mult.explanation})</span>
                  )}
                </div>
                <span className={`text-xs font-mono ${
                  mult.value > 1 ? "text-red-400" : mult.value < 1 ? "text-green-400" : "text-slate-400"
                }`}>
                  x{mult.value.toFixed(2)}
                </span>
              </div>
            ))}
          </div>

          {/* Warnings */}
          {breakdown.warnings && breakdown.warnings.length > 0 && (
            <div className="mt-3 pt-2 border-t border-slate-800">
              {breakdown.warnings.map((warning, idx) => (
                <div key={idx} className="flex items-center gap-2 text-[10px] text-orange-400">
                  <span>⚠</span>
                  <span>{warning}</span>
                </div>
              ))}
            </div>
          )}

          {/* Calculation */}
          <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-600">
            {breakdown.baseCost} × {(breakdown.finalCost / breakdown.baseCost).toFixed(2)} = {breakdown.finalCost}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// COST PREVIEW (for showing before action is taken)
// =============================================================================

interface CostPreviewProps {
  intentionType: string;
  zone: (ZoneData & { name_fr?: string }) | null;
  defcon: number;
  worldTension: number;
}

export function CostPreview({ intentionType, zone, defcon, worldTension }: CostPreviewProps) {
  const breakdown = estimateCost(intentionType, zone, defcon, worldTension);

  return (
    <div className="bg-[#0d1420] border border-cyan-900/30 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-mono text-cyan-400/70 uppercase tracking-wider">
          Estimation du cout
        </span>
        {zone?.name_fr && (
          <span className="text-[10px] font-mono text-slate-500">
            {zone.name_fr}
          </span>
        )}
      </div>

      <CostBreakdown breakdown={breakdown} />
    </div>
  );
}

export default CostBreakdown;
