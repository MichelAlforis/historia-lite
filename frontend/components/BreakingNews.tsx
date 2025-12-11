'use client';

import { useState, useEffect, useCallback } from 'react';
import { GameEvent, COUNTRY_FLAGS } from '@/lib/types';
import { X, AlertTriangle, Swords, Atom, Crown, TrendingDown, Handshake, Shield } from 'lucide-react';

interface BreakingNewsProps {
  event: GameEvent | null;
  onDismiss: () => void;
}

// Types d'evenements qui declenchent les Breaking News
const BREAKING_NEWS_TYPES = [
  'war',
  'conflict',
  'attack',
  'nuclear',
  'coup',
  'political_crisis',
  'ally_under_attack',
  'diplomatic_crisis',
  'defcon_change',
  'bloc_change',
  'major_sanctions',
  'revolution',
];

// Verifie si un evenement merite un Breaking News
export function isBreakingNewsWorthy(event: GameEvent): boolean {
  const typeLower = event.type.toLowerCase();
  return BREAKING_NEWS_TYPES.some(t => typeLower.includes(t));
}

// Determine la severite pour le style
function getSeverity(type: string): 'critical' | 'urgent' | 'important' {
  const typeLower = type.toLowerCase();
  if (typeLower.includes('nuclear') || typeLower.includes('war') || typeLower.includes('attack')) {
    return 'critical';
  }
  if (typeLower.includes('coup') || typeLower.includes('crisis') || typeLower.includes('revolution')) {
    return 'urgent';
  }
  return 'important';
}

// Icone selon le type
function getNewsIcon(type: string) {
  const typeLower = type.toLowerCase();
  const iconClass = "w-5 h-5";

  if (typeLower.includes('nuclear')) return <Atom className={iconClass} />;
  if (typeLower.includes('war') || typeLower.includes('attack') || typeLower.includes('conflict')) {
    return <Swords className={iconClass} />;
  }
  if (typeLower.includes('coup') || typeLower.includes('revolution')) return <Crown className={iconClass} />;
  if (typeLower.includes('crisis')) return <TrendingDown className={iconClass} />;
  if (typeLower.includes('diplomatic') || typeLower.includes('alliance')) return <Handshake className={iconClass} />;
  if (typeLower.includes('defcon')) return <Shield className={iconClass} />;
  return <AlertTriangle className={iconClass} />;
}

// Couleurs selon severite
function getSeverityStyles(severity: 'critical' | 'urgent' | 'important') {
  switch (severity) {
    case 'critical':
      return {
        banner: 'bg-red-600',
        ticker: 'bg-red-700',
        text: 'text-white',
        glow: 'shadow-red-500/50',
      };
    case 'urgent':
      return {
        banner: 'bg-amber-600',
        ticker: 'bg-amber-700',
        text: 'text-white',
        glow: 'shadow-amber-500/50',
      };
    default:
      return {
        banner: 'bg-sky-600',
        ticker: 'bg-sky-700',
        text: 'text-white',
        glow: 'shadow-sky-500/50',
      };
  }
}

export default function BreakingNews({ event, onDismiss }: BreakingNewsProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  // Animation d'entree
  useEffect(() => {
    if (event) {
      setIsVisible(true);
      setIsExiting(false);
    }
  }, [event]);

  // Auto-dismiss apres 8 secondes
  useEffect(() => {
    if (!event || !isVisible) return;

    const timer = setTimeout(() => {
      handleDismiss();
    }, 8000);

    return () => clearTimeout(timer);
  }, [event, isVisible]);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss();
    }, 500);
  }, [onDismiss]);

  if (!event || !isVisible) return null;

  const severity = getSeverity(event.type);
  const styles = getSeverityStyles(severity);
  const icon = getNewsIcon(event.type);
  const countryFlag = event.country_id ? COUNTRY_FLAGS[event.country_id] : null;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-500 ease-out
        ${isExiting ? 'opacity-0 -translate-y-full' : 'opacity-100 translate-y-0'}`}
    >
      {/* Barre rouge BREAKING NEWS */}
      <div className={`${styles.banner} ${styles.text} shadow-2xl ${styles.glow}`}>
        {/* Header avec BREAKING NEWS */}
        <div className={`${styles.ticker} px-4 py-1 flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <span className="animate-pulse">
              <span className="inline-block w-2 h-2 bg-white rounded-full mr-2" />
            </span>
            <span className="font-black tracking-widest text-sm">
              {severity === 'critical' ? 'ALERTE CRITIQUE' :
               severity === 'urgent' ? 'FLASH INFO' : 'BREAKING NEWS'}
            </span>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-white/20 rounded transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Contenu principal */}
        <div className="px-6 py-4">
          <div className="flex items-start gap-4">
            {/* Icone + Drapeau */}
            <div className="flex flex-col items-center gap-1">
              {icon}
              {countryFlag && (
                <span className="text-2xl">{countryFlag}</span>
              )}
            </div>

            {/* Texte */}
            <div className="flex-1">
              <h2 className="text-xl font-bold leading-tight">
                {event.title_fr || event.title}
              </h2>
              <p className="text-sm opacity-90 mt-1 leading-relaxed">
                {event.description_fr || event.description}
              </p>
            </div>
          </div>
        </div>

        {/* Ticker defilant en bas */}
        <div className={`${styles.ticker} overflow-hidden py-1`}>
          <div className="animate-ticker whitespace-nowrap text-xs font-medium">
            <span className="mx-8">
              {event.title_fr || event.title}
            </span>
            <span className="mx-8 opacity-60">|</span>
            <span className="mx-8">
              {event.description_fr || event.description}
            </span>
            <span className="mx-8 opacity-60">|</span>
            <span className="mx-8">
              {event.title_fr || event.title}
            </span>
          </div>
        </div>
      </div>

      {/* Overlay sombre sur le reste de l'ecran */}
      <div
        className={`fixed inset-0 bg-black/30 -z-10 transition-opacity duration-500
          ${isExiting ? 'opacity-0' : 'opacity-100'}`}
        onClick={handleDismiss}
      />
    </div>
  );
}

// Styles CSS pour l'animation du ticker (a ajouter dans globals.css)
// @keyframes ticker {
//   0% { transform: translateX(0); }
//   100% { transform: translateX(-50%); }
// }
// .animate-ticker {
//   animation: ticker 20s linear infinite;
// }
