/**
 * Shared styling utilities for Historia-lite
 *
 * Centralizes common styling configurations to avoid duplication.
 */

// =============================================================================
// RISK LEVEL STYLING
// =============================================================================

export interface RiskStyle {
  color: string;
  bgColor: string;
  label: string;
}

export const RISK_STYLES: Record<string, RiskStyle> = {
  low: {
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    label: "FAIBLE",
  },
  medium: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    label: "MOYEN",
  },
  high: {
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    label: "ELEVE",
  },
  extreme: {
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    label: "EXTREME",
  },
  critical: {
    color: "text-red-500",
    bgColor: "bg-red-600/20",
    label: "CRITIQUE",
  },
};

export function getRiskStyle(riskLevel: string): RiskStyle {
  return RISK_STYLES[riskLevel] || RISK_STYLES.low;
}

// =============================================================================
// ACTION CATEGORY STYLING
// =============================================================================

export interface CategoryStyle {
  icon: string;
  color: string;
}

export const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  DIPLO: { icon: "\uD83E\uDD1D", color: "text-blue-400" },
  MIL: { icon: "\u2694\uFE0F", color: "text-red-400" },
  COV: { icon: "\uD83D\uDD75\uFE0F", color: "text-purple-400" },
  INTEL: { icon: "\uD83D\uDD0D", color: "text-cyan-400" },
  ECO: { icon: "\uD83D\uDCB0", color: "text-green-400" },
  DOM: { icon: "\uD83C\uDFDB\uFE0F", color: "text-amber-400" },
  GEN: { icon: "\u2696\uFE0F", color: "text-slate-400" },
};

export function getCategoryStyle(category: string): CategoryStyle {
  return CATEGORY_STYLES[category] || CATEGORY_STYLES.GEN;
}

// =============================================================================
// TENSION BAND STYLING
// =============================================================================

export interface TensionStyle {
  border: string;
  bg: string;
  text: string;
}

export const TENSION_STYLES: Record<string, TensionStyle> = {
  low: {
    border: "border-slate-700",
    bg: "bg-slate-900/30",
    text: "text-slate-400",
  },
  medium: {
    border: "border-yellow-500/30",
    bg: "bg-yellow-950/20",
    text: "text-yellow-400",
  },
  high: {
    border: "border-orange-500/50",
    bg: "bg-orange-950/30",
    text: "text-orange-400",
  },
  critical: {
    border: "border-red-500/70",
    bg: "bg-red-950/40",
    text: "text-red-400",
  },
};

export function getTensionStyle(tension: string): TensionStyle {
  return TENSION_STYLES[tension] || TENSION_STYLES.low;
}
