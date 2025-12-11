'use client';

import React from 'react';
import { CrisisArc, CrisisPhase, PHASE_NAMES_FR, PHASE_COLORS, COUNTRY_FLAGS } from '@/lib/types';
import { AlertTriangle, TrendingUp, TrendingDown, Minus, Users, Radio } from 'lucide-react';

interface CrisisArcDisplayProps {
  crisis: CrisisArc;
  compact?: boolean;
}

const PHASE_ORDER: CrisisPhase[] = ['latent', 'escalation', 'climax', 'resolution', 'aftermath'];

const CrisisArcDisplay: React.FC<CrisisArcDisplayProps> = ({ crisis, compact = false }) => {
  const currentPhaseIndex = PHASE_ORDER.indexOf(crisis.current_phase);

  // Momentum indicator
  const getMomentumIcon = () => {
    if (crisis.momentum > 20) {
      return <TrendingUp className="w-4 h-4 text-red-500" />;
    } else if (crisis.momentum < -20) {
      return <TrendingDown className="w-4 h-4 text-green-500" />;
    }
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getMomentumText = () => {
    if (crisis.momentum > 50) return 'En forte expansion';
    if (crisis.momentum > 20) return 'En expansion';
    if (crisis.momentum < -50) return 'En net recul';
    if (crisis.momentum < -20) return 'En recul';
    return 'Stable';
  };

  // Intensity color
  const getIntensityColor = () => {
    if (crisis.intensity >= 75) return 'bg-red-500';
    if (crisis.intensity >= 50) return 'bg-orange-500';
    if (crisis.intensity >= 25) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (compact) {
    return (
      <div className={`p-3 rounded-lg border-l-4 ${PHASE_COLORS[crisis.current_phase]}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium text-sm">{crisis.name_fr}</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/50">
            {PHASE_NAMES_FR[crisis.current_phase]}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${getIntensityColor()} transition-all`}
              style={{ width: `${crisis.intensity}%` }}
            />
          </div>
          <span className="text-xs text-gray-600">{crisis.intensity}%</span>
          {getMomentumIcon()}
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-lg border-l-4 ${PHASE_COLORS[crisis.current_phase]} bg-opacity-50`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-bold text-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {crisis.name_fr}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            {crisis.primary_actors.map(actor => (
              <span key={actor} className="text-lg" title={actor}>
                {COUNTRY_FLAGS[actor] || actor}
              </span>
            ))}
          </div>
        </div>
        <div className="text-right">
          <span className="px-2 py-1 rounded-full text-sm font-medium bg-white/70">
            {PHASE_NAMES_FR[crisis.current_phase]}
          </span>
          <div className="text-xs text-gray-600 mt-1">
            {crisis.months_active} mois
          </div>
        </div>
      </div>

      {/* Phase Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center gap-1">
          {PHASE_ORDER.map((phase, idx) => (
            <div
              key={phase}
              className={`h-2 flex-1 rounded transition-all ${
                idx <= currentPhaseIndex
                  ? idx === currentPhaseIndex
                    ? 'bg-current animate-pulse'
                    : PHASE_COLORS[phase].split(' ')[0]
                  : 'bg-gray-200'
              }`}
              title={PHASE_NAMES_FR[phase]}
            />
          ))}
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>Latente</span>
          <span>Climax</span>
          <span>Apres-crise</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Intensity */}
        <div className="bg-white/50 rounded-lg p-2">
          <div className="text-xs text-gray-500 mb-1">Intensite</div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getIntensityColor()} transition-all`}
                style={{ width: `${crisis.intensity}%` }}
              />
            </div>
            <span className="text-sm font-medium">{crisis.intensity}%</span>
          </div>
        </div>

        {/* Momentum */}
        <div className="bg-white/50 rounded-lg p-2">
          <div className="text-xs text-gray-500 mb-1">Momentum</div>
          <div className="flex items-center gap-2">
            {getMomentumIcon()}
            <span className="text-sm">{getMomentumText()}</span>
          </div>
        </div>

        {/* Media Attention */}
        <div className="bg-white/50 rounded-lg p-2">
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            <Radio className="w-3 h-3" />
            Attention media
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all"
                style={{ width: `${crisis.media_attention}%` }}
              />
            </div>
            <span className="text-sm">{crisis.media_attention}%</span>
          </div>
        </div>

        {/* International Involvement */}
        <div className="bg-white/50 rounded-lg p-2">
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            <Users className="w-3 h-3" />
            Pays impliques
          </div>
          <span className="text-sm font-medium">{crisis.international_involvement}</span>
        </div>
      </div>

      {/* Spillover Risk */}
      {crisis.spillover_risk > 0.3 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-sm">
          <span className="font-medium text-amber-700">
            Risque de contagion: {Math.round(crisis.spillover_risk * 100)}%
          </span>
        </div>
      )}

      {/* AI Prediction */}
      {crisis.ai_predicted_outcome && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500">Prediction IA</div>
          <div className="text-sm">
            Issue probable: <span className="font-medium">{crisis.ai_predicted_outcome}</span>
            <span className="text-xs text-gray-500 ml-2">
              ({Math.round(crisis.ai_confidence * 100)}% confiance)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default CrisisArcDisplay;
