'use client';

import { useState } from 'react';
import {
  StrategicOverview,
  TensionTrend,
  TimelineAlert,
  CrisisArc,
  WorldMood,
  COUNTRY_FLAGS,
  TIMELINE_REGION_NAMES_FR,
  ERA_NAMES_FR,
  ERA_COLORS,
  PHASE_NAMES_FR,
  PHASE_COLORS,
  ALERT_LEVEL_COLORS,
  ALERT_LEVEL_ICONS,
  getTensionColor,
  getStabilityColor,
  getDangerColor,
  GeopoliticalEra,
  CrisisPhase,
} from '@/lib/types';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Shield,
  Target,
  Zap,
  Globe,
  Users,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import MonthlyHighlightsCard from './MonthlyHighlightsCard';

interface StrategicTimelineViewProps {
  overview: StrategicOverview;
  onEventClick?: (eventId: string) => void;
  onCrisisClick?: (crisisId: string) => void;
}

export default function StrategicTimelineView({
  overview,
  onEventClick,
  onCrisisClick,
}: StrategicTimelineViewProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('highlights');

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="space-y-4">
      {/* Summary Bar */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-stone-200">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Danger Level */}
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getDangerColor(overview.summary.danger_level)}`}>
              <span className="text-white font-bold">{overview.summary.danger_level}</span>
            </div>
            <div>
              <p className="text-xs text-gray-500">Niveau de danger</p>
              <p className="font-semibold">
                {overview.summary.danger_level >= 70 ? 'Critique' :
                 overview.summary.danger_level >= 50 ? 'Eleve' :
                 overview.summary.danger_level >= 30 ? 'Modere' : 'Faible'}
              </p>
            </div>
          </div>

          {/* Stability Index */}
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getStabilityColor(overview.summary.stability_index)}`}>
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Stabilite mondiale</p>
              <p className="font-semibold">{overview.summary.stability_index}/100</p>
            </div>
          </div>

          {/* World Mood */}
          {overview.world_mood && (
            <div className="flex items-center gap-3">
              <div className={`px-3 py-2 rounded-lg ${ERA_COLORS[overview.world_mood.era as GeopoliticalEra] || 'bg-gray-500'}`}>
                <Globe className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Ere actuelle</p>
                <p className="font-semibold">{overview.world_mood.era_fr}</p>
              </div>
            </div>
          )}

          {/* Events Analyzed */}
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-indigo-500" />
            <div>
              <p className="text-xs text-gray-500">Evenements analyses</p>
              <p className="font-semibold">{overview.trends.total_events_analyzed}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Column 1: Active Crises */}
        <div className="space-y-4">
          <SectionHeader
            title="Foyers de crise"
            icon={<Zap className="w-4 h-4" />}
            count={overview.active_crises.length}
            expanded={expandedSection === 'crises'}
            onToggle={() => toggleSection('crises')}
            color="red"
          />
          {expandedSection === 'crises' && (
            <div className="space-y-3">
              {overview.active_crises.length === 0 ? (
                <p className="text-sm text-gray-500 italic p-3 bg-gray-50 rounded-lg">
                  Aucune crise active
                </p>
              ) : (
                overview.active_crises.map((crisis) => (
                  <CrisisCard
                    key={crisis.id}
                    crisis={crisis}
                    onClick={() => onCrisisClick?.(crisis.id)}
                  />
                ))
              )}
            </div>
          )}
        </div>

        {/* Column 2: Trends */}
        <div className="space-y-4">
          <SectionHeader
            title="Tendances"
            icon={<TrendingUp className="w-4 h-4" />}
            count={overview.trends.tension_trends.length}
            expanded={expandedSection === 'trends'}
            onToggle={() => toggleSection('trends')}
            color="amber"
          />
          {expandedSection === 'trends' && (
            <div className="space-y-3">
              {/* Tension Trends */}
              <div className="bg-white rounded-lg p-3 border border-stone-200">
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Tensions par paire
                </h4>
                <div className="space-y-2">
                  {overview.trends.tension_trends.slice(0, 5).map((trend) => (
                    <TensionTrendRow key={trend.pair} trend={trend} />
                  ))}
                  {overview.trends.tension_trends.length === 0 && (
                    <p className="text-sm text-gray-400 italic">Aucune tension notable</p>
                  )}
                </div>
              </div>

              {/* Most Active Actors */}
              <div className="bg-white rounded-lg p-3 border border-stone-200">
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  <Users className="w-3 h-3 inline mr-1" />
                  Acteurs les plus actifs
                </h4>
                <div className="space-y-1">
                  {overview.trends.most_active_actors.slice(0, 5).map((actor, idx) => (
                    <div key={actor.country} className="flex items-center justify-between text-sm">
                      <span>
                        {idx + 1}. {COUNTRY_FLAGS[actor.country] || '🏳️'} {actor.country}
                      </span>
                      <span className="text-gray-500">{actor.event_count} evt</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rising Event Types */}
              {overview.trends.rising_event_types.length > 0 && (
                <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
                  <h4 className="text-xs font-semibold text-amber-700 uppercase mb-2">
                    Types en hausse
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {overview.trends.rising_event_types.map((type) => (
                      <span
                        key={type}
                        className="px-2 py-0.5 bg-amber-100 text-amber-800 text-xs rounded"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Column 3: Alerts & Predictions */}
        <div className="space-y-4">
          <SectionHeader
            title="Alertes"
            icon={<AlertTriangle className="w-4 h-4" />}
            count={overview.trends.alerts.length}
            expanded={expandedSection === 'alerts'}
            onToggle={() => toggleSection('alerts')}
            color="blue"
          />
          {expandedSection === 'alerts' && (
            <div className="space-y-3">
              {overview.trends.alerts.length === 0 ? (
                <p className="text-sm text-gray-500 italic p-3 bg-gray-50 rounded-lg">
                  Aucune alerte active
                </p>
              ) : (
                overview.trends.alerts.map((alert, idx) => (
                  <AlertCard key={idx} alert={alert} />
                ))
              )}

              {/* Key Regions */}
              {overview.summary.key_regions.length > 0 && (
                <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-200">
                  <h4 className="text-xs font-semibold text-indigo-700 uppercase mb-2">
                    <Target className="w-3 h-3 inline mr-1" />
                    Regions cles
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {overview.summary.key_regions.map((region) => (
                      <span
                        key={region}
                        className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs rounded"
                      >
                        {TIMELINE_REGION_NAMES_FR[region] || region}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Monthly Highlights (Expanded by default) */}
      <div>
        <SectionHeader
          title="Resume mensuel"
          icon={<Activity className="w-4 h-4" />}
          expanded={expandedSection === 'highlights'}
          onToggle={() => toggleSection('highlights')}
          color="purple"
        />
        {expandedSection === 'highlights' && (
          <div className="mt-3">
            <MonthlyHighlightsCard
              highlights={overview.monthly_highlights}
              onEventClick={onEventClick}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// --- Sub-components ---

interface SectionHeaderProps {
  title: string;
  icon: React.ReactNode;
  count?: number;
  expanded: boolean;
  onToggle: () => void;
  color: 'red' | 'amber' | 'blue' | 'purple';
}

function SectionHeader({ title, icon, count, expanded, onToggle, color }: SectionHeaderProps) {
  const colors = {
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  };

  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 bg-white rounded-lg border border-stone-200 hover:bg-stone-50 transition-colors"
    >
      <div className="flex items-center gap-2">
        <div className={`p-1.5 rounded ${colors[color]} text-white`}>{icon}</div>
        <span className="font-semibold text-gray-800">{title}</span>
        {count !== undefined && (
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
            {count}
          </span>
        )}
      </div>
      {expanded ? (
        <ChevronUp className="w-4 h-4 text-gray-400" />
      ) : (
        <ChevronDown className="w-4 h-4 text-gray-400" />
      )}
    </button>
  );
}

interface CrisisCardProps {
  crisis: {
    id: string;
    name_fr: string;
    phase: string;
    intensity: number;
    actors: string[];
  };
  onClick?: () => void;
}

function CrisisCard({ crisis, onClick }: CrisisCardProps) {
  const phaseColor = PHASE_COLORS[crisis.phase as CrisisPhase] || 'bg-gray-100 border-gray-500 text-gray-800';
  const phaseName = PHASE_NAMES_FR[crisis.phase as CrisisPhase] || crisis.phase;

  return (
    <div
      className={`p-3 rounded-lg border-l-4 cursor-pointer hover:opacity-90 transition-opacity ${phaseColor}`}
      onClick={onClick}
    >
      <h4 className="font-semibold text-sm mb-1">{crisis.name_fr}</h4>
      <div className="flex items-center justify-between text-xs">
        <span>Phase: {phaseName}</span>
        <span className="font-medium">{crisis.intensity}%</span>
      </div>
      <div className="flex gap-1 mt-2">
        {crisis.actors.slice(0, 4).map((actor) => (
          <span key={actor} className="text-lg" title={actor}>
            {COUNTRY_FLAGS[actor] || '🏳️'}
          </span>
        ))}
        {crisis.actors.length > 4 && (
          <span className="text-xs text-gray-500">+{crisis.actors.length - 4}</span>
        )}
      </div>
    </div>
  );
}

interface TensionTrendRowProps {
  trend: TensionTrend;
}

function TensionTrendRow({ trend }: TensionTrendRowProps) {
  const colorClass = getTensionColor(trend.tension_delta);
  const isRising = trend.tension_delta > 0;

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span>{COUNTRY_FLAGS[trend.country_a] || trend.country_a}</span>
        <span className="text-gray-400">↔</span>
        <span>{COUNTRY_FLAGS[trend.country_b] || trend.country_b}</span>
      </div>
      <div className={`flex items-center gap-1 ${colorClass}`}>
        {isRising ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        <span className="text-sm font-medium">
          {isRising ? '+' : ''}{trend.tension_delta.toFixed(0)}
        </span>
      </div>
    </div>
  );
}

interface AlertCardProps {
  alert: TimelineAlert;
}

function AlertCard({ alert }: AlertCardProps) {
  const colorClass = ALERT_LEVEL_COLORS[alert.level] || ALERT_LEVEL_COLORS.info;
  const icon = ALERT_LEVEL_ICONS[alert.level] || ALERT_LEVEL_ICONS.info;

  return (
    <div className={`p-3 rounded-lg border-l-4 ${colorClass}`}>
      <div className="flex items-start gap-2">
        <span className="text-lg">{icon}</span>
        <div className="flex-1">
          <p className="text-sm font-medium">{alert.message}</p>
          {alert.countries.length > 0 && (
            <div className="flex gap-1 mt-1">
              {alert.countries.map((c) => (
                <span key={c} className="text-sm">
                  {COUNTRY_FLAGS[c] || c}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="text-xs opacity-60">{alert.severity}%</div>
      </div>
    </div>
  );
}
