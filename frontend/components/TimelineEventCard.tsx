'use client';

import { useState } from 'react';
import {
  TimelineEvent,
  CausalLink,
  COUNTRY_FLAGS,
  TIMELINE_EVENT_COLORS,
  TIMELINE_EVENT_TYPE_NAMES,
  getImportanceColor,
  getImportanceLabel,
  formatGameDate,
} from '@/lib/types';
import { ChevronDown, ChevronUp, Link2, ArrowRight, ArrowLeft, Zap } from 'lucide-react';

interface TimelineEventCardProps {
  event: TimelineEvent;
  onEventClick?: (eventId: string) => void;
  expanded?: boolean;
  showCausalChain?: boolean;
}

const EVENT_FAMILY_ICONS: Record<string, string> = {
  structural: '🏛️',
  tactical: '⚡',
  opportunity: '🎯',
  escalation: '📈',
  narrative: '📖',
  player: '🎮',
};

const EVENT_FAMILY_NAMES: Record<string, string> = {
  structural: 'Structurel',
  tactical: 'Tactique',
  opportunity: 'Opportunite',
  escalation: 'Escalade',
  narrative: 'Narratif',
  player: 'Joueur',
};

export default function TimelineEventCard({
  event,
  onEventClick,
  expanded: initialExpanded = false,
  showCausalChain = true,
}: TimelineEventCardProps) {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [showCauses, setShowCauses] = useState(false);
  const [showEffects, setShowEffects] = useState(false);

  const flag = COUNTRY_FLAGS[event.actor_country] || '🏳️';
  const typeColor = TIMELINE_EVENT_COLORS[event.type] || 'bg-gray-500';
  const importanceColor = getImportanceColor(event.importance);
  const familyIcon = EVENT_FAMILY_ICONS[event.family] || '📄';

  const hasCauses = event.caused_by_chain && event.caused_by_chain.length > 0;
  const hasEffects = event.effects_chain && event.effects_chain.length > 0;

  return (
    <div
      className={`bg-white rounded-lg border shadow-sm transition-all ${
        !event.read ? 'border-l-4 border-l-blue-500' : 'border-stone-200'
      } ${event.importance >= 4 ? 'ring-1 ring-amber-300' : ''}`}
    >
      {/* Header */}
      <div
        className="p-3 cursor-pointer hover:bg-stone-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Date row */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-stone-500">
            {event.date.display_fr || formatGameDate(event.date, 'fr')}
          </span>
          <div className="flex items-center gap-2">
            {/* Importance badge */}
            <span className={`px-1.5 py-0.5 text-[10px] rounded ${importanceColor} text-white`}>
              {getImportanceLabel(event.importance)}
            </span>
            {/* Type badge */}
            <span className={`px-1.5 py-0.5 text-[10px] rounded ${typeColor} text-white`}>
              {TIMELINE_EVENT_TYPE_NAMES[event.type]}
            </span>
          </div>
        </div>

        {/* Actor + Title */}
        <div className="flex items-start gap-2">
          <span className="text-xl">{flag}</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm text-stone-800 line-clamp-2">
              {event.title_fr || event.title}
            </h3>
            {/* Family + targets */}
            <div className="flex items-center gap-2 mt-1 text-xs text-stone-500">
              <span>{familyIcon} {EVENT_FAMILY_NAMES[event.family]}</span>
              {event.target_countries.length > 0 && (
                <span className="flex items-center gap-1">
                  <ArrowRight className="w-3 h-3" />
                  {event.target_countries.slice(0, 3).map(c => COUNTRY_FLAGS[c] || c).join(' ')}
                  {event.target_countries.length > 3 && ` +${event.target_countries.length - 3}`}
                </span>
              )}
            </div>
          </div>
          {/* Expand icon */}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-stone-400 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-stone-400 flex-shrink-0" />
          )}
        </div>

        {/* Ripple indicator */}
        {event.ripple_targets && event.ripple_targets.length > 0 && (
          <div className="mt-2 flex items-center gap-1 text-xs text-amber-600">
            <Zap className="w-3 h-3" />
            <span>Cascade: {event.ripple_targets.length} pays affectes</span>
          </div>
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-3 pb-3 border-t border-stone-100">
          {/* Description */}
          <p className="mt-3 text-sm text-stone-700 leading-relaxed">
            {event.description_fr || event.description}
          </p>

          {/* Causal chains */}
          {showCausalChain && (hasCauses || hasEffects) && (
            <div className="mt-4 space-y-3">
              {/* Causes */}
              {hasCauses && (
                <div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowCauses(!showCauses);
                    }}
                    className="flex items-center gap-2 text-xs font-medium text-stone-600 hover:text-stone-800"
                  >
                    <ArrowLeft className="w-3 h-3" />
                    <Link2 className="w-3 h-3" />
                    {showCauses ? 'Masquer' : 'Voir'} les {event.caused_by_chain.length} causes
                  </button>
                  {showCauses && (
                    <div className="mt-2 pl-4 border-l-2 border-blue-200 space-y-2">
                      {event.caused_by_chain.map((cause, idx) => (
                        <CausalLinkCard
                          key={cause.event_id}
                          link={cause}
                          direction="cause"
                          depth={idx}
                          onClick={() => onEventClick?.(cause.event_id)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Effects */}
              {hasEffects && (
                <div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowEffects(!showEffects);
                    }}
                    className="flex items-center gap-2 text-xs font-medium text-stone-600 hover:text-stone-800"
                  >
                    <Link2 className="w-3 h-3" />
                    <ArrowRight className="w-3 h-3" />
                    {showEffects ? 'Masquer' : 'Voir'} les {event.effects_chain.length} consequences
                  </button>
                  {showEffects && (
                    <div className="mt-2 pl-4 border-l-2 border-amber-200 space-y-2">
                      {event.effects_chain.map((effect, idx) => (
                        <CausalLinkCard
                          key={effect.event_id}
                          link={effect}
                          direction="effect"
                          depth={idx}
                          onClick={() => onEventClick?.(effect.event_id)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Ripple targets list */}
          {event.ripple_targets && event.ripple_targets.length > 0 && (
            <div className="mt-3 pt-3 border-t border-stone-100">
              <p className="text-xs text-stone-500 mb-1">Pays touches par effet cascade:</p>
              <div className="flex flex-wrap gap-1">
                {event.ripple_targets.map(countryId => (
                  <span
                    key={countryId}
                    className="px-2 py-0.5 bg-amber-50 text-amber-700 text-xs rounded"
                  >
                    {COUNTRY_FLAGS[countryId]} {countryId}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Sub-component for causal links
interface CausalLinkCardProps {
  link: CausalLink;
  direction: 'cause' | 'effect';
  depth: number;
  onClick?: () => void;
}

function CausalLinkCard({ link, direction, depth, onClick }: CausalLinkCardProps) {
  const strengthPercent = Math.round(link.strength * 100);
  const isStrong = link.strength >= 0.7;
  const isMedium = link.strength >= 0.4 && link.strength < 0.7;

  const linkTypeLabel = {
    direct: 'Direct',
    indirect: 'Indirect',
    probable: 'Probable',
  }[link.link_type];

  const bgColor = direction === 'cause' ? 'bg-blue-50' : 'bg-amber-50';
  const borderColor = direction === 'cause' ? 'border-blue-200' : 'border-amber-200';
  const textColor = direction === 'cause' ? 'text-blue-700' : 'text-amber-700';

  return (
    <div
      className={`p-2 rounded ${bgColor} border ${borderColor} cursor-pointer hover:opacity-80 transition-opacity`}
      onClick={onClick}
      style={{ marginLeft: `${depth * 8}px` }}
    >
      <div className="flex items-center justify-between">
        <span className={`text-xs font-medium ${textColor}`}>
          {link.title_fr || link.title}
        </span>
        <div className="flex items-center gap-1">
          <span className={`text-[10px] px-1 rounded ${
            isStrong ? 'bg-green-100 text-green-700' :
            isMedium ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-600'
          }`}>
            {strengthPercent}%
          </span>
          <span className="text-[10px] text-stone-400">{linkTypeLabel}</span>
        </div>
      </div>
      {link.date && (
        <p className="text-[10px] text-stone-500 mt-0.5">
          {link.date.display_fr || formatGameDate(link.date, 'fr')}
        </p>
      )}
    </div>
  );
}
