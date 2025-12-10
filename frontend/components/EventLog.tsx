'use client';

import { useState } from 'react';
import { GameEvent, EVENT_COLORS, COUNTRY_FLAGS } from '@/lib/types';

interface EventLogProps {
  events: GameEvent[];
  maxEvents?: number;
}

// Event type icons
const EVENT_ICONS: Record<string, string> = {
  war: '&#9876;',
  peace: '&#128330;',
  alliance: '&#129309;',
  sanction: '&#128683;',
  trade: '&#128176;',
  diplomacy: '&#127760;',
  military: '&#128737;',
  economy: '&#128200;',
  crisis: '&#9888;',
  nuclear: '&#9762;',
  election: '&#128499;',
  coup: '&#128481;',
  default: '&#128196;',
};

// Event type labels
const EVENT_LABELS: Record<string, string> = {
  war: 'Guerre',
  peace: 'Paix',
  alliance: 'Alliance',
  sanction: 'Sanction',
  trade: 'Commerce',
  diplomacy: 'Diplomatie',
  military: 'Militaire',
  economy: 'Economie',
  crisis: 'Crise',
  nuclear: 'Nucleaire',
  election: 'Election',
  coup: 'Coup d\'etat',
};

type FilterType = 'all' | 'war' | 'diplomacy' | 'economy' | 'military';

export function EventLog({ events, maxEvents = 20 }: EventLogProps) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [expanded, setExpanded] = useState(true);

  // Filter events
  const filteredEvents = events.filter((event) => {
    if (filter === 'all') return true;
    if (filter === 'war') return event.type === 'war' || event.type === 'peace';
    if (filter === 'diplomacy') return event.type === 'diplomacy' || event.type === 'alliance' || event.type === 'sanction';
    if (filter === 'economy') return event.type === 'economy' || event.type === 'trade';
    if (filter === 'military') return event.type === 'military' || event.type === 'nuclear';
    return true;
  });

  const displayEvents = filteredEvents.slice(-maxEvents).reverse();

  // Count events by type
  const warCount = events.filter(e => e.type === 'war' || e.type === 'peace').length;
  const diploCount = events.filter(e => e.type === 'diplomacy' || e.type === 'alliance' || e.type === 'sanction').length;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden h-full flex flex-col shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-indigo-900/50 to-gray-700 cursor-pointer hover:from-indigo-900/70 transition-all"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-sm">&#128220;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Journal</span>
            <div className="text-xs text-gray-400">
              {events.length} evenements | {warCount} conflits
            </div>
          </div>
        </div>
        <button
          className="text-gray-400 hover:text-white transition-transform duration-200"
          style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
          &#9650;
        </button>
      </div>

      <div className={`flex-1 flex flex-col transition-all duration-300 ease-in-out overflow-hidden ${expanded ? 'opacity-100' : 'max-h-0 opacity-0'}`}>
        {/* Filters */}
        <div className="px-3 py-2 bg-gray-750 border-b border-gray-700 flex flex-wrap gap-1">
          {([
            { key: 'all', label: 'Tous', icon: '&#128196;' },
            { key: 'war', label: 'Conflits', icon: '&#9876;' },
            { key: 'diplomacy', label: 'Diplo', icon: '&#127760;' },
            { key: 'economy', label: 'Eco', icon: '&#128200;' },
            { key: 'military', label: 'Mil', icon: '&#128737;' },
          ] as const).map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={(e) => {
                e.stopPropagation();
                setFilter(key);
              }}
              className={`px-2 py-1 text-xs rounded-lg flex items-center gap-1 transition-all ${
                filter === key
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
              }`}
            >
              <span dangerouslySetInnerHTML={{ __html: icon }} />
              {label}
            </button>
          ))}
        </div>

        {/* Events list */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 p-3 space-y-2">
          {displayEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <span className="text-4xl mb-2">&#128220;</span>
              <p className="text-sm">Aucun evenement</p>
            </div>
          ) : (
            displayEvents.map((event, index) => (
              <EventCard key={event.id} event={event} index={index} />
            ))
          )}
        </div>

        {/* Footer */}
        {displayEvents.length > 0 && (
          <div className="px-3 py-2 bg-gray-750 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
            <span>Affichage: {displayEvents.length}/{events.length}</span>
            <span>Derniers evenements</span>
          </div>
        )}
      </div>
    </div>
  );
}

// Individual event card
function EventCard({ event, index }: { event: GameEvent; index: number }) {
  const icon = EVENT_ICONS[event.type] || EVENT_ICONS.default;
  const colorClass = EVENT_COLORS[event.type] || 'bg-gray-500';
  const label = EVENT_LABELS[event.type] || event.type;

  // Determine severity for border color
  const isUrgent = event.type === 'war' || event.type === 'crisis' || event.type === 'coup' || event.type === 'nuclear';
  const isPositive = event.type === 'peace' || event.type === 'alliance' || event.type === 'trade';

  const borderColor = isUrgent
    ? 'border-l-red-500'
    : isPositive
    ? 'border-l-green-500'
    : 'border-l-gray-600';

  // Extract country codes from event for flags
  const extractCountries = (text: string): string[] => {
    const codes = Object.keys(COUNTRY_FLAGS);
    return codes.filter(code => text.includes(code));
  };

  const mentionedCountries = extractCountries(event.title_fr + ' ' + event.description_fr);

  return (
    <div
      className={`event-item p-3 bg-gradient-to-r from-gray-750 to-gray-800 rounded-lg border-l-4 ${borderColor} hover:from-gray-700 hover:to-gray-750 transition-all duration-200 group`}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      {/* Header */}
      <div className="flex items-start gap-2 mb-1">
        <div
          className={`w-7 h-7 rounded-lg ${colorClass.replace('bg-', 'bg-opacity-30 bg-')} flex items-center justify-center flex-shrink-0`}
        >
          <span className="text-sm" dangerouslySetInnerHTML={{ __html: icon }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <span className="font-medium text-gray-200 text-sm leading-tight group-hover:text-indigo-400 transition-colors">
              {event.title_fr}
            </span>
            <div className="flex items-center gap-1 flex-shrink-0">
              <span className={`text-xs px-1.5 py-0.5 rounded ${colorClass.replace('bg-', 'bg-opacity-20 bg-')} ${colorClass.replace('bg-', 'text-').replace('-500', '-300')}`}>
                {label}
              </span>
              <span className="text-xs text-gray-500 font-medium">
                {event.year}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-gray-400 mt-1.5 ml-9 leading-relaxed">
        {event.description_fr}
      </p>

      {/* Mentioned countries */}
      {mentionedCountries.length > 0 && (
        <div className="flex items-center gap-1 mt-2 ml-9">
          {mentionedCountries.slice(0, 4).map((code) => (
            <span
              key={code}
              className="text-base"
              title={code}
            >
              {COUNTRY_FLAGS[code]}
            </span>
          ))}
          {mentionedCountries.length > 4 && (
            <span className="text-xs text-gray-500">+{mentionedCountries.length - 4}</span>
          )}
        </div>
      )}
    </div>
  );
}
