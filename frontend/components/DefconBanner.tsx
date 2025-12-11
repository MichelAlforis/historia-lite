'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Shield, Radiation } from 'lucide-react';

interface DefconBannerProps {
  level: number;
  show: boolean;
  onClose?: () => void;
}

const DEFCON_CONFIG: Record<number, {
  bg: string;
  border: string;
  text: string;
  glow: string;
  label: string;
  description: string;
  icon: 'radiation' | 'alert' | 'shield';
}> = {
  1: {
    bg: 'bg-red-950',
    border: 'border-red-500',
    text: 'text-red-100',
    glow: 'shadow-[0_0_30px_rgba(239,68,68,0.5)]',
    label: 'DEFCON 1',
    description: 'GUERRE NUCLEAIRE IMMINENTE',
    icon: 'radiation'
  },
  2: {
    bg: 'bg-red-900',
    border: 'border-red-400',
    text: 'text-red-100',
    glow: 'shadow-[0_0_20px_rgba(248,113,113,0.4)]',
    label: 'DEFCON 2',
    description: 'FORCES ARMEES PRETES AU COMBAT',
    icon: 'radiation'
  },
  3: {
    bg: 'bg-orange-900',
    border: 'border-orange-400',
    text: 'text-orange-100',
    glow: 'shadow-[0_0_15px_rgba(251,146,60,0.3)]',
    label: 'DEFCON 3',
    description: 'FORCES EN ETAT D\'ALERTE',
    icon: 'alert'
  },
  4: {
    bg: 'bg-yellow-900',
    border: 'border-yellow-400',
    text: 'text-yellow-100',
    glow: 'shadow-[0_0_10px_rgba(250,204,21,0.2)]',
    label: 'DEFCON 4',
    description: 'VIGILANCE RENFORCEE',
    icon: 'shield'
  },
  5: {
    bg: 'bg-green-900',
    border: 'border-green-400',
    text: 'text-green-100',
    glow: 'shadow-[0_0_10px_rgba(34,197,94,0.2)]',
    label: 'DEFCON 5',
    description: 'SITUATION NORMALE',
    icon: 'shield'
  }
};

export function DefconBanner({ level, show, onClose }: DefconBannerProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (show) {
      setIsExiting(false);
      const timer = setTimeout(() => {
        setIsExiting(true);
        setTimeout(() => {
          onClose?.();
        }, 500);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!show && !isExiting) return null;

  const config = DEFCON_CONFIG[level] || DEFCON_CONFIG[5];
  const Icon = config.icon === 'radiation' ? Radiation :
               config.icon === 'alert' ? AlertTriangle : Shield;

  return (
    <div
      className={`
        fixed top-0 left-0 right-0 z-[100]
        ${config.bg} ${config.border} ${config.text} ${config.glow}
        border-b-4 py-4 px-6
        ${isExiting ? 'defcon-banner-exit' : 'defcon-banner-enter'}
      `}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-4">
        <Icon
          className={`w-8 h-8 ${level <= 2 ? 'animate-alert-siren' : ''}`}
        />

        <div className="text-center">
          <div className="text-3xl font-bold tracking-[0.3em] font-mono">
            {config.label}
          </div>
          <div className="text-sm opacity-80 tracking-wider mt-1">
            {config.description}
          </div>
        </div>

        <Icon
          className={`w-8 h-8 ${level <= 2 ? 'animate-alert-siren' : ''}`}
        />
      </div>

      {level <= 2 && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500 to-transparent animate-pulse" />
        </div>
      )}
    </div>
  );
}

export default DefconBanner;
