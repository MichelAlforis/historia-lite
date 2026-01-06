"use client";

/**
 * LeaderPanel - Dynamic World Leaders
 *
 * Shows the relevant leader based on context:
 * - Zone selection
 * - Active crisis
 * - Default to main adversary (USSR)
 *
 * Each leader has personality, moods, and quotes.
 */

import React, { useState, useEffect } from "react";

// =============================================================================
// LEADER TYPES
// =============================================================================

type LeaderId = "khrushchev" | "castro" | "mao" | "ho_chi_minh" | "nasser" | "de_gaulle";

type LeaderMood =
  | "calm"
  | "smug"
  | "angry"
  | "threatening"
  | "desperate"
  | "triumphant"
  | "worried"
  | "defiant"
  | "friendly";

interface LeaderConfig {
  id: LeaderId;
  name: string;
  title: string;
  country: string;
  flag: string;
  color: string;
  borderColor: string;
  isAlly: boolean;
  zones: string[];
  portrait: LeaderPortraitConfig;
  quotes: Record<LeaderMood, string>;
  defaultMood: LeaderMood;
}

interface LeaderPortraitConfig {
  faceColor: string;
  hairColor: string;
  hairStyle: "bald" | "slick" | "thick" | "military" | "wavy" | "receding";
  facialHair: "none" | "beard" | "goatee" | "mustache";
  glasses: boolean;
  hat: "none" | "military_cap" | "kepi" | "beret";
  features: string[];
}

// =============================================================================
// LEADERS DATABASE
// =============================================================================

const LEADERS: Record<LeaderId, LeaderConfig> = {
  khrushchev: {
    id: "khrushchev",
    name: "NIKITA KHROUCHTCHEV",
    title: "Premier Secretaire",
    country: "URSS",
    flag: "☭",
    color: "red",
    borderColor: "border-red-900/30",
    isAlly: false,
    zones: ["europe_east", "far_east"],
    portrait: {
      faceColor: "#d4a574",
      hairColor: "#5a4a3a",
      hairStyle: "bald",
      facialHair: "none",
      glasses: false,
      hat: "none",
      features: ["round_face", "thick_eyebrows"],
    },
    quotes: {
      calm: "\"Nous pouvons discuter... pour l'instant.\"",
      smug: "\"Vous croyez vraiment pouvoir nous arreter?\"",
      angry: "\"VOUS OSEZ?! Il y aura des consequences!\"",
      threatening: "\"Nous vous enterrerons.\"",
      desperate: "\"Le Politburo exige des resultats...\"",
      triumphant: "\"Ha! L'Histoire est de notre cote!\"",
      worried: "\"Peut-etre... devrions-nous reconsiderer.\"",
      defiant: "\"L'URSS ne reculera jamais!\"",
      friendly: "\"La coexistence pacifique est possible.\"",
    },
    defaultMood: "calm",
  },

  castro: {
    id: "castro",
    name: "FIDEL CASTRO",
    title: "Lider Maximo",
    country: "CUBA",
    flag: "🇨🇺",
    color: "green",
    borderColor: "border-green-900/30",
    isAlly: false,
    zones: ["central_america"],
    portrait: {
      faceColor: "#c49a74",
      hairColor: "#2a2a2a",
      hairStyle: "thick",
      facialHair: "beard",
      glasses: false,
      hat: "military_cap",
      features: ["strong_jaw", "intense_eyes"],
    },
    quotes: {
      calm: "\"La Revolution ne craint personne.\"",
      smug: "\"Les Yankees ne comprennent rien a Cuba.\"",
      angry: "\"Imperialistas! Vous paierez pour ceci!\"",
      threatening: "\"Nous sommes prets a mourir pour la Revolution!\"",
      desperate: "\"L'embargo nous etrangle... mais nous resisterons.\"",
      triumphant: "\"Viva la Revolucion! Cuba vaincra!\"",
      worried: "\"Moscou doit nous soutenir davantage...\"",
      defiant: "\"Patria o Muerte!\"",
      friendly: "\"Le peuple cubain desire la paix.\"",
    },
    defaultMood: "defiant",
  },

  mao: {
    id: "mao",
    name: "MAO ZEDONG",
    title: "Grand Timonier",
    country: "CHINE",
    flag: "🇨🇳",
    color: "red",
    borderColor: "border-red-800/30",
    isAlly: false,
    zones: ["far_east", "southeast_asia"],
    portrait: {
      faceColor: "#deb887",
      hairColor: "#1a1a1a",
      hairStyle: "slick",
      facialHair: "none",
      glasses: false,
      hat: "none",
      features: ["mole", "round_face", "serene_expression"],
    },
    quotes: {
      calm: "\"La patience est une vertu revolutionnaire.\"",
      smug: "\"L'Occident est un tigre de papier.\"",
      angry: "\"Les revisionnistes seront balayes!\"",
      threatening: "\"Nous avons 600 millions de soldats.\"",
      desperate: "\"Le Grand Bond doit reussir...\"",
      triumphant: "\"Le vent d'Est l'emporte sur le vent d'Ouest!\"",
      worried: "\"Les contradictions internes s'aggravent.\"",
      defiant: "\"Le pouvoir est au bout du fusil.\"",
      friendly: "\"La Chine desire la paix avec tous les peuples.\"",
    },
    defaultMood: "calm",
  },

  ho_chi_minh: {
    id: "ho_chi_minh",
    name: "HO CHI MINH",
    title: "Oncle Ho",
    country: "VIETNAM",
    flag: "🇻🇳",
    color: "red",
    borderColor: "border-red-700/30",
    isAlly: false,
    zones: ["southeast_asia"],
    portrait: {
      faceColor: "#d4a574",
      hairColor: "#888888",
      hairStyle: "receding",
      facialHair: "goatee",
      glasses: false,
      hat: "none",
      features: ["thin_face", "wise_eyes", "goatee"],
    },
    quotes: {
      calm: "\"Le Vietnam sera unifie, tot ou tard.\"",
      smug: "\"Vous ne pouvez pas bombarder une idee.\"",
      angry: "\"Chaque bombe cree dix nouveaux combattants!\"",
      threatening: "\"Nous combattrons mille ans s'il le faut.\"",
      desperate: "\"Le peuple souffre mais ne plie pas.\"",
      triumphant: "\"Rien n'est plus precieux que l'independance!\"",
      worried: "\"L'aide sino-sovietique est insuffisante.\"",
      defiant: "\"Vous tuerez dix des notres, nous tuerons un des votres.\"",
      friendly: "\"Nous aspirons simplement a la liberte.\"",
    },
    defaultMood: "defiant",
  },

  nasser: {
    id: "nasser",
    name: "GAMAL ABDEL NASSER",
    title: "Rais",
    country: "EGYPTE",
    flag: "🇪🇬",
    color: "amber",
    borderColor: "border-amber-900/30",
    isAlly: false,
    zones: ["middle_east", "north_africa"],
    portrait: {
      faceColor: "#c49a74",
      hairColor: "#2a2a2a",
      hairStyle: "military",
      facialHair: "mustache",
      glasses: false,
      hat: "none",
      features: ["strong_chin", "military_uniform", "proud_posture"],
    },
    quotes: {
      calm: "\"Le Monde Arabe se releve.\"",
      smug: "\"Le Canal est a l'Egypte, pas aux colonisateurs.\"",
      angry: "\"Israel ne survivra pas a cette generation!\"",
      threatening: "\"Les armees arabes sont pretes.\"",
      desperate: "\"Ou est le soutien sovietique?\"",
      triumphant: "\"Le panarabisme triomphe!\"",
      worried: "\"La situation au Sinai m'inquiete.\"",
      defiant: "\"L'Egypte ne sera plus jamais une colonie!\"",
      friendly: "\"Le non-alignement est notre voie.\"",
    },
    defaultMood: "defiant",
  },

  de_gaulle: {
    id: "de_gaulle",
    name: "CHARLES DE GAULLE",
    title: "President",
    country: "FRANCE",
    flag: "🇫🇷",
    color: "blue",
    borderColor: "border-blue-900/30",
    isAlly: true,
    zones: ["europe_west", "north_africa"],
    portrait: {
      faceColor: "#e8d4c4",
      hairColor: "#888888",
      hairStyle: "military",
      facialHair: "none",
      glasses: false,
      hat: "kepi",
      features: ["tall", "prominent_nose", "military_uniform"],
    },
    quotes: {
      calm: "\"La France a sa propre voie.\"",
      smug: "\"L'OTAN? La France n'est le vassal de personne.\"",
      angry: "\"Les Anglo-Saxons ne comprennent rien!\"",
      threatening: "\"La Force de Frappe garantit notre independance.\"",
      desperate: "\"L'Algerie nous saigne...\"",
      triumphant: "\"La grandeur de la France est intacte!\"",
      worried: "\"L'Europe doit s'unir... sous notre direction.\"",
      defiant: "\"Non, non, et non!\"",
      friendly: "\"La France reste l'alliee des Etats-Unis.\"",
    },
    defaultMood: "smug",
  },
};

// Zone to leader mapping
const ZONE_LEADER_MAP: Record<string, LeaderId> = {
  europe_east: "khrushchev",
  europe_west: "de_gaulle",
  central_america: "castro",
  south_america: "castro",
  middle_east: "nasser",
  north_africa: "nasser",
  sub_saharan_africa: "nasser",
  southeast_asia: "ho_chi_minh",
  south_asia: "mao",
  far_east: "mao",
  turkey_greece: "khrushchev",
  scandinavia: "khrushchev",
};

// =============================================================================
// PORTRAIT RENDERER
// =============================================================================

interface PortraitProps {
  leader: LeaderConfig;
  mood: LeaderMood;
  glowColor: string;
}

function LeaderPortrait({ leader, mood, glowColor }: PortraitProps) {
  const [blinkPhase, setBlinkPhase] = useState(0);
  const config = leader.portrait;

  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinkPhase(1);
      setTimeout(() => setBlinkPhase(0), 150);
    }, 3000 + Math.random() * 2000);
    return () => clearInterval(blinkInterval);
  }, []);

  const eyeHeight = blinkPhase === 1 ? 2 : 8;
  const moodEffects = getMoodEffects(mood);

  return (
    <div className="relative w-20 h-20 rounded-full overflow-hidden" style={{ boxShadow: `0 0 30px ${glowColor}` }}>
      <div className="absolute inset-0 rounded-full transition-colors duration-500" style={{ backgroundColor: glowColor }} />

      <svg viewBox="0 0 100 100" className="relative w-full h-full">
        {/* Hat (if any) */}
        {config.hat === "military_cap" && (
          <g>
            <ellipse cx="50" cy="20" rx="32" ry="12" fill="#2d4a2d" />
            <rect x="18" y="18" width="64" height="8" fill="#2d4a2d" />
            <rect x="22" y="26" width="56" height="4" fill="#1a2e1a" />
            <ellipse cx="50" cy="22" rx="8" ry="4" fill="#8b0000" />
          </g>
        )}
        {config.hat === "kepi" && (
          <g>
            <path d="M 25 30 L 35 15 L 65 15 L 75 30 Z" fill="#1a2e4a" />
            <rect x="20" y="28" width="60" height="6" fill="#0a1e3a" />
            <ellipse cx="50" cy="20" rx="5" ry="3" fill="#ffd700" />
          </g>
        )}

        {/* Hair (based on style) */}
        {config.hairStyle === "thick" && (
          <ellipse cx="50" cy="28" rx="28" ry="18" fill={config.hairColor} />
        )}
        {config.hairStyle === "slick" && (
          <ellipse cx="50" cy="30" rx="30" ry="15" fill={config.hairColor} />
        )}
        {config.hairStyle === "receding" && (
          <>
            <path d="M 25 40 Q 30 25, 50 25 Q 70 25, 75 40" fill={config.hairColor} />
          </>
        )}
        {config.hairStyle === "military" && (
          <path d="M 22 38 L 25 28 Q 50 22, 75 28 L 78 38 Z" fill={config.hairColor} />
        )}

        {/* Face base */}
        <ellipse cx="50" cy="55" rx="32" ry="38" fill={config.faceColor} className="transition-all duration-300" />

        {/* Bald head shine (for Khrushchev) */}
        {config.hairStyle === "bald" && (
          <>
            <ellipse cx="50" cy="35" rx="28" ry="22" fill={config.faceColor} />
            <ellipse cx="50" cy="30" rx="14" ry="9" fill="rgba(255,255,255,0.15)" />
          </>
        )}

        {/* Eyebrows */}
        <g transform={`rotate(${moodEffects.browAngle}, 35, 48)`}>
          <rect x="25" y="46" width="18" height="3" rx="1.5" fill={config.hairColor} />
        </g>
        <g transform={`rotate(${-moodEffects.browAngle}, 65, 48)`}>
          <rect x="57" y="46" width="18" height="3" rx="1.5" fill={config.hairColor} />
        </g>

        {/* Eyes */}
        <g transform={`translate(${moodEffects.eyeX}, ${moodEffects.eyeY})`}>
          <ellipse cx="35" cy="55" rx="5" ry={eyeHeight} fill="white" />
          <ellipse cx="35" cy="55" rx="2.5" ry={Math.min(2.5, eyeHeight)} fill="#2a2a2a" />
          <ellipse cx="34" cy="54" rx="1" ry="1" fill="white" />
          <ellipse cx="65" cy="55" rx="5" ry={eyeHeight} fill="white" />
          <ellipse cx="65" cy="55" rx="2.5" ry={Math.min(2.5, eyeHeight)} fill="#2a2a2a" />
          <ellipse cx="64" cy="54" rx="1" ry="1" fill="white" />
        </g>

        {/* Glasses (if any) */}
        {config.glasses && (
          <g stroke="#2a2a2a" strokeWidth="1.5" fill="none">
            <circle cx="35" cy="55" r="10" />
            <circle cx="65" cy="55" r="10" />
            <line x1="45" y1="55" x2="55" y2="55" />
          </g>
        )}

        {/* Nose */}
        <ellipse cx="50" cy="68" rx="5" ry="4" fill={darkenColor(config.faceColor, 15)} />

        {/* Facial hair */}
        {config.facialHair === "beard" && (
          <path d="M 30 72 Q 35 90, 50 95 Q 65 90, 70 72 Q 65 85, 50 88 Q 35 85, 30 72" fill={config.hairColor} />
        )}
        {config.facialHair === "goatee" && (
          <path d="M 42 78 Q 45 92, 50 95 Q 55 92, 58 78 Q 55 85, 50 88 Q 45 85, 42 78" fill={config.hairColor} />
        )}
        {config.facialHair === "mustache" && (
          <path d="M 38 74 Q 44 78, 50 76 Q 56 78, 62 74 Q 56 76, 50 74 Q 44 76, 38 74" fill={config.hairColor} strokeWidth="2" />
        )}

        {/* Mouth */}
        <path
          d={`M 40 80 Q 50 ${80 + moodEffects.mouthCurve} 60 80`}
          fill="none"
          stroke={darkenColor(config.faceColor, 30)}
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Ears */}
        <ellipse cx="18" cy="55" rx="4" ry="7" fill={config.faceColor} />
        <ellipse cx="82" cy="55" rx="4" ry="7" fill={config.faceColor} />

        {/* Collar/uniform hint */}
        {leader.id === "castro" || leader.id === "nasser" || leader.id === "de_gaulle" ? (
          <path d="M 25 95 L 32 85 L 50 88 L 68 85 L 75 95" fill="#3a4a3a" stroke="#2a3a2a" strokeWidth="1" />
        ) : (
          <path d="M 25 95 L 35 85 L 50 90 L 65 85 L 75 95" fill="#3a3a3a" stroke="#2a2a2a" strokeWidth="1" />
        )}

        {/* Mao's mole */}
        {leader.id === "mao" && (
          <circle cx="44" cy="82" r="2" fill={darkenColor(config.faceColor, 20)} />
        )}
      </svg>

      {/* Anger effect */}
      {(mood === "angry" || mood === "threatening") && (
        <div className="absolute top-2 right-3 text-red-500 animate-pulse">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L8 8H4L8 14L4 22H12L16 14L20 22H16L12 14L16 8H12L8 2H12Z" />
          </svg>
        </div>
      )}
    </div>
  );
}

function getMoodEffects(mood: LeaderMood) {
  const effects: Record<LeaderMood, { browAngle: number; eyeX: number; eyeY: number; mouthCurve: number }> = {
    calm: { browAngle: 0, eyeX: 0, eyeY: 0, mouthCurve: 0 },
    smug: { browAngle: 5, eyeX: 2, eyeY: -1, mouthCurve: 6 },
    angry: { browAngle: -15, eyeX: 0, eyeY: 2, mouthCurve: -8 },
    threatening: { browAngle: -20, eyeX: 0, eyeY: 3, mouthCurve: -4 },
    desperate: { browAngle: 10, eyeX: -1, eyeY: 1, mouthCurve: -6 },
    triumphant: { browAngle: 8, eyeX: 0, eyeY: -2, mouthCurve: 12 },
    worried: { browAngle: 8, eyeX: 1, eyeY: 0, mouthCurve: -3 },
    defiant: { browAngle: -10, eyeX: 0, eyeY: 1, mouthCurve: -2 },
    friendly: { browAngle: 5, eyeX: 0, eyeY: -1, mouthCurve: 8 },
  };
  return effects[mood];
}

function darkenColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace("#", ""), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.max(0, (num >> 16) - amt);
  const G = Math.max(0, ((num >> 8) & 0x00ff) - amt);
  const B = Math.max(0, (num & 0x0000ff) - amt);
  return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface LeaderPanelProps {
  selectedZone?: string | null;
  activeCrisis?: { zone: string; type: string } | null;
  defcon: number;
  worldTension: number;
  pressures?: { army: number; party: number; economy: number };
}

export function LeaderPanel({
  selectedZone,
  activeCrisis,
  defcon,
  worldTension,
  pressures = { army: 45, party: 55, economy: 40 },
}: LeaderPanelProps) {
  // Determine which leader to show
  const getActiveLeader = (): LeaderId => {
    // Crisis takes priority
    if (activeCrisis?.zone) {
      return ZONE_LEADER_MAP[activeCrisis.zone] || "khrushchev";
    }
    // Then selected zone
    if (selectedZone) {
      return ZONE_LEADER_MAP[selectedZone] || "khrushchev";
    }
    // Default to main adversary
    return "khrushchev";
  };

  const leaderId = getActiveLeader();
  const leader = LEADERS[leaderId];

  // Determine mood based on game state
  const getMood = (): LeaderMood => {
    if (defcon <= 2) return "threatening";
    if (worldTension > 80) return "angry";
    if (pressures.army > 80 || pressures.party > 80) return "desperate";
    if (worldTension < 30 && leader.isAlly) return "friendly";
    if (worldTension < 30) return "worried";
    if (worldTension > 60) return leader.isAlly ? "worried" : "smug";
    return leader.defaultMood;
  };

  const mood = getMood();
  const quote = leader.quotes[mood];

  // Glow color based on mood and leader
  const getGlowColor = () => {
    if (mood === "angry" || mood === "threatening") return "rgba(255, 50, 50, 0.4)";
    if (mood === "triumphant") return "rgba(255, 200, 50, 0.4)";
    if (mood === "friendly") return "rgba(50, 150, 255, 0.3)";
    if (leader.isAlly) return "rgba(50, 100, 200, 0.2)";
    return "rgba(150, 50, 50, 0.2)";
  };

  // Typing effect for quote
  const [displayedQuote, setDisplayedQuote] = useState("");
  const [quoteIndex, setQuoteIndex] = useState(0);

  useEffect(() => {
    setDisplayedQuote("");
    setQuoteIndex(0);
  }, [leaderId, mood]);

  useEffect(() => {
    if (quoteIndex < quote.length) {
      const timeout = setTimeout(() => {
        setDisplayedQuote(quote.slice(0, quoteIndex + 1));
        setQuoteIndex(quoteIndex + 1);
      }, 25);
      return () => clearTimeout(timeout);
    }
  }, [quoteIndex, quote]);

  const moodLabel = {
    calm: "NEUTRE",
    smug: "CONFIANT",
    angry: "FURIEUX",
    threatening: "MENACANT",
    desperate: "SOUS PRESSION",
    triumphant: "VICTORIEUX",
    worried: "INQUIET",
    defiant: "DEFIANT",
    friendly: "COOPERATIF",
  };

  const moodColor = {
    calm: "bg-slate-700 text-slate-400",
    smug: "bg-amber-500/20 text-amber-400",
    angry: "bg-red-500/20 text-red-400",
    threatening: "bg-red-600/30 text-red-400",
    desperate: "bg-orange-500/20 text-orange-400",
    triumphant: "bg-yellow-500/20 text-yellow-400",
    worried: "bg-blue-500/20 text-blue-400",
    defiant: "bg-purple-500/20 text-purple-400",
    friendly: "bg-green-500/20 text-green-400",
  };

  return (
    <div className={`
      bg-[#0d1420] border rounded-lg overflow-hidden transition-all duration-500
      ${defcon <= 2 && !leader.isAlly ? "border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.3)]" : leader.borderColor}
    `}>
      {/* Header */}
      <div className={`px-4 py-2 border-b ${leader.borderColor} bg-[#0a0e17]`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{leader.flag}</span>
            <span className={`text-xs font-mono tracking-[0.12em] uppercase ${
              leader.isAlly ? "text-blue-400/70" : "text-red-400/70"
            }`}>
              {leader.title}
            </span>
          </div>
          {leader.isAlly && (
            <span className="text-[9px] font-mono bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
              ALLIE
            </span>
          )}
        </div>
      </div>

      {/* Portrait + Info */}
      <div className="p-4">
        <div className="flex items-start gap-4">
          <LeaderPortrait leader={leader} mood={mood} glowColor={getGlowColor()} />

          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-slate-200 tracking-wide">
              {leader.name}
            </h3>
            <p className="text-[10px] font-mono text-slate-500 mt-0.5">
              {leader.country}
            </p>

            {/* Mood indicator */}
            <div className={`mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono ${moodColor[mood]}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                mood === "threatening" || mood === "angry" ? "bg-red-400 animate-pulse" : "bg-current"
              }`} />
              {moodLabel[mood]}
            </div>
          </div>
        </div>

        {/* Quote */}
        <div className="mt-4 p-3 bg-[#080c14] rounded border border-slate-800/50">
          <p className={`text-xs min-h-[2.5rem] ${
            mood === "angry" || mood === "threatening" ? "text-red-400 font-bold" :
            mood === "triumphant" ? "text-yellow-400" :
            mood === "friendly" ? "text-green-400" :
            mood === "defiant" ? "text-purple-400" :
            "text-slate-400"
          }`}>
            {displayedQuote}
            <span className="animate-pulse">|</span>
          </p>
        </div>

        {/* Pressures (only for USSR leader) */}
        {leaderId === "khrushchev" && (
          <div className="mt-4 space-y-2">
            <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">
              Pressions Internes
            </div>
            <PressureBar label="Armee Rouge" value={pressures.army} color="bg-red-600" icon="🎖️" />
            <PressureBar label="Politburo" value={pressures.party} color="bg-amber-600" icon="⚙️" />
            <PressureBar label="Economie" value={pressures.economy} color="bg-emerald-600" icon="🏭" />
          </div>
        )}

        {/* Leader-specific info */}
        {leaderId !== "khrushchev" && (
          <div className="mt-4 pt-3 border-t border-slate-800/50">
            <div className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-1">
              Zones d'Influence
            </div>
            <div className="flex flex-wrap gap-1">
              {leader.zones.map((zone) => (
                <span key={zone} className="text-[10px] font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                  {zone.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// PRESSURE BAR (reused from AdversaryPanel)
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
      <span className="text-sm">{icon}</span>
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

export default LeaderPanel;
