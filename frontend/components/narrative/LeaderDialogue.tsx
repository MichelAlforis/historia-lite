"use client";

/**
 * LeaderDialogue - Dialogue d'un Leader Mondial
 *
 * Affiche un dialogue cinematographique d'un leader.
 * Le ton influence le style visuel (angry = rouge, pleased = vert, etc.)
 */

import React from "react";

// =============================================================================
// TYPES
// =============================================================================

interface LeaderDialogueData {
  speaker: string;
  title: string;
  tone: "angry" | "pleased" | "threatening" | "neutral" | "cautious";
  message: string;
  country?: string;
  portrait_style?: string;
}

interface LeaderDialogueProps {
  dialogue: LeaderDialogueData;
  mood?: string;
}

// =============================================================================
// TONE STYLES
// =============================================================================

const TONE_STYLES = {
  angry: {
    border: "border-red-700/50",
    bg: "bg-red-950/30",
    speaker: "text-red-400",
    message: "text-red-200",
    icon: "text-red-500",
  },
  threatening: {
    border: "border-orange-700/50",
    bg: "bg-orange-950/30",
    speaker: "text-orange-400",
    message: "text-orange-200",
    icon: "text-orange-500",
  },
  pleased: {
    border: "border-green-700/50",
    bg: "bg-green-950/30",
    speaker: "text-green-400",
    message: "text-green-200",
    icon: "text-green-500",
  },
  cautious: {
    border: "border-amber-700/50",
    bg: "bg-amber-950/30",
    speaker: "text-amber-400",
    message: "text-amber-200",
    icon: "text-amber-500",
  },
  neutral: {
    border: "border-slate-700/50",
    bg: "bg-slate-900/50",
    speaker: "text-slate-400",
    message: "text-slate-300",
    icon: "text-slate-500",
  },
};

// =============================================================================
// COUNTRY FLAGS/ICONS (simplified)
// =============================================================================

const COUNTRY_ICONS: Record<string, string> = {
  USA: "us",
  USSR: "su",
  FRA: "fr",
  GBR: "gb",
  CHN: "cn",
  DEU: "de",
  CUB: "cu",
  EGY: "eg",
  IND: "in",
  BRA: "br",
};

// =============================================================================
// COMPONENT
// =============================================================================

export function LeaderDialogue({ dialogue, mood }: LeaderDialogueProps) {
  const toneStyle = TONE_STYLES[dialogue.tone] || TONE_STYLES.neutral;

  return (
    <div className={`${toneStyle.bg} border ${toneStyle.border} rounded-lg p-4`}>
      {/* Header - Speaker info */}
      <div className="flex items-start gap-3 mb-3">
        {/* Portrait placeholder */}
        <div className={`
          w-12 h-12 rounded-full flex items-center justify-center
          bg-slate-800 border-2 ${toneStyle.border}
        `}>
          <span className="text-lg font-bold text-slate-500">
            {dialogue.speaker.charAt(0)}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-semibold ${toneStyle.speaker}`}>
              {dialogue.speaker}
            </span>
            {dialogue.country && (
              <span className="text-[10px] font-mono text-slate-600 uppercase">
                [{dialogue.country}]
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {dialogue.title}
          </div>
        </div>

        {/* Tone indicator */}
        <div className={`text-xs ${toneStyle.icon}`}>
          {getToneIcon(dialogue.tone)}
        </div>
      </div>

      {/* Message - The actual dialogue */}
      <div className="relative">
        {/* Quote marks */}
        <span className={`absolute -left-1 -top-2 text-2xl ${toneStyle.icon} opacity-30`}>
          "
        </span>

        <p className={`${toneStyle.message} text-sm leading-relaxed pl-4 pr-2 italic`}>
          {dialogue.message}
        </p>

        <span className={`absolute -right-1 -bottom-2 text-2xl ${toneStyle.icon} opacity-30`}>
          "
        </span>
      </div>
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function getToneIcon(tone: string): string {
  switch (tone) {
    case "angry":
      return "!!";
    case "threatening":
      return "!";
    case "pleased":
      return "+";
    case "cautious":
      return "?";
    default:
      return "-";
  }
}

export default LeaderDialogue;
