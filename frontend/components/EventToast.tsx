'use client';

import { useState, useEffect } from 'react';
import { GameEvent, COUNTRY_FLAGS } from '@/lib/types';
import {
  X,
  Swords,
  Handshake,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Zap,
  Globe,
  Users,
  Building,
  Atom,
  Flag,
  Flame,
  Crown,
  Banknote,
  Eye,
  Scale,
  Skull,
  Sparkles,
  Target,
  HeartHandshake,
  Bomb,
  Fuel,
} from 'lucide-react';

interface EventToastProps {
  events: GameEvent[];
  onDismiss: () => void;
  onViewHistory: () => void;
}

// Get icon based on event type
function getEventIcon(type: string, severity?: string) {
  const iconClass = "w-5 h-5";
  const typeLower = type.toLowerCase();

  // Procedural event types (Phase 17)
  if (typeLower.includes('diplomatic_crisis') || typeLower.includes('ally_under_attack')) {
    return <HeartHandshake className={`${iconClass} text-orange-500`} />;
  }
  if (typeLower.includes('diplomatic_opportunity') || typeLower.includes('alliance_offer')) {
    return <Sparkles className={`${iconClass} text-emerald-500`} />;
  }
  if (typeLower.includes('political_crisis') || typeLower.includes('coup')) {
    return <Crown className={`${iconClass} text-red-500`} />;
  }
  if (typeLower.includes('oil') || typeLower.includes('energy')) {
    return <Fuel className={`${iconClass} text-amber-600`} />;
  }
  if (typeLower.includes('scandal')) {
    return <Eye className={`${iconClass} text-purple-500`} />;
  }
  if (typeLower.includes('arms_race') || typeLower.includes('rivalry')) {
    return <Target className={`${iconClass} text-orange-500`} />;
  }
  if (typeLower.includes('intelligence')) {
    return <Eye className={`${iconClass} text-indigo-500`} />;
  }
  if (typeLower.includes('reform') || typeLower.includes('political')) {
    return <Scale className={`${iconClass} text-blue-500`} />;
  }
  if (typeLower.includes('regional_instability') || typeLower.includes('crisis')) {
    return <Flame className={`${iconClass} text-orange-500`} />;
  }
  if (typeLower.includes('boom') || typeLower.includes('positive') || typeLower.includes('growth')) {
    return <TrendingUp className={`${iconClass} text-emerald-500`} />;
  }
  if (typeLower.includes('recession') || typeLower.includes('warning')) {
    return <TrendingDown className={`${iconClass} text-red-500`} />;
  }

  // Original event types
  switch (typeLower) {
    case 'war':
    case 'conflict':
    case 'attack':
      return <Swords className={`${iconClass} text-red-500`} />;
    case 'alliance':
    case 'treaty':
    case 'peace':
      return <Handshake className={`${iconClass} text-emerald-500`} />;
    case 'economic_boom':
      return <TrendingUp className={`${iconClass} text-emerald-500`} />;
    case 'economic_crisis':
      return <TrendingDown className={`${iconClass} text-red-500`} />;
    case 'revolution':
    case 'instability':
      return <AlertTriangle className={`${iconClass} text-amber-500`} />;
    case 'military':
    case 'defense':
      return <Shield className={`${iconClass} text-sky-500`} />;
    case 'technology':
    case 'research':
      return <Zap className={`${iconClass} text-purple-500`} />;
    case 'diplomacy':
    case 'negotiation':
      return <Globe className={`${iconClass} text-sky-500`} />;
    case 'population':
    case 'migration':
      return <Users className={`${iconClass} text-stone-500`} />;
    case 'infrastructure':
      return <Building className={`${iconClass} text-stone-500`} />;
    case 'nuclear':
      return <Atom className={`${iconClass} text-red-600`} />;
    case 'sanctions':
      return <Banknote className={`${iconClass} text-amber-600`} />;
    case 'humanitarian':
      return <Users className={`${iconClass} text-blue-500`} />;
    case 'espionage':
      return <Eye className={`${iconClass} text-indigo-500`} />;
    default:
      return <Flag className={`${iconClass} text-stone-400`} />;
  }
}

// Get severity color based on event type
function getEventSeverity(type: string): 'critical' | 'warning' | 'info' | 'success' {
  const criticalTypes = [
    'war', 'nuclear', 'conflict', 'attack', 'coup',
    'political_crisis', 'ally_under_attack', 'diplomatic_crisis'
  ];
  const warningTypes = [
    'economic_crisis', 'recession', 'instability', 'revolution',
    'oil_crisis', 'scandal', 'arms_race', 'regional_instability',
    'recession_warning', 'rival_growing'
  ];
  const successTypes = [
    'alliance', 'treaty', 'peace', 'economic_boom', 'growth',
    'diplomatic_opportunity', 'alliance_offer', 'positive', 'boom'
  ];

  const typeLower = type.toLowerCase();
  if (criticalTypes.some(t => typeLower.includes(t))) return 'critical';
  if (warningTypes.some(t => typeLower.includes(t))) return 'warning';
  if (successTypes.some(t => typeLower.includes(t))) return 'success';
  return 'info';
}

function getSeverityStyles(severity: 'critical' | 'warning' | 'info' | 'success') {
  switch (severity) {
    case 'critical':
      return 'bg-red-50 border-red-300 ring-red-200 animate-pulse-subtle critical-border-pulse';
    case 'warning':
      return 'bg-amber-50 border-amber-200 ring-amber-100';
    case 'success':
      return 'bg-emerald-50 border-emerald-200 ring-emerald-100';
    default:
      return 'bg-sky-50 border-sky-200 ring-sky-100';
  }
}

// Get header gradient based on severity
function getHeaderGradient(severity: 'critical' | 'warning' | 'info' | 'success') {
  switch (severity) {
    case 'critical':
      return 'from-red-500/10 to-transparent';
    case 'warning':
      return 'from-amber-500/10 to-transparent';
    case 'success':
      return 'from-emerald-500/10 to-transparent';
    default:
      return 'from-sky-500/10 to-transparent';
  }
}

export default function EventToast({ events, onDismiss, onViewHistory }: EventToastProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  // Auto-advance through events (slower for critical events)
  useEffect(() => {
    if (events.length <= 1) return;

    const currentEvent = events[currentIndex];
    const severity = getEventSeverity(currentEvent?.type || '');
    // 6 seconds for critical events, 4 seconds for others
    const delay = severity === 'critical' ? 6000 : 4000;

    const timer = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % events.length);
    }, delay);

    return () => clearInterval(timer);
  }, [events.length, currentIndex]);

  // Handle dismiss with animation
  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss();
    }, 300);
  };

  if (!isVisible || events.length === 0) return null;

  const currentEvent = events[currentIndex];
  const severity = getEventSeverity(currentEvent.type);
  const severityStyles = getSeverityStyles(severity);
  const headerGradient = getHeaderGradient(severity);

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-md transition-all duration-300 ease-out
        ${isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}
        ${severity === 'critical' ? 'animate-bounce-once' : ''}
        ${currentEvent.type.toLowerCase().includes('coup') || currentEvent.type.toLowerCase().includes('war') ? 'animate-shake' : ''}`}
    >
      <div className={`rounded-2xl border-2 shadow-xl ring-4 ${severityStyles} overflow-hidden`}>
        {/* Header */}
        <div className={`flex items-center justify-between px-4 py-3 bg-gradient-to-r ${headerGradient}`}>
          <div className="flex items-center gap-2">
            {getEventIcon(currentEvent.type)}
            <span className="text-sm font-medium text-stone-600 uppercase tracking-wide">
              {currentEvent.type.replace(/_/g, ' ')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {events.length > 1 && (
              <span className="text-xs text-stone-400">
                {currentIndex + 1}/{events.length}
              </span>
            )}
            <button
              onClick={handleDismiss}
              className="p-1 hover:bg-white/80 rounded-lg transition"
            >
              <X className="w-4 h-4 text-stone-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="px-4 py-3">
          <div className="flex items-start gap-3">
            {currentEvent.country_id && (
              <span className="text-2xl" aria-hidden="true">
                {COUNTRY_FLAGS[currentEvent.country_id] || ''}
              </span>
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-stone-800">
                {currentEvent.title_fr || currentEvent.title}
              </h3>
              <p className="text-sm text-stone-600 mt-1 leading-relaxed">
                {currentEvent.description_fr || currentEvent.description}
              </p>
              <div className="text-xs text-stone-400 mt-2">
                Annee {currentEvent.year}
              </div>
            </div>
          </div>
        </div>

        {/* Footer with pagination dots */}
        {events.length > 1 && (
          <div className="px-4 py-2 bg-white/30 flex items-center justify-between">
            <div className="flex gap-1">
              {events.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentIndex
                      ? 'bg-stone-600 w-4'
                      : 'bg-stone-300 hover:bg-stone-400'
                  }`}
                  aria-label={`Voir evenement ${index + 1}`}
                />
              ))}
            </div>
            <button
              onClick={onViewHistory}
              className="text-xs text-stone-500 hover:text-stone-700 transition"
            >
              Voir l'historique
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Mini toast for single quick events
export function EventMiniToast({ event, onDismiss }: { event: GameEvent; onDismiss: () => void }) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsExiting(true);
      setTimeout(onDismiss, 300);
    }, 3000);

    return () => clearTimeout(timer);
  }, [onDismiss]);

  const severity = getEventSeverity(event.type);
  const severityStyles = getSeverityStyles(severity);

  return (
    <div
      className={`fixed bottom-24 right-4 z-40 max-w-sm transition-all duration-300
        ${isExiting ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}`}
    >
      <div className={`rounded-xl border shadow-lg ${severityStyles} px-4 py-3`}>
        <div className="flex items-center gap-3">
          {getEventIcon(event.type)}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-stone-800 truncate">
              {event.title_fr || event.title}
            </p>
          </div>
          <button onClick={() => { setIsExiting(true); setTimeout(onDismiss, 300); }}>
            <X className="w-4 h-4 text-stone-400" />
          </button>
        </div>
      </div>
    </div>
  );
}
