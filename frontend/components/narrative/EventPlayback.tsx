"use client";

/**
 * EventPlayback - DRAMATIC Event Presentation with NarrativeScene Support
 *
 * Each event is a MOMENT. Not just data - DRAMA.
 *
 * AMELIORATIONS:
 * - Ecran de respiration avant le premier evenement
 * - Bouton dynamique qui change selon le contexte
 * - Le joueur ne choisit pas quand le monde s'arrete.
 *   Il decouvre quand il n'a plus le choix.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  useNarrativeStore,
  JumpEvent,
} from "@/stores/narrativeStore";
import NarrativeScene, { NarrativeSceneData } from "./NarrativeScene";

// =============================================================================
// PHRASES DE RESPIRATION (transition JUMPING -> PLAYBACK)
// =============================================================================

const BREATHING_PHRASES = [
  "Pendant que vous decidiez, le monde a continue d'agir.",
  "Vos ordres sont partis. Les consequences arrivent.",
  "Le temps s'est ecoule. Les evenements vous rattrapent.",
  "Les rouages de l'Histoire se sont mis en mouvement.",
  "Ce qui devait arriver est arrive.",
];

function getBreathingPhrase(): string {
  return BREATHING_PHRASES[Math.floor(Math.random() * BREATHING_PHRASES.length)];
}

// =============================================================================
// TEXTES DYNAMIQUES POUR LE BOUTON CONTINUER
// =============================================================================

interface DynamicButtonText {
  text: string;
  icon: string;
}

function getDynamicButtonText(
  currentIndex: number,
  totalEvents: number,
  currentEvent: JumpEvent | null,
  canAdvance: boolean
): DynamicButtonText {
  // Dernier evenement
  if (currentIndex >= totalEvents - 1) {
    return { text: "Reprendre le controle", icon: "command" };
  }

  // Si on est en train de reveler, on peut "Passer"
  if (!canAdvance) {
    return { text: "Passer", icon: "skip" };
  }

  // Evenement critique proche
  const isCritical = currentEvent?.importance === "critical";
  const isMajor = currentEvent?.importance === "major";
  const remaining = totalEvents - currentIndex - 1;

  // Basé sur le type d'evenement et la progression
  if (isCritical) {
    return { text: "La pression monte", icon: "tension" };
  }

  if (remaining === 1) {
    return { text: "Dernier rapport", icon: "final" };
  }

  if (isMajor) {
    return { text: "Suite des evenements", icon: "next" };
  }

  // Progression normale
  if (currentIndex < 2) {
    return { text: "Ecouter la suite", icon: "listen" };
  }

  return { text: "Continuer", icon: "next" };
}

// =============================================================================
// TYPEWRITER TEXT
// =============================================================================

interface TypewriterTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

function TypewriterText({ text, speed = 25, onComplete }: TypewriterTextProps) {
  const [displayed, setDisplayed] = useState("");
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setDisplayed("");
    setIndex(0);
  }, [text]);

  useEffect(() => {
    if (index < text.length) {
      const timeout = setTimeout(() => {
        setDisplayed(text.slice(0, index + 1));
        setIndex(index + 1);
      }, speed);
      return () => clearTimeout(timeout);
    } else if (onComplete) {
      onComplete();
    }
  }, [index, text, speed, onComplete]);

  return (
    <>
      {displayed}
      {index < text.length && <span className="animate-pulse text-cyan-400">|</span>}
    </>
  );
}

// =============================================================================
// ECRAN DE RESPIRATION
// =============================================================================

interface BreathingScreenProps {
  phrase: string;
  onComplete: () => void;
}

function BreathingScreen({ phrase, onComplete }: BreathingScreenProps) {
  useEffect(() => {
    const timer = setTimeout(onComplete, 2500);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/98">
      {/* Subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 via-transparent to-slate-900/50" />

      {/* Content */}
      <div className="relative text-center px-8 max-w-xl animate-fade-in">
        {/* Decorative line top */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <div className="w-16 h-px bg-gradient-to-r from-transparent to-slate-600" />
          <div className="w-2 h-2 rounded-full bg-slate-600" />
          <div className="w-16 h-px bg-gradient-to-l from-transparent to-slate-600" />
        </div>

        {/* Phrase */}
        <p className="text-lg text-slate-400 font-mono italic leading-relaxed">
          "{phrase}"
        </p>

        {/* Decorative line bottom */}
        <div className="flex items-center justify-center gap-4 mt-8">
          <div className="w-16 h-px bg-gradient-to-r from-transparent to-slate-600" />
          <div className="w-2 h-2 rounded-full bg-slate-600 animate-pulse" />
          <div className="w-16 h-px bg-gradient-to-l from-transparent to-slate-600" />
        </div>

        {/* Subtle progress indicator */}
        <div className="mt-12">
          <div className="w-32 h-0.5 bg-slate-800 rounded-full mx-auto overflow-hidden">
            <div className="h-full bg-slate-600 animate-progress-2s" />
          </div>
        </div>
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes progress-2s {
          from { width: 0%; }
          to { width: 100%; }
        }
        .animate-fade-in {
          animation: fade-in 0.8s ease-out;
        }
        .animate-progress-2s {
          animation: progress-2s 2.5s ease-out;
        }
      `}</style>
    </div>
  );
}

// =============================================================================
// EVENT DRAMATIC CONFIG
// =============================================================================

interface EventDrama {
  headerBg: string;
  headerText: string;
  icon: string;
  borderColor: string;
  glowColor: string;
  soundHint: string;
  dramaticLabel: string;
  watermark?: string;
  watermarkColor?: string;
}

const EVENT_DRAMA: Record<string, EventDrama> = {
  player_action: {
    headerBg: "bg-gradient-to-r from-blue-900 via-cyan-900 to-blue-900",
    headerText: "text-cyan-100",
    icon: "E",
    borderColor: "border-cyan-500/50",
    glowColor: "shadow-[0_0_30px_rgba(6,182,212,0.3)]",
    soundHint: "*transmission*",
    dramaticLabel: "ORDRES DE WASHINGTON",
    watermark: "*",
    watermarkColor: "text-blue-500/10",
  },
  adversary_action: {
    headerBg: "bg-gradient-to-r from-red-950 via-red-900 to-red-950",
    headerText: "text-red-100",
    icon: "M",
    borderColor: "border-red-500/60",
    glowColor: "shadow-[0_0_40px_rgba(239,68,68,0.4)]",
    soundHint: "*interception*",
    dramaticLabel: "MOSCOU A BOUGE",
    watermark: "M",
    watermarkColor: "text-red-500/10",
  },
  world_event: {
    headerBg: "bg-gradient-to-r from-purple-950 via-indigo-900 to-purple-950",
    headerText: "text-purple-100",
    icon: "W",
    borderColor: "border-purple-500/50",
    glowColor: "shadow-[0_0_25px_rgba(168,85,247,0.3)]",
    soundHint: "*telex AFP*",
    dramaticLabel: "FLASH INTERNATIONAL",
  },
  crisis: {
    headerBg: "bg-gradient-to-r from-orange-900 via-red-800 to-orange-900",
    headerText: "text-orange-100",
    icon: "!",
    borderColor: "border-orange-500/60",
    glowColor: "shadow-[0_0_50px_rgba(249,115,22,0.5)]",
    soundHint: "*ALERTE*",
    dramaticLabel: "CRISE MAJEURE",
    watermark: "!",
    watermarkColor: "text-orange-500/10",
  },
  resolution: {
    headerBg: "bg-gradient-to-r from-amber-900 via-yellow-800 to-amber-900",
    headerText: "text-amber-100",
    icon: "R",
    borderColor: "border-amber-500/50",
    glowColor: "shadow-[0_0_25px_rgba(245,158,11,0.3)]",
    soundHint: "*signature*",
    dramaticLabel: "RESOLUTION",
  },
  consequence: {
    headerBg: "bg-gradient-to-r from-slate-900 to-slate-800",
    headerText: "text-slate-200",
    icon: ">",
    borderColor: "border-slate-600",
    glowColor: "",
    soundHint: "*rapport*",
    dramaticLabel: "CONSEQUENCE",
  },
  time_passage: {
    headerBg: "bg-gradient-to-r from-slate-950 to-slate-900",
    headerText: "text-slate-400",
    icon: "T",
    borderColor: "border-slate-700",
    glowColor: "",
    soundHint: "",
    dramaticLabel: "LE TEMPS PASSE...",
  },
};

// =============================================================================
// DRAMATIC EVENT CARD (with NarrativeScene support)
// =============================================================================

interface EventCardProps {
  event: JumpEvent;
  isRevealing: boolean;
  onRevealComplete: () => void;
  isLast?: boolean;
  onNext?: () => void;
}

function EventCard({ event, isRevealing, onRevealComplete, isLast, onNext }: EventCardProps) {
  const [phase, setPhase] = useState<"intro" | "title" | "body" | "effects" | "done">("intro");

  const hasNarrativeScene = event.narrative_scene && event.narrative_scene.narrative;
  const drama = EVENT_DRAMA[event.type] || EVENT_DRAMA.world_event;
  const isCritical = event.importance === "critical";
  const isMajor = event.importance === "major";

  useEffect(() => {
    if (!isRevealing) {
      setPhase("done");
      return;
    }

    setPhase("intro");

    if (hasNarrativeScene) {
      const timer = setTimeout(() => {
        setPhase("done");
        onRevealComplete();
      }, 500);
      return () => clearTimeout(timer);
    }

    const timers = [
      setTimeout(() => setPhase("title"), 400),
      setTimeout(() => setPhase("body"), 1200),
      setTimeout(() => setPhase("effects"), 3000),
      setTimeout(() => {
        setPhase("done");
        onRevealComplete();
      }, 4000),
    ];

    return () => timers.forEach(clearTimeout);
  }, [isRevealing, onRevealComplete, hasNarrativeScene]);

  if (hasNarrativeScene && phase !== "intro") {
    return (
      <div className={`
        relative overflow-hidden rounded-xl
        ${isCritical ? "ring-4 ring-red-500/50" : ""}
        ${isMajor ? "ring-2 ring-amber-500/40" : ""}
        transition-all duration-500
      `}>
        <NarrativeScene
          scene={event.narrative_scene as NarrativeSceneData}
          onContinue={onNext}
          isLast={isLast}
        />
      </div>
    );
  }

  return (
    <div className={`
      relative overflow-hidden rounded-xl
      border-2 ${drama.borderColor}
      ${drama.glowColor}
      ${isCritical ? "ring-4 ring-red-500/50 animate-pulse" : ""}
      ${isMajor ? "ring-2 ring-amber-500/40" : ""}
      bg-[#0a0e17]
      transition-all duration-500
    `}>
      {/* CRT scanlines */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-20">
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.8) 2px, rgba(0,0,0,0.8) 4px)',
        }} />
      </div>

      {/* Header */}
      <div className={`relative ${drama.headerBg} px-5 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`text-3xl font-mono font-bold ${phase === "intro" ? "animate-bounce" : ""}`}>
              [{drama.icon}]
            </span>
            <div>
              <div className={`text-sm font-mono font-bold tracking-[0.15em] ${drama.headerText} uppercase`}>
                {drama.dramaticLabel}
              </div>
              <div className="text-[10px] text-white/40 font-mono italic mt-0.5">
                {drama.soundHint}
              </div>
            </div>
          </div>

          {isCritical && (
            <span className="px-3 py-1 bg-red-600 text-white text-xs font-mono font-bold rounded animate-pulse">
              CRITIQUE
            </span>
          )}
          {isMajor && !isCritical && (
            <span className="px-3 py-1 bg-amber-600 text-white text-xs font-mono font-bold rounded">
              MAJEUR
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="relative p-6">
        <h3 className={`text-xl font-bold text-slate-100 mb-4 min-h-[1.75rem] transition-all duration-500 ${
          phase === "intro" ? "opacity-0 translate-y-4" : "opacity-100 translate-y-0"
        }`}>
          {phase !== "intro" && (
            phase === "title" && isRevealing ? (
              <TypewriterText text={event.title_fr} speed={35} />
            ) : (
              event.title_fr
            )
          )}
        </h3>

        <div className={`min-h-[5rem] mb-5 transition-all duration-500 ${
          phase === "intro" || phase === "title" ? "opacity-0" : "opacity-100"
        }`}>
          {(phase === "body" || phase === "effects" || phase === "done") && (
            <p className="text-sm text-slate-300 leading-relaxed">
              {phase === "body" && isRevealing ? (
                <TypewriterText text={event.description_fr} speed={12} />
              ) : (
                event.description_fr
              )}
            </p>
          )}
        </div>

        {(event.target_zone || event.target_actor) && (
          <div className={`flex flex-wrap gap-2 mb-5 transition-all duration-500 ${
            phase === "effects" || phase === "done" ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}>
            {event.target_zone && (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-cyan-500/10 rounded-lg text-xs font-mono text-cyan-400 border border-cyan-500/30">
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                {event.target_zone.toUpperCase()}
              </span>
            )}
            {event.target_actor && (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 rounded-lg text-xs font-mono text-amber-400 border border-amber-500/30">
                {event.target_actor.toUpperCase()}
              </span>
            )}
          </div>
        )}

        {Object.keys(event.effects).length > 0 && !hasNarrativeScene && (
          <div className={`pt-5 border-t border-slate-800/50 transition-all duration-700 ${
            phase === "effects" || phase === "done" ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-3">
              Impact Detecte
            </div>
            <div className="flex flex-wrap gap-3">
              {Object.entries(event.effects).map(([key, value], idx) => {
                const isPositive = typeof value === "number" && value > 0;
                const isNegative = typeof value === "number" && value < 0;
                const isBig = typeof value === "number" && Math.abs(value) >= 10;

                return (
                  <span
                    key={key}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-mono font-bold
                      transition-all duration-300
                      ${isPositive
                        ? `bg-green-500/15 text-green-400 border border-green-500/30 ${isBig ? "animate-pulse shadow-lg shadow-green-500/20" : ""}`
                        : isNegative
                        ? `bg-red-500/15 text-red-400 border border-red-500/30 ${isBig ? "animate-pulse shadow-lg shadow-red-500/20" : ""}`
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                      }
                    `}
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    {key}: {isPositive ? "+" : ""}{value}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {drama.watermark && (
        <div className={`absolute bottom-4 right-6 text-8xl font-mono ${drama.watermarkColor || "text-slate-500/5"} pointer-events-none select-none`}>
          {drama.watermark}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TENSION PROGRESS BAR
// =============================================================================

interface ProgressBarProps {
  current: number;
  total: number;
}

function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = total > 0 ? (current / total) * 100 : 0;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-red-500/60 animate-ping" />
          </div>
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
            Evenement {current} / {total}
          </span>
        </div>
        <span className="text-xs font-mono text-cyan-400">
          {total - current > 0 ? `${total - current} a venir` : "Dernier evenement"}
        </span>
      </div>

      <div className="relative h-2.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-600 via-cyan-500 to-cyan-400 transition-all duration-700 ease-out"
          style={{ width: `${percentage}%` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
        </div>
      </div>

      <div className="relative h-2 mt-1.5 flex items-center">
        {Array.from({ length: Math.min(total, 15) }, (_, i) => {
          const pos = total > 1 ? (i / (total - 1)) * 100 : 50;
          const isPast = i < current;
          const isCurrent = i === current - 1;

          return (
            <div
              key={i}
              className={`absolute w-2 h-2 rounded-full transition-all duration-300 ${
                isCurrent
                  ? "bg-cyan-400 scale-150 shadow-lg shadow-cyan-400/50"
                  : isPast
                  ? "bg-cyan-500/60"
                  : "bg-slate-700"
              }`}
              style={{ left: `${pos}%`, transform: `translateX(-50%) ${isCurrent ? "scale(1.5)" : ""}` }}
            />
          );
        })}
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function EventPlayback() {
  const {
    gamePhase,
    playbackState,
    nextEvent,
    saveHere,
    intervene,
    isLoading,
  } = useNarrativeStore();

  const [currentEvent, setCurrentEvent] = useState<JumpEvent | null>(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [isRevealing, setIsRevealing] = useState(false);
  const [canAdvance, setCanAdvance] = useState(false);

  // NOUVEAU: Etat pour l'ecran de respiration
  const [showBreathing, setShowBreathing] = useState(false);
  const [breathingPhrase, setBreathingPhrase] = useState("");

  // Start playback when entering playback phase
  useEffect(() => {
    if (gamePhase === "playback" && !hasStarted) {
      // NOUVEAU: Montrer l'ecran de respiration d'abord
      setBreathingPhrase(getBreathingPhrase());
      setShowBreathing(true);
      setHasStarted(true);
    }
  }, [gamePhase, hasStarted]);

  // Reset when leaving playback
  useEffect(() => {
    if (gamePhase !== "playback") {
      setHasStarted(false);
      setCurrentEvent(null);
      setIsRevealing(false);
      setCanAdvance(false);
      setShowBreathing(false);
    }
  }, [gamePhase]);

  const handleBreathingComplete = useCallback(() => {
    setShowBreathing(false);
    loadNextEvent();
  }, []);

  const loadNextEvent = async () => {
    setIsRevealing(true);
    setCanAdvance(false);
    const event = await nextEvent();
    setCurrentEvent(event);
  };

  const handleRevealComplete = useCallback(() => {
    setIsRevealing(false);
    setCanAdvance(true);
  }, []);

  const handleNext = async () => {
    if (!canAdvance && !isLoading && isRevealing) {
      setIsRevealing(false);
      setCanAdvance(true);
      return;
    }
    await loadNextEvent();
  };

  const handleSave = async () => {
    await saveHere();
  };

  const handleIntervene = async () => {
    await intervene();
  };

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (gamePhase !== "playback" || showBreathing) return;

      if (e.code === "Space" || e.code === "Enter") {
        e.preventDefault();
        handleNext();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [gamePhase, canAdvance, isLoading, isRevealing, showBreathing]);

  // Don't show if not in playback
  if (gamePhase !== "playback") {
    return null;
  }

  // NOUVEAU: Ecran de respiration
  if (showBreathing) {
    return <BreathingScreen phrase={breathingPhrase} onComplete={handleBreathingComplete} />;
  }

  const canContinue = playbackState && playbackState.remaining > 0;

  // NOUVEAU: Texte dynamique du bouton
  const buttonInfo = getDynamicButtonText(
    playbackState?.current_index || 0,
    playbackState?.total_events || 0,
    currentEvent,
    canAdvance
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/95">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `
            radial-gradient(circle at center, rgba(6,182,212,0.3) 0%, transparent 70%),
            linear-gradient(rgba(6,182,212,0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6,182,212,0.2) 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 30px 30px, 30px 30px',
        }} />
      </div>

      {/* Content */}
      <div className="relative w-full max-w-2xl mx-4 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="absolute inset-0 w-3 h-3 rounded-full bg-red-500/50 animate-ping" />
            </div>
            <span className="text-sm font-mono text-slate-300 uppercase tracking-[0.15em]">
              Reception En Cours
            </span>
          </div>
          <span className="text-xs font-mono text-red-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            DIRECT
          </span>
        </div>

        {/* Progress */}
        {playbackState && (
          <ProgressBar
            current={playbackState.current_index}
            total={playbackState.total_events}
          />
        )}

        {/* Event card */}
        {currentEvent ? (
          <EventCard
            event={currentEvent}
            isRevealing={isRevealing}
            onRevealComplete={handleRevealComplete}
            isLast={!canContinue}
            onNext={handleNext}
          />
        ) : (
          <div className="bg-[#0a0e17] border-2 border-slate-800 rounded-xl p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-800/50 flex items-center justify-center">
              <div className="w-10 h-10 border-3 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
            </div>
            <p className="text-sm font-mono text-slate-500 uppercase tracking-wider">
              Reception du signal...
            </p>
          </div>
        )}

        {/* Controls */}
        <div className="mt-6 p-5 bg-[#0a0e17]/90 border border-slate-800 rounded-xl backdrop-blur-sm">
          <div className="flex items-center justify-between">
            {/* Left actions */}
            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all font-mono text-xs uppercase tracking-wider hover:scale-105"
              >
                Sauvegarder
              </button>

              {canContinue && (
                <button
                  onClick={handleIntervene}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 border border-orange-500/30 rounded-lg transition-all font-mono text-xs uppercase tracking-wider hover:scale-105"
                >
                  Intervenir
                </button>
              )}
            </div>

            {/* Next / Finish - BOUTON DYNAMIQUE */}
            <button
              onClick={handleNext}
              disabled={isLoading}
              className={`flex items-center gap-3 px-8 py-3 rounded-xl font-mono text-sm uppercase tracking-wider transition-all hover:scale-105 ${
                canContinue
                  ? "bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-lg shadow-cyan-500/30"
                  : "bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 text-white shadow-lg shadow-green-500/30"
              }`}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{canContinue ? buttonInfo.text : "Reprendre le controle"}</span>
                  <span className="text-lg">{canContinue ? ">" : ""}</span>
                </>
              )}
            </button>
          </div>

          {/* Keyboard hint */}
          <div className="mt-4 text-center">
            <span className="text-[10px] font-mono text-slate-600">
              <kbd className="px-2 py-1 bg-slate-800 rounded text-slate-400 mr-2">ESPACE</kbd>
              pour continuer
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EventPlayback;
