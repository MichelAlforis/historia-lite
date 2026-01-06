"use client";

/**
 * DramaticEffects - Screen-wide visual drama
 *
 * When things get tense, YOU FEEL IT.
 * - Screen shake on critical events
 * - Red overlay when DEFCON drops
 * - Flash effects on major events
 * - Tension vignette that pulses
 */

import React, { useEffect, useState, useCallback } from "react";

// =============================================================================
// SCREEN SHAKE
// =============================================================================

interface ShakeEffectProps {
  intensity: "light" | "medium" | "heavy" | "nuclear";
  duration?: number;
  onComplete?: () => void;
}

export function useScreenShake() {
  const [shake, setShake] = useState<ShakeEffectProps | null>(null);

  const triggerShake = useCallback((intensity: ShakeEffectProps["intensity"], duration = 500) => {
    setShake({ intensity, duration });
    setTimeout(() => setShake(null), duration);
  }, []);

  return { shake, triggerShake };
}

// =============================================================================
// DEFCON OVERLAY
// =============================================================================

interface DefconOverlayProps {
  defcon: number;
  worldTension: number;
}

export function DefconOverlay({ defcon, worldTension }: DefconOverlayProps) {
  const [pulsePhase, setPulsePhase] = useState(0);

  // Heartbeat effect when DEFCON is critical
  useEffect(() => {
    if (defcon <= 2) {
      const interval = setInterval(() => {
        setPulsePhase((p) => (p + 1) % 2);
      }, defcon === 1 ? 400 : 800);
      return () => clearInterval(interval);
    }
  }, [defcon]);

  // Calculate overlay intensity
  const getOverlayStyle = () => {
    if (defcon === 1) {
      return {
        background: `radial-gradient(ellipse at center,
          rgba(255, 0, 0, ${0.15 + pulsePhase * 0.1}) 0%,
          rgba(139, 0, 0, ${0.25 + pulsePhase * 0.1}) 50%,
          rgba(50, 0, 0, 0.4) 100%)`,
        animation: "pulse 0.4s ease-in-out infinite",
      };
    }
    if (defcon === 2) {
      return {
        background: `radial-gradient(ellipse at center,
          rgba(255, 50, 0, ${0.08 + pulsePhase * 0.05}) 0%,
          rgba(139, 0, 0, ${0.12 + pulsePhase * 0.05}) 70%,
          transparent 100%)`,
      };
    }
    if (defcon === 3 && worldTension > 70) {
      return {
        background: `radial-gradient(ellipse at center,
          rgba(255, 100, 0, 0.05) 0%,
          rgba(200, 50, 0, 0.08) 70%,
          transparent 100%)`,
      };
    }
    return {};
  };

  if (defcon > 3 || (defcon === 3 && worldTension <= 70)) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 pointer-events-none z-40 transition-all duration-300"
      style={getOverlayStyle()}
    >
      {/* DEFCON 1: Nuclear warning stripes at edges */}
      {defcon === 1 && (
        <>
          {/* Top warning stripe */}
          <div className="absolute top-0 left-0 right-0 h-2 bg-[repeating-linear-gradient(90deg,#ff0000,#ff0000_20px,#000000_20px,#000000_40px)] animate-pulse" />
          {/* Bottom warning stripe */}
          <div className="absolute bottom-0 left-0 right-0 h-2 bg-[repeating-linear-gradient(90deg,#ff0000,#ff0000_20px,#000000_20px,#000000_40px)] animate-pulse" />
        </>
      )}
    </div>
  );
}

// =============================================================================
// TENSION VIGNETTE
// =============================================================================

interface TensionVignetteProps {
  tension: number; // 0-100
}

export function TensionVignette({ tension }: TensionVignetteProps) {
  if (tension < 50) return null;

  const intensity = Math.min(0.6, (tension - 50) / 100);
  const spreadFactor = Math.max(40, 70 - (tension - 50) * 0.5);

  return (
    <div
      className="fixed inset-0 pointer-events-none z-30 transition-all duration-1000"
      style={{
        background: `radial-gradient(ellipse at center,
          transparent ${spreadFactor}%,
          rgba(20, 0, 0, ${intensity}) 100%)`,
      }}
    />
  );
}

// =============================================================================
// EVENT FLASH
// =============================================================================

interface FlashEffectProps {
  type: "success" | "warning" | "danger" | "critical" | "soviet";
  message?: string;
}

export function useEventFlash() {
  const [flash, setFlash] = useState<FlashEffectProps | null>(null);

  const triggerFlash = useCallback((type: FlashEffectProps["type"], message?: string) => {
    setFlash({ type, message });
    setTimeout(() => setFlash(null), 1500);
  }, []);

  return { flash, triggerFlash };
}

export function EventFlash({ flash }: { flash: FlashEffectProps | null }) {
  if (!flash) return null;

  const colors: Record<FlashEffectProps["type"], { bg: string; border: string; text: string }> = {
    success: {
      bg: "rgba(34, 197, 94, 0.15)",
      border: "border-green-500",
      text: "text-green-400",
    },
    warning: {
      bg: "rgba(245, 158, 11, 0.15)",
      border: "border-amber-500",
      text: "text-amber-400",
    },
    danger: {
      bg: "rgba(239, 68, 68, 0.15)",
      border: "border-red-500",
      text: "text-red-400",
    },
    critical: {
      bg: "rgba(220, 38, 38, 0.25)",
      border: "border-red-600",
      text: "text-red-500",
    },
    soviet: {
      bg: "rgba(185, 28, 28, 0.2)",
      border: "border-red-700",
      text: "text-red-400",
    },
  };

  const config = colors[flash.type];

  return (
    <div
      className={`fixed inset-0 pointer-events-none z-50 flex items-center justify-center animate-pulse`}
      style={{ backgroundColor: config.bg }}
    >
      {flash.message && (
        <div className={`${config.border} border-2 ${config.text} px-8 py-4 rounded-lg bg-black/80 font-mono text-xl uppercase tracking-widest animate-bounce`}>
          {flash.message}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// ALERT BANNER (Breaking News Style)
// =============================================================================

interface AlertBannerProps {
  message: string;
  type: "breaking" | "urgent" | "flash" | "soviet";
  onDismiss?: () => void;
}

export function AlertBanner({ message, type, onDismiss }: AlertBannerProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setVisible(false);
      onDismiss?.();
    }, 5000);
    return () => clearTimeout(timeout);
  }, [onDismiss]);

  if (!visible) return null;

  const styles: Record<AlertBannerProps["type"], { bg: string; text: string; label: string }> = {
    breaking: {
      bg: "bg-red-600",
      text: "text-white",
      label: "⚠ FLASH INFO",
    },
    urgent: {
      bg: "bg-amber-600",
      text: "text-black",
      label: "⚡ URGENT",
    },
    flash: {
      bg: "bg-cyan-600",
      text: "text-white",
      label: "📡 TÉLEX",
    },
    soviet: {
      bg: "bg-red-800",
      text: "text-white",
      label: "☭ MOSCOU",
    },
  };

  const config = styles[type];

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 ${config.bg} ${config.text} animate-slide-down`}>
      <div className="max-w-4xl mx-auto px-4 py-2 flex items-center gap-4">
        {/* Blinking label */}
        <span className="font-mono text-xs font-bold tracking-wider animate-pulse shrink-0">
          {config.label}
        </span>

        {/* Scrolling text effect */}
        <div className="flex-1 overflow-hidden">
          <p className="font-mono text-sm whitespace-nowrap animate-marquee">
            {message} • {message} • {message}
          </p>
        </div>

        {/* Dismiss */}
        <button
          onClick={() => {
            setVisible(false);
            onDismiss?.();
          }}
          className="shrink-0 opacity-70 hover:opacity-100 transition-opacity"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// DRAMATIC WRAPPER (Combines all effects)
// =============================================================================

interface DramaticWrapperProps {
  children: React.ReactNode;
  defcon: number;
  worldTension: number;
  shake?: ShakeEffectProps | null;
}

export function DramaticWrapper({
  children,
  defcon,
  worldTension,
  shake,
}: DramaticWrapperProps) {
  const getShakeClass = () => {
    if (!shake) return "";
    switch (shake.intensity) {
      case "light":
        return "animate-shake-light";
      case "medium":
        return "animate-shake-medium";
      case "heavy":
        return "animate-shake-heavy";
      case "nuclear":
        return "animate-shake-nuclear";
      default:
        return "";
    }
  };

  return (
    <div className={`relative min-h-screen ${getShakeClass()}`}>
      {/* Tension vignette */}
      <TensionVignette tension={worldTension} />

      {/* DEFCON overlay */}
      <DefconOverlay defcon={defcon} worldTension={worldTension} />

      {/* Main content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}

// =============================================================================
// TYPEWRITER TEXT (For dramatic reveals)
// =============================================================================

interface TypewriterTextProps {
  text: string;
  speed?: number;
  className?: string;
  onComplete?: () => void;
}

export function TypewriterText({
  text,
  speed = 30,
  className = "",
  onComplete,
}: TypewriterTextProps) {
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
    <span className={className}>
      {displayed}
      {index < text.length && <span className="animate-pulse">▊</span>}
    </span>
  );
}

// =============================================================================
// CSS ANIMATIONS (Add to global CSS or Tailwind config)
// =============================================================================

/*
Add these to your tailwind.config.js or global CSS:

@keyframes shake-light {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}

@keyframes shake-medium {
  0%, 100% { transform: translateX(0) translateY(0); }
  25% { transform: translateX(-4px) translateY(2px); }
  50% { transform: translateX(4px) translateY(-2px); }
  75% { transform: translateX(-4px) translateY(2px); }
}

@keyframes shake-heavy {
  0%, 100% { transform: translateX(0) translateY(0) rotate(0); }
  20% { transform: translateX(-8px) translateY(4px) rotate(-1deg); }
  40% { transform: translateX(8px) translateY(-4px) rotate(1deg); }
  60% { transform: translateX(-8px) translateY(4px) rotate(-1deg); }
  80% { transform: translateX(8px) translateY(-4px) rotate(1deg); }
}

@keyframes shake-nuclear {
  0%, 100% { transform: translateX(0) translateY(0) rotate(0); }
  10% { transform: translateX(-15px) translateY(10px) rotate(-2deg); }
  20% { transform: translateX(15px) translateY(-10px) rotate(2deg); }
  30% { transform: translateX(-15px) translateY(10px) rotate(-2deg); }
  40% { transform: translateX(15px) translateY(-10px) rotate(2deg); }
  50% { transform: translateX(-15px) translateY(10px) rotate(-2deg); }
  60% { transform: translateX(15px) translateY(-10px) rotate(2deg); }
  70% { transform: translateX(-15px) translateY(10px) rotate(-2deg); }
  80% { transform: translateX(15px) translateY(-10px) rotate(2deg); }
  90% { transform: translateX(-10px) translateY(5px) rotate(-1deg); }
}

@keyframes marquee {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

@keyframes slide-down {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(0); }
}

.animate-shake-light { animation: shake-light 0.3s ease-in-out; }
.animate-shake-medium { animation: shake-medium 0.4s ease-in-out; }
.animate-shake-heavy { animation: shake-heavy 0.5s ease-in-out; }
.animate-shake-nuclear { animation: shake-nuclear 1s ease-in-out; }
.animate-marquee { animation: marquee 10s linear infinite; }
.animate-slide-down { animation: slide-down 0.3s ease-out; }
*/

export default DramaticWrapper;
