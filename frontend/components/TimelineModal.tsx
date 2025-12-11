'use client';

import { useState, useEffect, useMemo } from 'react';
import { X, ChevronLeft, ChevronRight, Filter, Calendar, Loader2 } from 'lucide-react';
import {
  TimelineEvent,
  GameDate,
  TimelineEventType,
  COUNTRY_FLAGS,
  TIMELINE_EVENT_COLORS,
  TIMELINE_EVENT_TYPE_NAMES,
  MONTH_NAMES_FR,
  formatMonthYear,
} from '@/lib/types';
import { useGameStore } from '@/stores/gameStore';
import TimelineEventCard from './TimelineEventCard';

interface TimelineModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Filter options
const EVENT_TYPE_OPTIONS: TimelineEventType[] = [
  'war', 'diplomatic', 'economic', 'political', 'military',
  'internal', 'technology', 'cultural', 'crisis', 'player_action'
];

const IMPORTANCE_OPTIONS = [
  { value: 1, label: 'Tous' },
  { value: 2, label: 'Mineur+' },
  { value: 3, label: 'Notable+' },
  { value: 4, label: 'Important+' },
  { value: 5, label: 'Critique' },
];

export default function TimelineModal({ isOpen, onClose }: TimelineModalProps) {
  const {
    timeline,
    timelineLoading,
    year,
    month,
    viewingDate,
    setViewingDate,
    goToPreviousMonth,
    goToNextMonth,
    fetchTimeline,
    canGoBack,
    advanceMonth,
  } = useGameStore();

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [typeFilter, setTypeFilter] = useState<TimelineEventType | 'all'>('all');
  const [countryFilter, setCountryFilter] = useState<string>('all');
  const [importanceFilter, setImportanceFilter] = useState(1);

  // Selected event for detailed view
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // Load timeline on open
  useEffect(() => {
    if (isOpen && timeline.length === 0) {
      fetchTimeline();
    }
  }, [isOpen, timeline.length, fetchTimeline]);

  // Get current viewing date
  const displayDate = viewingDate || { year, month, day: 1 };
  const displayMonthYear = formatMonthYear(displayDate.year, displayDate.month, 'fr');

  // Check if we're viewing the current month (can advance game)
  const isCurrentMonth = displayDate.year === year && displayDate.month === month;

  // Get all countries mentioned in events
  const allCountries = useMemo(() => {
    const countries = new Set<string>();
    timeline.forEach(event => {
      countries.add(event.actor_country);
      event.target_countries.forEach(c => countries.add(c));
    });
    return Array.from(countries).sort();
  }, [timeline]);

  // Filter events for current month
  const eventsForMonth = useMemo(() => {
    let filtered = timeline.filter(event =>
      event.date.year === displayDate.year && event.date.month === displayDate.month
    );

    // Apply type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(e => e.type === typeFilter);
    }

    // Apply country filter
    if (countryFilter !== 'all') {
      filtered = filtered.filter(e =>
        e.actor_country === countryFilter ||
        e.target_countries.includes(countryFilter)
      );
    }

    // Apply importance filter
    if (importanceFilter > 1) {
      filtered = filtered.filter(e => e.importance >= importanceFilter);
    }

    // Sort by day within month (descending)
    return filtered.sort((a, b) => b.date.day - a.date.day);
  }, [timeline, displayDate, typeFilter, countryFilter, importanceFilter]);

  // Navigation handlers
  const handlePrevMonth = () => {
    if (viewingDate) {
      let newMonth = viewingDate.month - 1;
      let newYear = viewingDate.year;
      if (newMonth < 1) {
        newMonth = 12;
        newYear -= 1;
      }
      setViewingDate({ year: newYear, month: newMonth, day: 1, display: '', display_fr: '' });
    } else {
      goToPreviousMonth();
    }
  };

  const handleNextMonth = async () => {
    if (viewingDate) {
      let newMonth = viewingDate.month + 1;
      let newYear = viewingDate.year;
      if (newMonth > 12) {
        newMonth = 1;
        newYear += 1;
      }

      // If we're going past current date, advance the game
      const nextDate = { year: newYear, month: newMonth, day: 1 };
      const isAfterCurrent = (newYear * 12 + newMonth) > (year * 12 + month);

      if (isAfterCurrent) {
        await advanceMonth();
      }

      setViewingDate({ ...nextDate, display: '', display_fr: '' });
    } else {
      await goToNextMonth();
    }
  };

  // Event click handler
  const handleEventClick = (eventId: string) => {
    const event = timeline.find(e => e.id === eventId);
    if (event) {
      // Navigate to event's month
      setViewingDate({
        year: event.date.year,
        month: event.date.month,
        day: 1,
        display: '',
        display_fr: ''
      });
      setSelectedEventId(eventId);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[85vh] bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-stone-50 border-b">
          {/* Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevMonth}
              disabled={!canGoBack()}
              className="p-2 rounded-lg hover:bg-stone-200 disabled:opacity-30 disabled:cursor-not-allowed"
              title="Mois precedent"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="text-center min-w-[150px]">
              <h2 className="text-lg font-semibold">{displayMonthYear}</h2>
              <p className="text-xs text-stone-500">
                {eventsForMonth.length} evenement{eventsForMonth.length !== 1 ? 's' : ''}
              </p>
            </div>

            <button
              onClick={handleNextMonth}
              disabled={timelineLoading}
              className="p-2 rounded-lg hover:bg-stone-200 disabled:opacity-30"
              title={isCurrentMonth ? 'Avancer d\'un mois' : 'Mois suivant'}
            >
              {timelineLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg transition-colors ${
                showFilters ? 'bg-blue-100 text-blue-600' : 'hover:bg-stone-200'
              }`}
              title="Filtres"
            >
              <Filter className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-stone-200"
              title="Fermer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="px-4 py-3 bg-stone-100 border-b space-y-3">
            <div className="flex flex-wrap gap-4">
              {/* Type filter */}
              <div className="flex-1 min-w-[150px]">
                <label className="block text-xs font-medium text-stone-600 mb-1">Type</label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as TimelineEventType | 'all')}
                  className="w-full px-2 py-1.5 text-sm border rounded-lg bg-white"
                >
                  <option value="all">Tous les types</option>
                  {EVENT_TYPE_OPTIONS.map(type => (
                    <option key={type} value={type}>
                      {TIMELINE_EVENT_TYPE_NAMES[type]}
                    </option>
                  ))}
                </select>
              </div>

              {/* Country filter */}
              <div className="flex-1 min-w-[150px]">
                <label className="block text-xs font-medium text-stone-600 mb-1">Pays</label>
                <select
                  value={countryFilter}
                  onChange={(e) => setCountryFilter(e.target.value)}
                  className="w-full px-2 py-1.5 text-sm border rounded-lg bg-white"
                >
                  <option value="all">Tous les pays</option>
                  {allCountries.map(country => (
                    <option key={country} value={country}>
                      {COUNTRY_FLAGS[country]} {country}
                    </option>
                  ))}
                </select>
              </div>

              {/* Importance filter */}
              <div className="flex-1 min-w-[150px]">
                <label className="block text-xs font-medium text-stone-600 mb-1">Importance</label>
                <select
                  value={importanceFilter}
                  onChange={(e) => setImportanceFilter(Number(e.target.value))}
                  className="w-full px-2 py-1.5 text-sm border rounded-lg bg-white"
                >
                  {IMPORTANCE_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Quick filters */}
            <div className="flex flex-wrap gap-1">
              {EVENT_TYPE_OPTIONS.slice(0, 6).map(type => (
                <button
                  key={type}
                  onClick={() => setTypeFilter(typeFilter === type ? 'all' : type)}
                  className={`px-2 py-1 text-xs rounded ${
                    typeFilter === type
                      ? `${TIMELINE_EVENT_COLORS[type]} text-white`
                      : 'bg-white border hover:bg-stone-50'
                  }`}
                >
                  {TIMELINE_EVENT_TYPE_NAMES[type]}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Events list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {timelineLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-stone-400" />
            </div>
          ) : eventsForMonth.length === 0 ? (
            <div className="text-center py-12 text-stone-500">
              <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Aucun evenement pour ce mois</p>
              {(typeFilter !== 'all' || countryFilter !== 'all' || importanceFilter > 1) && (
                <button
                  onClick={() => {
                    setTypeFilter('all');
                    setCountryFilter('all');
                    setImportanceFilter(1);
                  }}
                  className="mt-2 text-sm text-blue-600 hover:underline"
                >
                  Reinitialiser les filtres
                </button>
              )}
            </div>
          ) : (
            eventsForMonth.map(event => (
              <TimelineEventCard
                key={event.id}
                event={event}
                expanded={selectedEventId === event.id}
                onEventClick={handleEventClick}
                showCausalChain={true}
              />
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-stone-50 border-t text-xs text-stone-500 flex items-center justify-between">
          <span>
            {timeline.length} evenements au total
          </span>
          {isCurrentMonth && (
            <button
              onClick={advanceMonth}
              disabled={timelineLoading}
              className="px-3 py-1 bg-emerald-500 text-white rounded-lg text-xs font-medium hover:bg-emerald-600 disabled:opacity-50"
            >
              Avancer d'un mois
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
