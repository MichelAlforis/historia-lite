"use client";

/**
 * IntelReport - Rapport de Renseignement
 *
 * Affiche un rapport classe avec style CIA/KGB authentique.
 * Classification, source type, fiabilite, et note d'analyste.
 */

import React from "react";

// =============================================================================
// TYPES
// =============================================================================

interface IntelReportData {
  classification: string;
  content: string;
  reliability: string;
  source_type: string;
  analyst_note?: string;
}

interface IntelReportProps {
  report: IntelReportData;
}

// =============================================================================
// CLASSIFICATION STYLES
// =============================================================================

const CLASSIFICATION_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  "TOP SECRET": {
    bg: "bg-red-950",
    text: "text-red-300",
    border: "border-red-700",
  },
  "TOP SECRET - EYES ONLY": {
    bg: "bg-red-950",
    text: "text-red-300",
    border: "border-red-700",
  },
  "SECRET": {
    bg: "bg-orange-950",
    text: "text-orange-300",
    border: "border-orange-700",
  },
  "CONFIDENTIAL": {
    bg: "bg-amber-950",
    text: "text-amber-300",
    border: "border-amber-700",
  },
  "RESTRICTED": {
    bg: "bg-slate-900",
    text: "text-slate-300",
    border: "border-slate-600",
  },
};

// =============================================================================
// SOURCE TYPE ICONS
// =============================================================================

const SOURCE_ICONS: Record<string, { icon: string; label: string }> = {
  humint: { icon: "HUM", label: "Source humaine" },
  sigint: { icon: "SIG", label: "Interception" },
  imagery: { icon: "IMG", label: "Imagerie" },
  osint: { icon: "OSI", label: "Source ouverte" },
};

// =============================================================================
// RELIABILITY INDICATORS
// =============================================================================

const RELIABILITY_STYLES: Record<string, { label: string; color: string }> = {
  certain: { label: "CERTAIN", color: "text-green-400 bg-green-500/20" },
  likely: { label: "PROBABLE", color: "text-cyan-400 bg-cyan-500/20" },
  uncertain: { label: "INCERTAIN", color: "text-amber-400 bg-amber-500/20" },
  rumor: { label: "RUMEUR", color: "text-red-400 bg-red-500/20" },
};

// =============================================================================
// COMPONENT
// =============================================================================

export function IntelReport({ report }: IntelReportProps) {
  const classStyle = CLASSIFICATION_STYLES[report.classification] ||
                     CLASSIFICATION_STYLES["CONFIDENTIAL"];
  const sourceInfo = SOURCE_ICONS[report.source_type] || SOURCE_ICONS.humint;
  const reliability = RELIABILITY_STYLES[report.reliability] || RELIABILITY_STYLES.uncertain;

  return (
    <div className={`${classStyle.bg} border ${classStyle.border} rounded-lg overflow-hidden`}>
      {/* Classification Banner */}
      <div className={`px-4 py-2 border-b ${classStyle.border} flex items-center justify-between`}>
        <span className={`text-[10px] font-mono font-bold tracking-widest ${classStyle.text}`}>
          {report.classification}
        </span>
        <div className="flex items-center gap-2">
          {/* Source type */}
          <span className="text-[9px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400">
            {sourceInfo.icon}
          </span>
          {/* Reliability */}
          <span className={`text-[9px] font-mono px-2 py-0.5 rounded ${reliability.color}`}>
            {reliability.label}
          </span>
        </div>
      </div>

      {/* Report Content */}
      <div className="p-4">
        <div className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
          {report.content}
        </div>

        {/* Analyst Note */}
        {report.analyst_note && (
          <div className="mt-4 pt-3 border-t border-slate-700">
            <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-1">
              Note de l'Analyste
            </div>
            <div className="text-[11px] text-cyan-400/80 italic font-mono">
              {report.analyst_note}
            </div>
          </div>
        )}
      </div>

      {/* Footer - Declassification notice */}
      <div className="px-4 py-2 bg-black/30 text-[8px] font-mono text-slate-600 text-center">
        DISTRIBUTION RESTREINTE - NEED TO KNOW BASIS
      </div>
    </div>
  );
}

export default IntelReport;
