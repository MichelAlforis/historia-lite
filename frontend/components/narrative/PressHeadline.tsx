"use client";

/**
 * PressHeadline - Depeche de Presse
 *
 * Affiche un titre de presse d'une des 40+ sources avec leur biais editorial.
 * Le biais influence la presentation (pro_west, pro_east, neutral).
 */

import React from "react";

// =============================================================================
// TYPES
// =============================================================================

interface PressHeadlineData {
  source: string;
  source_id: string;
  headline: string;
  excerpt: string;
  sentiment: "positive" | "negative" | "neutral";
  bias: string;
  country: string;
  credibility: string;
}

interface PressHeadlineProps {
  headline: PressHeadlineData;
}

// =============================================================================
// BIAS STYLES
// =============================================================================

const BIAS_STYLES: Record<string, { border: string; bg: string; source: string }> = {
  pro_west: {
    border: "border-blue-800/40",
    bg: "bg-blue-950/20",
    source: "text-blue-400",
  },
  pro_east: {
    border: "border-red-800/40",
    bg: "bg-red-950/20",
    source: "text-red-400",
  },
  neutral: {
    border: "border-slate-700/40",
    bg: "bg-slate-900/30",
    source: "text-slate-400",
  },
  nationalist: {
    border: "border-amber-800/40",
    bg: "bg-amber-950/20",
    source: "text-amber-400",
  },
  pan_african: {
    border: "border-green-800/40",
    bg: "bg-green-950/20",
    source: "text-green-400",
  },
  pan_arab: {
    border: "border-emerald-800/40",
    bg: "bg-emerald-950/20",
    source: "text-emerald-400",
  },
  anti_colonial: {
    border: "border-purple-800/40",
    bg: "bg-purple-950/20",
    source: "text-purple-400",
  },
};

// =============================================================================
// SENTIMENT INDICATORS
// =============================================================================

const SENTIMENT_ICONS: Record<string, { icon: string; color: string }> = {
  positive: { icon: "+", color: "text-green-400" },
  negative: { icon: "-", color: "text-red-400" },
  neutral: { icon: "=", color: "text-slate-500" },
};

// =============================================================================
// CREDIBILITY BADGES
// =============================================================================

const CREDIBILITY_BADGES: Record<string, string> = {
  high: "border-cyan-500/30 text-cyan-400",
  medium: "border-slate-500/30 text-slate-500",
  tabloid: "border-orange-500/30 text-orange-400",
  state: "border-red-500/30 text-red-400",
};

// =============================================================================
// COMPONENT
// =============================================================================

export function PressHeadline({ headline }: PressHeadlineProps) {
  const biasStyle = BIAS_STYLES[headline.bias] || BIAS_STYLES.neutral;
  const sentiment = SENTIMENT_ICONS[headline.sentiment] || SENTIMENT_ICONS.neutral;
  const credBadge = CREDIBILITY_BADGES[headline.credibility] || CREDIBILITY_BADGES.medium;

  return (
    <div className={`${biasStyle.bg} border ${biasStyle.border} rounded p-3`}>
      {/* Source Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* Source name */}
          <span className={`text-[11px] font-mono ${biasStyle.source} font-semibold`}>
            {headline.source}
          </span>

          {/* Country tag */}
          <span className="text-[9px] font-mono text-slate-600 uppercase">
            [{headline.country}]
          </span>

          {/* Credibility badge */}
          <span className={`text-[8px] font-mono border px-1 rounded ${credBadge}`}>
            {headline.credibility === "high" ? "FIABLE" :
             headline.credibility === "tabloid" ? "TABLOID" :
             headline.credibility === "state" ? "ETAT" : ""}
          </span>
        </div>

        {/* Sentiment indicator */}
        <span className={`text-xs font-bold ${sentiment.color}`}>
          {sentiment.icon}
        </span>
      </div>

      {/* Headline */}
      <h4 className="text-sm font-semibold text-slate-200 mb-1 leading-tight">
        {headline.headline}
      </h4>

      {/* Excerpt */}
      <p className="text-[11px] text-slate-400 leading-relaxed">
        {headline.excerpt}
      </p>

      {/* Bias indicator (subtle) */}
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[8px] font-mono text-slate-600 uppercase">
          {getBiasLabel(headline.bias)}
        </span>
      </div>
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function getBiasLabel(bias: string): string {
  const labels: Record<string, string> = {
    pro_west: "Orientation occidentale",
    pro_east: "Orientation sovietique",
    neutral: "Non-aligne",
    nationalist: "Nationaliste",
    pan_african: "Panafricain",
    pan_arab: "Panarabiste",
    anti_colonial: "Anti-colonial",
  };
  return labels[bias] || "";
}

export default PressHeadline;
