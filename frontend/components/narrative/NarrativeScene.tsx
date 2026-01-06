"use client";

/**
 * NarrativeScene - Le Composant Principal du Chef d'Orchestre
 *
 * Affiche une scene narrative complete composee par le backend.
 * Le joueur ne voit JAMAIS de metriques, juste une histoire.
 *
 * Elements:
 * - Recit narratif principal
 * - Dialogue de leader (optionnel)
 * - Titres de presse multiples (optionnel)
 * - Rapport intel (optionnel)
 * - Teaser de consequences (optionnel)
 */

import React from "react";
import LeaderDialogue from "./LeaderDialogue";
import PressHeadline from "./PressHeadline";
import IntelReport from "./IntelReport";
import ConsequenceTeaser from "./ConsequenceTeaser";

// =============================================================================
// TYPES
// =============================================================================

export interface LeaderDialogueData {
  speaker: string;
  title: string;
  tone: "angry" | "pleased" | "threatening" | "neutral" | "cautious";
  message: string;
  country?: string;
  portrait_style?: string;
}

export interface PressHeadlineData {
  source: string;
  source_id: string;
  headline: string;
  excerpt: string;
  sentiment: "positive" | "negative" | "neutral";
  bias: string;
  country: string;
  credibility: string;
}

export interface IntelReportData {
  classification: string;
  content: string;
  reliability: string;
  source_type: string;
  analyst_note?: string;
}

export interface CausalContextData {
  caused_by?: string;
  caused_by_date?: string;
  effects_preview?: string[];
  domino_zones?: string[];
}

export interface NarrativeSceneData {
  narrative: string;
  mood: "neutral" | "tense" | "hopeful" | "dark" | "triumphant";
  importance: "minor" | "normal" | "major" | "critical";

  // Optionnels - le Chef d'Orchestre decide ce qui est pertinent
  leader_dialogue?: LeaderDialogueData;
  press_headlines?: PressHeadlineData[];
  intel_report?: IntelReportData;
  causal_context?: CausalContextData;
  consequence_teaser?: string;

  // Metadata
  year?: number;
  month?: number;
  zone?: string;
  zone_name_fr?: string;
  event_type?: string;

  // Flags
  is_player_caused?: boolean;
  is_crisis?: boolean;
  is_turning_point?: boolean;
}

interface NarrativeSceneProps {
  scene: NarrativeSceneData;
  onContinue?: () => void;
  isLast?: boolean;
}

// =============================================================================
// MOOD STYLES
// =============================================================================

const MOOD_STYLES = {
  neutral: {
    bg: "bg-[#0d1420]",
    border: "border-slate-700",
    text: "text-slate-300",
    accent: "text-cyan-400",
  },
  tense: {
    bg: "bg-[#1a0f0f]",
    border: "border-orange-900/50",
    text: "text-orange-100",
    accent: "text-orange-400",
  },
  hopeful: {
    bg: "bg-[#0f1a15]",
    border: "border-green-900/50",
    text: "text-green-100",
    accent: "text-green-400",
  },
  dark: {
    bg: "bg-[#0a0a0a]",
    border: "border-red-900/50",
    text: "text-red-100",
    accent: "text-red-400",
  },
  triumphant: {
    bg: "bg-[#15150f]",
    border: "border-amber-700/50",
    text: "text-amber-100",
    accent: "text-amber-400",
  },
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function NarrativeScene({ scene, onContinue, isLast }: NarrativeSceneProps) {
  const mood = MOOD_STYLES[scene.mood] || MOOD_STYLES.neutral;

  return (
    <div className={`${mood.bg} border ${mood.border} rounded-lg overflow-hidden`}>
      {/* Header - Context */}
      {(scene.zone_name_fr || scene.year) && (
        <div className="px-4 py-2 border-b border-slate-800/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {scene.zone_name_fr && (
              <span className={`text-xs font-mono uppercase tracking-wider ${mood.accent}`}>
                {scene.zone_name_fr}
              </span>
            )}
            {scene.is_crisis && (
              <span className="text-[10px] font-mono text-red-400 bg-red-500/20 px-2 py-0.5 rounded">
                CRISE
              </span>
            )}
            {scene.is_turning_point && (
              <span className="text-[10px] font-mono text-amber-400 bg-amber-500/20 px-2 py-0.5 rounded">
                MOMENT HISTORIQUE
              </span>
            )}
          </div>
          {scene.year && (
            <span className="text-[10px] font-mono text-slate-600">
              {scene.month && `${getMonthName(scene.month)} `}{scene.year}
            </span>
          )}
        </div>
      )}

      {/* Main Narrative */}
      <div className="p-4">
        <p className={`text-sm leading-relaxed ${mood.text} whitespace-pre-wrap`}>
          {scene.narrative}
        </p>
      </div>

      {/* Causal Context - D'ou vient cet evenement */}
      {scene.causal_context?.caused_by && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 text-[10px] text-slate-500">
            <span className="text-slate-600">En consequence de:</span>
            <span className="text-cyan-500/70">{scene.causal_context.caused_by}</span>
          </div>
        </div>
      )}

      {/* Leader Dialogue - Si present */}
      {scene.leader_dialogue && (
        <div className="px-4 pb-4">
          <LeaderDialogue dialogue={scene.leader_dialogue} mood={scene.mood} />
        </div>
      )}

      {/* Press Headlines - Multiples perspectives */}
      {scene.press_headlines && scene.press_headlines.length > 0 && (
        <div className="px-4 pb-4">
          <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">
            Dans la presse mondiale
          </div>
          <div className="space-y-2">
            {scene.press_headlines.map((headline, idx) => (
              <PressHeadline key={idx} headline={headline} />
            ))}
          </div>
        </div>
      )}

      {/* Intel Report - Si covert */}
      {scene.intel_report && (
        <div className="px-4 pb-4">
          <IntelReport report={scene.intel_report} />
        </div>
      )}

      {/* Domino Zones - Effets de contagion */}
      {scene.causal_context?.domino_zones && scene.causal_context.domino_zones.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono text-orange-500/70">
              Zones affectees:
            </span>
            {scene.causal_context.domino_zones.map((zone, idx) => (
              <span
                key={idx}
                className="text-[10px] font-mono text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded"
              >
                {zone}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Consequence Teaser */}
      {scene.consequence_teaser && (
        <div className="px-4 pb-4">
          <ConsequenceTeaser text={scene.consequence_teaser} />
        </div>
      )}

      {/* Footer - Continue Button */}
      {onContinue && (
        <div className="px-4 py-3 border-t border-slate-800/50 flex justify-end">
          <button
            onClick={onContinue}
            className={`
              px-4 py-2 text-xs font-mono uppercase tracking-wider rounded
              transition-all duration-200
              ${isLast
                ? "bg-cyan-600 hover:bg-cyan-500 text-white"
                : "bg-slate-800 hover:bg-slate-700 text-slate-300"
              }
            `}
          >
            {isLast ? "Terminer" : "Continuer"}
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function getMonthName(month: number): string {
  const months = [
    "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
  ];
  return months[month - 1] || "";
}

export default NarrativeScene;
