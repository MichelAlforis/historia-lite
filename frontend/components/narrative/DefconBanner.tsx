"use client";

/**
 * DefconBanner - Dramatic DEFCON Display
 *
 * Military-style DEFCON indicator with appropriate urgency
 */

import React from "react";

interface DefconBannerProps {
  level: number;
}

const DEFCON_CONFIG: Record<
  number,
  {
    bg: string;
    glow: string;
    border: string;
    label: string;
    sublabel: string;
  }
> = {
  1: {
    bg: "bg-red-600",
    glow: "shadow-[0_0_30px_rgba(239,68,68,0.5)]",
    border: "border-red-400",
    label: "1",
    sublabel: "GUERRE",
  },
  2: {
    bg: "bg-red-700",
    glow: "shadow-[0_0_20px_rgba(185,28,28,0.4)]",
    border: "border-red-500",
    label: "2",
    sublabel: "ALERTE",
  },
  3: {
    bg: "bg-orange-600",
    glow: "shadow-[0_0_15px_rgba(234,88,12,0.3)]",
    border: "border-orange-500",
    label: "3",
    sublabel: "TENSION",
  },
  4: {
    bg: "bg-yellow-600",
    glow: "",
    border: "border-yellow-500",
    label: "4",
    sublabel: "VIGILANCE",
  },
  5: {
    bg: "bg-green-700",
    glow: "",
    border: "border-green-600",
    label: "5",
    sublabel: "NORMAL",
  },
};

export default function DefconBanner({ level }: DefconBannerProps) {
  const config = DEFCON_CONFIG[level] || DEFCON_CONFIG[5];
  const isCritical = level <= 2;

  return (
    <div
      className={`
        relative overflow-hidden rounded-lg
        ${config.border} border
        ${config.glow}
        ${isCritical ? "animate-pulse" : ""}
      `}
    >
      {/* Background */}
      <div className={`${config.bg} px-4 py-2`}>
        <div className="flex items-center gap-3">
          {/* DEFCON Label */}
          <div className="text-center">
            <div className="text-[10px] font-mono tracking-[0.2em] text-white/60 uppercase">
              DEFCON
            </div>
            <div className="text-2xl font-mono font-black text-white leading-none">
              {config.label}
            </div>
          </div>

          {/* Separator */}
          <div className="w-px h-8 bg-white/20" />

          {/* Status */}
          <div className="text-xs font-mono tracking-wider text-white/80 uppercase">
            {config.sublabel}
          </div>
        </div>
      </div>

      {/* Scan line effect for critical levels */}
      {isCritical && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent" />
        </div>
      )}
    </div>
  );
}
