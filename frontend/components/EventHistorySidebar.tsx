'use client';

import { useEffect } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { GameEvent, COUNTRY_FLAGS } from '@/lib/types';
import {
  X,
  History,
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
  ChevronRight
} from 'lucide-react';

interface EventHistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

// Get icon based on event type
function getEventIcon(type: string) {
  const iconClass = "w-4 h-4";
  switch (type.toLowerCase()) {
    case 'war':
    case 'conflict':
    case 'attack':
      return <Swords className={`${iconClass} text-red-500`} />;
    case 'alliance':
    case 'treaty':
    case 'peace':
      return <Handshake className={`${iconClass} text-emerald-500`} />;
    case 'economic_boom':
    case 'growth':
      return <TrendingUp className={`${iconClass} text-emerald-500`} />;
    case 'economic_crisis':
    case 'recession':
      return <TrendingDown className={`${iconClass} text-red-500`} />;
    case 'coup':
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
    default:
      return <Flag className={`${iconClass} text-stone-400`} />;
  }
}

// Get severity color based on event type
function getEventBgColor(type: string): string {
  const criticalTypes = ['war', 'nuclear', 'conflict', 'attack', 'coup'];
  const warningTypes = ['economic_crisis', 'recession', 'instability', 'revolution'];
  const successTypes = ['alliance', 'treaty', 'peace', 'economic_boom', 'growth'];

  const typeLower = type.toLowerCase();
  if (criticalTypes.some(t => typeLower.includes(t))) return 'bg-red-50 border-red-100';
  if (warningTypes.some(t => typeLower.includes(t))) return 'bg-amber-50 border-amber-100';
  if (successTypes.some(t => typeLower.includes(t))) return 'bg-emerald-50 border-emerald-100';
  return 'bg-stone-50 border-stone-100';
}

// Group events by year
function groupEventsByYear(events: GameEvent[]): Map<number, GameEvent[]> {
  const grouped = new Map<number, GameEvent[]>();
  events.forEach(event => {
    const year = event.year;
    if (!grouped.has(year)) {
      grouped.set(year, []);
    }
    grouped.get(year)!.push(event);
  });
  return grouped;
}

export default function EventHistorySidebar({ isOpen, onClose }: EventHistorySidebarProps) {
  const { eventHistory, fetchEventHistory, world } = useGameStore();

  // Fetch history when sidebar opens
  useEffect(() => {
    if (isOpen) {
      fetchEventHistory(100);
    }
  }, [isOpen, fetchEventHistory]);

  if (!isOpen) return null;

  const groupedEvents = groupEventsByYear(eventHistory);
  const sortedYears = Array.from(groupedEvents.keys()).sort((a, b) => b - a);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-stone-900/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-white shadow-2xl
        transform transition-transform duration-300 ease-out overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-100 flex items-center justify-between bg-stone-50">
          <div className="flex items-center gap-3">
            <History className="w-5 h-5 text-stone-500" />
            <div>
              <h2 className="text-lg font-semibold text-stone-800">Historique</h2>
              <p className="text-xs text-stone-500">
                {eventHistory.length} evenements
                {world && ` | Annee ${world.year}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-stone-100 rounded-xl transition"
          >
            <X className="w-5 h-5 text-stone-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {eventHistory.length === 0 ? (
            <div className="text-center py-12">
              <History className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-stone-500">Aucun evenement pour le moment</p>
              <p className="text-stone-400 text-sm mt-1">
                Avancez dans le temps pour voir l'histoire se derouler
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {sortedYears.map(year => (
                <div key={year}>
                  {/* Year header */}
                  <div className="sticky top-0 bg-white/95 backdrop-blur-sm py-2 mb-3 z-10">
                    <div className="flex items-center gap-2">
                      <div className="h-px flex-1 bg-stone-200" />
                      <span className="text-sm font-bold text-stone-600 px-2">
                        {year}
                      </span>
                      <div className="h-px flex-1 bg-stone-200" />
                    </div>
                  </div>

                  {/* Events for this year */}
                  <div className="space-y-2">
                    {groupedEvents.get(year)!.map((event, index) => (
                      <div
                        key={event.id || `${year}-${index}`}
                        className={`rounded-xl border p-3 transition-all hover:shadow-sm ${getEventBgColor(event.type)}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">
                            {getEventIcon(event.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              {event.country_id && (
                                <span className="text-lg" aria-hidden="true">
                                  {COUNTRY_FLAGS[event.country_id] || ''}
                                </span>
                              )}
                              <h3 className="font-medium text-stone-800 text-sm truncate">
                                {event.title_fr || event.title}
                              </h3>
                            </div>
                            <p className="text-xs text-stone-600 leading-relaxed line-clamp-2">
                              {event.description_fr || event.description}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-xs px-2 py-0.5 bg-white/80 rounded-full text-stone-500">
                                {event.type.replace(/_/g, ' ')}
                              </span>
                              {event.target_id && (
                                <span className="text-xs text-stone-400 flex items-center gap-1">
                                  <ChevronRight className="w-3 h-3" />
                                  {COUNTRY_FLAGS[event.target_id] || event.target_id}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-stone-100 bg-stone-50">
          <button
            onClick={onClose}
            className="w-full py-2 text-stone-600 hover:text-stone-800 text-sm transition"
          >
            Fermer
          </button>
        </div>
      </div>
    </>
  );
}
