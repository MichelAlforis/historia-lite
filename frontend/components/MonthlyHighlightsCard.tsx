'use client';

import {
  MonthlyHighlights,
  COUNTRY_FLAGS,
  TIMELINE_REGION_NAMES_FR,
  MONTH_NAMES_FR,
  getImportanceColor,
} from '@/lib/types';
import { TrendingUp, TrendingDown, MapPin, AlertCircle, Calendar } from 'lucide-react';

interface MonthlyHighlightsCardProps {
  highlights: MonthlyHighlights;
  onEventClick?: (eventId: string) => void;
}

export default function MonthlyHighlightsCard({
  highlights,
  onEventClick,
}: MonthlyHighlightsCardProps) {
  const monthName = MONTH_NAMES_FR[highlights.month - 1];
  const criticalCount = highlights.by_importance[5] || 0;

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 shadow-sm border border-indigo-100">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-indigo-600" />
          <h3 className="font-bold text-lg text-indigo-900">
            {monthName} {highlights.year}
          </h3>
        </div>
        <span className="text-sm text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full">
          {highlights.total_events} evenements
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-gray-700 mb-4 leading-relaxed">
        {highlights.summary_fr}
      </p>

      {/* Stats Row */}
      <div className="flex gap-3 mb-4 flex-wrap">
        {criticalCount > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded text-xs">
            <AlertCircle className="w-3 h-3" />
            {criticalCount} critique{criticalCount > 1 ? 's' : ''}
          </div>
        )}
        {highlights.crisis_events_count > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">
            {highlights.crisis_events_count} crise{highlights.crisis_events_count > 1 ? 's' : ''}
          </div>
        )}
        {highlights.precursor_events_count > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs">
            {highlights.precursor_events_count} precurseur{highlights.precursor_events_count > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Top Events */}
      {highlights.top_events_data.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Faits marquants
          </h4>
          <div className="space-y-2">
            {highlights.top_events_data.map((event, idx) => (
              <div
                key={event.id}
                className="flex items-start gap-2 p-2 bg-white rounded-lg cursor-pointer hover:bg-indigo-50 transition-colors"
                onClick={() => onEventClick?.(event.id)}
              >
                <span className="text-lg">{COUNTRY_FLAGS[event.actor_country] || '🏳️'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 line-clamp-1">
                    {event.title_fr}
                  </p>
                  <p className="text-xs text-gray-500">{event.date}</p>
                </div>
                <span className={`px-1.5 py-0.5 text-[10px] rounded text-white ${getImportanceColor(event.importance)}`}>
                  {event.importance}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tensions & Relations */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Rising Tensions */}
        {highlights.rising_tensions.length > 0 && (
          <div className="p-2 bg-red-50 rounded-lg">
            <div className="flex items-center gap-1 text-red-700 text-xs font-medium mb-1">
              <TrendingUp className="w-3 h-3" />
              Tensions
            </div>
            <div className="space-y-1">
              {highlights.rising_tensions.slice(0, 2).map((pair) => {
                const [a, b] = pair.split('-');
                return (
                  <div key={pair} className="text-xs text-red-600">
                    {COUNTRY_FLAGS[a] || a} ↔ {COUNTRY_FLAGS[b] || b}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Improving Relations */}
        {highlights.improving_relations.length > 0 && (
          <div className="p-2 bg-green-50 rounded-lg">
            <div className="flex items-center gap-1 text-green-700 text-xs font-medium mb-1">
              <TrendingDown className="w-3 h-3" />
              Amelioration
            </div>
            <div className="space-y-1">
              {highlights.improving_relations.slice(0, 2).map((pair) => {
                const [a, b] = pair.split('-');
                return (
                  <div key={pair} className="text-xs text-green-600">
                    {COUNTRY_FLAGS[a] || a} ↔ {COUNTRY_FLAGS[b] || b}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Active Regions */}
      {highlights.active_regions.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-gray-500 text-xs mb-2">
            <MapPin className="w-3 h-3" />
            Regions actives
          </div>
          <div className="flex flex-wrap gap-1">
            {highlights.active_regions.map((region) => (
              <span
                key={region}
                className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded border border-gray-200"
              >
                {TIMELINE_REGION_NAMES_FR[region] || region}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Event Type Distribution (mini bar) */}
      {Object.keys(highlights.by_type).length > 0 && (
        <div className="mt-4 pt-3 border-t border-indigo-100">
          <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
            {Object.entries(highlights.by_type).map(([type, count]) => {
              const width = (count / highlights.total_events) * 100;
              const colors: Record<string, string> = {
                war: 'bg-red-500',
                diplomatic: 'bg-blue-500',
                economic: 'bg-green-500',
                military: 'bg-gray-600',
                crisis: 'bg-orange-500',
                political: 'bg-purple-500',
              };
              return (
                <div
                  key={type}
                  className={`${colors[type] || 'bg-gray-400'}`}
                  style={{ width: `${width}%` }}
                  title={`${type}: ${count}`}
                />
              );
            })}
          </div>
          <div className="flex justify-between mt-1 text-[10px] text-gray-400">
            <span>Distribution par type</span>
            <span>{Object.keys(highlights.by_type).length} types</span>
          </div>
        </div>
      )}
    </div>
  );
}
