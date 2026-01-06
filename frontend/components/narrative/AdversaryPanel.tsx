"use client";

/**
 * AdversaryPanel - The Face of Your Enemy
 *
 * Khrushchev stares at you. His mood changes. He has personality.
 * This is not a system - this is a man who can end the world.
 */

import React, { useState, useEffect } from "react";

// =============================================================================
// KHRUSHCHEV MOODS
// =============================================================================

type KhrushchevMood =
  | "calm"        // Détente, négociations possibles
  | "smug"        // Il pense avoir l'avantage
  | "angry"       // Tu l'as provoqué
  | "threatening" // Il menace, DEFCON bas
  | "desperate"   // Sous pression interne
  | "triumphant"  // Il vient de gagner un round
  | "worried";    // Tu l'as mis en difficulté

interface MoodConfig {
  expression: string;
  eyePosition: { x: number; y: number };
  browAngle: number;
  mouthCurve: number;
  faceColor: string;
  glowColor: string;
  quote: string;
  quoteStyle: string;
}

const MOOD_CONFIG: Record<KhrushchevMood, MoodConfig> = {
  calm: {
    expression: "neutral",
    eyePosition: { x: 0, y: 0 },
    browAngle: 0,
    mouthCurve: 0,
    faceColor: "#d4a574",
    glowColor: "rgba(100, 150, 100, 0.2)",
    quote: "\"Nous pouvons discuter... pour l'instant.\"",
    quoteStyle: "text-slate-400",
  },
  smug: {
    expression: "smirk",
    eyePosition: { x: 2, y: -1 },
    browAngle: 5,
    mouthCurve: 8,
    faceColor: "#d4a574",
    glowColor: "rgba(200, 150, 50, 0.3)",
    quote: "\"Vous croyez vraiment pouvoir nous arrêter?\"",
    quoteStyle: "text-amber-400",
  },
  angry: {
    expression: "furious",
    eyePosition: { x: 0, y: 2 },
    browAngle: -15,
    mouthCurve: -10,
    faceColor: "#c98a64",
    glowColor: "rgba(255, 100, 100, 0.4)",
    quote: "\"VOUS OSEZ?! Il y aura des conséquences!\"",
    quoteStyle: "text-red-400 font-bold",
  },
  threatening: {
    expression: "menacing",
    eyePosition: { x: 0, y: 3 },
    browAngle: -20,
    mouthCurve: -5,
    faceColor: "#b87a54",
    glowColor: "rgba(255, 50, 50, 0.5)",
    quote: "\"Nous vous enterrerons.\"",
    quoteStyle: "text-red-500 font-bold animate-pulse",
  },
  desperate: {
    expression: "stressed",
    eyePosition: { x: -1, y: 1 },
    browAngle: 10,
    mouthCurve: -8,
    faceColor: "#c49a74",
    glowColor: "rgba(150, 100, 50, 0.3)",
    quote: "\"Le Politburo exige des résultats...\"",
    quoteStyle: "text-orange-400 italic",
  },
  triumphant: {
    expression: "victorious",
    eyePosition: { x: 0, y: -2 },
    browAngle: 10,
    mouthCurve: 15,
    faceColor: "#d4a574",
    glowColor: "rgba(255, 200, 50, 0.4)",
    quote: "\"Ha! L'Histoire est de notre côté!\"",
    quoteStyle: "text-yellow-400 font-bold",
  },
  worried: {
    expression: "concerned",
    eyePosition: { x: 1, y: 0 },
    browAngle: 8,
    mouthCurve: -3,
    faceColor: "#c4a584",
    glowColor: "rgba(100, 100, 150, 0.3)",
    quote: "\"Peut-être... devrions-nous reconsidérer.\"",
    quoteStyle: "text-blue-300 italic",
  },
};

// =============================================================================
// PRESSURE INDICATORS
// =============================================================================

interface PressureBarProps {
  label: string;
  value: number;
  color: string;
  icon: string;
}

function PressureBar({ label, value, color, icon }: PressureBarProps) {
  const isHigh = value > 70;
  const isCritical = value > 85;

  return (
    <div className="flex items-center gap-2">
      <span className="text-lg">{icon}</span>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">
            {label}
          </span>
          <span className={`text-[10px] font-mono ${isCritical ? "text-red-400 animate-pulse" : isHigh ? "text-orange-400" : "text-slate-400"}`}>
            {value}%
          </span>
        </div>
        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isCritical ? "bg-red-500 animate-pulse" : isHigh ? "bg-orange-500" : color
            }`}
            style={{ width: `${value}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// KHRUSHCHEV PORTRAIT (SVG)
// =============================================================================

interface PortraitProps {
  mood: KhrushchevMood;
  config: MoodConfig;
}

function KhrushchevPortrait({ mood, config }: PortraitProps) {
  const [blinkPhase, setBlinkPhase] = useState(0);

  // Blink animation
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinkPhase(1);
      setTimeout(() => setBlinkPhase(0), 150);
    }, 3000 + Math.random() * 2000);

    return () => clearInterval(blinkInterval);
  }, []);

  const eyeHeight = blinkPhase === 1 ? 2 : 8;

  return (
    <div className={`relative w-20 h-20 rounded-full overflow-hidden ${config.glowColor ? `shadow-[0_0_30px_${config.glowColor}]` : ""}`}>
      {/* Background glow */}
      <div
        className="absolute inset-0 rounded-full transition-colors duration-500"
        style={{ backgroundColor: config.glowColor }}
      />

      <svg viewBox="0 0 100 100" className="relative w-full h-full">
        {/* Face base */}
        <ellipse
          cx="50"
          cy="55"
          rx="35"
          ry="40"
          fill={config.faceColor}
          className="transition-all duration-300"
        />

        {/* Bald head */}
        <ellipse
          cx="50"
          cy="35"
          rx="30"
          ry="25"
          fill={config.faceColor}
          className="transition-all duration-300"
        />

        {/* Forehead shine */}
        <ellipse
          cx="50"
          cy="30"
          rx="15"
          ry="10"
          fill="rgba(255,255,255,0.15)"
        />

        {/* Eyebrows */}
        <g transform={`rotate(${config.browAngle}, 35, 48)`}>
          <rect x="25" y="46" width="20" height="4" rx="2" fill="#5a4a3a" />
        </g>
        <g transform={`rotate(${-config.browAngle}, 65, 48)`}>
          <rect x="55" y="46" width="20" height="4" rx="2" fill="#5a4a3a" />
        </g>

        {/* Eyes */}
        <g transform={`translate(${config.eyePosition.x}, ${config.eyePosition.y})`}>
          {/* Left eye */}
          <ellipse cx="35" cy="55" rx="6" ry={eyeHeight} fill="white" />
          <ellipse cx="35" cy="55" rx="3" ry={Math.min(3, eyeHeight)} fill="#2a2a2a" />
          <ellipse cx="34" cy="54" rx="1" ry="1" fill="white" />

          {/* Right eye */}
          <ellipse cx="65" cy="55" rx="6" ry={eyeHeight} fill="white" />
          <ellipse cx="65" cy="55" rx="3" ry={Math.min(3, eyeHeight)} fill="#2a2a2a" />
          <ellipse cx="64" cy="54" rx="1" ry="1" fill="white" />
        </g>

        {/* Nose */}
        <ellipse cx="50" cy="68" rx="6" ry="5" fill="#c49a74" />

        {/* Mouth */}
        <path
          d={`M 38 80 Q 50 ${80 + config.mouthCurve} 62 80`}
          fill="none"
          stroke="#8a6a5a"
          strokeWidth="3"
          strokeLinecap="round"
          className="transition-all duration-300"
        />

        {/* Ears */}
        <ellipse cx="15" cy="55" rx="5" ry="8" fill={config.faceColor} />
        <ellipse cx="85" cy="55" rx="5" ry="8" fill={config.faceColor} />

        {/* Collar hint */}
        <path
          d="M 25 95 L 35 85 L 50 90 L 65 85 L 75 95"
          fill="#3a3a3a"
          stroke="#2a2a2a"
          strokeWidth="1"
        />

        {/* Medal (when triumphant) */}
        {mood === "triumphant" && (
          <circle cx="50" cy="92" r="5" fill="#ffd700" stroke="#b8860b" strokeWidth="1">
            <animate attributeName="opacity" values="1;0.7;1" dur="1s" repeatCount="indefinite" />
          </circle>
        )}
      </svg>

      {/* Anger vein effect */}
      {(mood === "angry" || mood === "threatening") && (
        <div className="absolute top-2 right-4 text-red-500 animate-pulse">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L8 8H4L8 14L4 22H12L16 14L20 22H16L12 14L16 8H12L8 2H12Z" />
          </svg>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface AdversaryPanelProps {
  defcon: number;
  worldTension: number;
  lastAction?: string;
  pressures?: {
    army: number;
    party: number;
    economy: number;
  };
}

export function AdversaryPanel({
  defcon,
  worldTension,
  lastAction,
  pressures = { army: 45, party: 55, economy: 40 },
}: AdversaryPanelProps) {
  // Determine mood based on game state
  const getMood = (): KhrushchevMood => {
    if (defcon <= 2) return "threatening";
    if (worldTension > 80) return "angry";
    if (pressures.army > 80 || pressures.party > 80) return "desperate";
    if (worldTension < 30) return "worried";
    if (lastAction?.includes("victory") || lastAction?.includes("success")) return "triumphant";
    if (worldTension > 60) return "smug";
    return "calm";
  };

  const mood = getMood();
  const config = MOOD_CONFIG[mood];

  // Typing effect for quote
  const [displayedQuote, setDisplayedQuote] = useState("");
  const [quoteIndex, setQuoteIndex] = useState(0);

  useEffect(() => {
    setDisplayedQuote("");
    setQuoteIndex(0);
  }, [mood]);

  useEffect(() => {
    if (quoteIndex < config.quote.length) {
      const timeout = setTimeout(() => {
        setDisplayedQuote(config.quote.slice(0, quoteIndex + 1));
        setQuoteIndex(quoteIndex + 1);
      }, 30);
      return () => clearTimeout(timeout);
    }
  }, [quoteIndex, config.quote]);

  return (
    <div className={`
      bg-[#0d1420] border rounded-lg overflow-hidden transition-all duration-500
      ${defcon <= 2 ? "border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.3)]" : "border-red-900/30"}
    `}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-red-900/30 bg-[#0a0e17]">
        <div className="flex items-center gap-2">
          <span className="text-red-500 text-lg">☭</span>
          <span className="text-xs font-mono tracking-[0.15em] text-red-400/70 uppercase">
            Premier Secrétaire
          </span>
        </div>
      </div>

      {/* Portrait + Name */}
      <div className="p-4">
        <div className="flex items-start gap-4">
          <KhrushchevPortrait mood={mood} config={config} />

          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-slate-200 tracking-wide">
              NIKITA KHROUCHTCHEV
            </h3>
            <p className="text-[10px] font-mono text-slate-500 mt-0.5">
              URSS • PARTI COMMUNISTE
            </p>

            {/* Mood indicator */}
            <div className={`mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono ${
              mood === "threatening" || mood === "angry"
                ? "bg-red-500/20 text-red-400"
                : mood === "triumphant" || mood === "smug"
                ? "bg-amber-500/20 text-amber-400"
                : mood === "worried" || mood === "desperate"
                ? "bg-orange-500/20 text-orange-400"
                : "bg-slate-700 text-slate-400"
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                mood === "threatening" || mood === "angry" ? "bg-red-400 animate-pulse" : "bg-current"
              }`} />
              {mood === "calm" && "DIPLOMATIE POSSIBLE"}
              {mood === "smug" && "CONFIANT"}
              {mood === "angry" && "FURIEUX"}
              {mood === "threatening" && "MENAÇANT"}
              {mood === "desperate" && "SOUS PRESSION"}
              {mood === "triumphant" && "VICTORIEUX"}
              {mood === "worried" && "INQUIET"}
            </div>
          </div>
        </div>

        {/* Quote */}
        <div className="mt-4 p-3 bg-[#080c14] rounded border border-slate-800/50">
          <p className={`text-xs min-h-[2.5rem] ${config.quoteStyle}`}>
            {displayedQuote}
            <span className="animate-pulse">|</span>
          </p>
        </div>

        {/* Internal Pressures */}
        <div className="mt-4 space-y-2">
          <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">
            Pressions Internes Soviétiques
          </div>
          <PressureBar label="Armée Rouge" value={pressures.army} color="bg-red-600" icon="🎖️" />
          <PressureBar label="Politburo" value={pressures.party} color="bg-amber-600" icon="⚙️" />
          <PressureBar label="Économie" value={pressures.economy} color="bg-emerald-600" icon="🏭" />
        </div>

        {/* Last known action */}
        {lastAction && (
          <div className="mt-4 pt-3 border-t border-slate-800/50">
            <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-1">
              Dernière Action Détectée
            </div>
            <p className="text-xs text-slate-400 italic">
              "{lastAction}"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AdversaryPanel;
