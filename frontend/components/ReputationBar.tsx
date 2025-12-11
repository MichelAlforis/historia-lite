'use client';

import { useMemo } from 'react';
import { Globe, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ReputationBarProps {
  reputation: number; // -100 to +100
  showLabel?: boolean;
  compact?: boolean;
}

// Labels de reputation selon le score
function getReputationLabel(score: number): { label: string; labelFr: string } {
  if (score >= 80) return { label: 'beacon_of_hope', labelFr: 'Phare de l\'Humanite' };
  if (score >= 60) return { label: 'world_leader', labelFr: 'Leader du Monde Libre' };
  if (score >= 40) return { label: 'trusted_ally', labelFr: 'Allie de Confiance' };
  if (score >= 20) return { label: 'respected_power', labelFr: 'Puissance Respectee' };
  if (score >= 0) return { label: 'neutral_actor', labelFr: 'Acteur Neutre' };
  if (score >= -20) return { label: 'controversial', labelFr: 'Controverse' };
  if (score >= -40) return { label: 'distrusted', labelFr: 'Defie' };
  if (score >= -60) return { label: 'isolated', labelFr: 'Isole' };
  if (score >= -80) return { label: 'pariah', labelFr: 'Regime Paria' };
  return { label: 'world_enemy', labelFr: 'Ennemi de l\'Humanite' };
}

// Couleur selon le score
function getReputationColor(score: number): string {
  if (score >= 60) return 'emerald';
  if (score >= 20) return 'sky';
  if (score >= -20) return 'stone';
  if (score >= -60) return 'amber';
  return 'red';
}

// Classes Tailwind selon la couleur
function getColorClasses(color: string) {
  const classes: Record<string, { bg: string; text: string; fill: string; border: string }> = {
    emerald: {
      bg: 'bg-emerald-500',
      text: 'text-emerald-600',
      fill: 'bg-emerald-400',
      border: 'border-emerald-300',
    },
    sky: {
      bg: 'bg-sky-500',
      text: 'text-sky-600',
      fill: 'bg-sky-400',
      border: 'border-sky-300',
    },
    stone: {
      bg: 'bg-stone-500',
      text: 'text-stone-600',
      fill: 'bg-stone-400',
      border: 'border-stone-300',
    },
    amber: {
      bg: 'bg-amber-500',
      text: 'text-amber-600',
      fill: 'bg-amber-400',
      border: 'border-amber-300',
    },
    red: {
      bg: 'bg-red-500',
      text: 'text-red-600',
      fill: 'bg-red-400',
      border: 'border-red-300',
    },
  };
  return classes[color] || classes.stone;
}

// Icone de tendance
function getTrendIcon(trend: number) {
  if (trend > 2) return <TrendingUp className="w-3 h-3 text-emerald-500" />;
  if (trend < -2) return <TrendingDown className="w-3 h-3 text-red-500" />;
  return <Minus className="w-3 h-3 text-stone-400" />;
}

export default function ReputationBar({
  reputation,
  showLabel = true,
  compact = false
}: ReputationBarProps) {
  const { labelFr } = useMemo(() => getReputationLabel(reputation), [reputation]);
  const color = useMemo(() => getReputationColor(reputation), [reputation]);
  const colorClasses = useMemo(() => getColorClasses(color), [color]);

  // Convertir -100/+100 en pourcentage 0-100 pour la barre
  const percentage = ((reputation + 100) / 200) * 100;

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <Globe className={`w-4 h-4 ${colorClasses.text}`} />
        <div className="w-24 h-2 bg-stone-200 rounded-full overflow-hidden relative">
          {/* Marqueur central (0) */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-stone-400 z-10" />
          {/* Barre de remplissage */}
          <div
            className={`h-full ${colorClasses.fill} transition-all duration-500`}
            style={{
              width: `${percentage}%`,
              marginLeft: reputation < 0 ? `${percentage}%` : '50%',
              transform: reputation < 0 ? 'translateX(-100%)' : 'none',
            }}
          />
        </div>
        <span className={`text-xs font-medium ${colorClasses.text}`}>
          {reputation > 0 ? '+' : ''}{reputation}
        </span>
      </div>
    );
  }

  return (
    <div className={`bg-white/80 backdrop-blur-sm rounded-xl p-3 border ${colorClasses.border}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Globe className={`w-4 h-4 ${colorClasses.text}`} />
          <span className="text-xs font-medium text-stone-500">Reputation Mondiale</span>
        </div>
        <span className={`text-sm font-bold ${colorClasses.text}`}>
          {reputation > 0 ? '+' : ''}{reputation}
        </span>
      </div>

      {/* Barre de reputation */}
      <div className="relative h-3 bg-gradient-to-r from-red-200 via-stone-200 to-emerald-200 rounded-full overflow-hidden mb-2">
        {/* Marqueur central (0) */}
        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-stone-500 z-10" />

        {/* Indicateur de position */}
        <div
          className={`absolute top-0 bottom-0 w-1.5 ${colorClasses.bg} rounded-full shadow-md z-20 transition-all duration-500`}
          style={{ left: `calc(${percentage}% - 3px)` }}
        />
      </div>

      {/* Labels extremes */}
      <div className="flex justify-between text-[10px] text-stone-400 mb-2">
        <span>Paria</span>
        <span>Neutre</span>
        <span>Leader</span>
      </div>

      {/* Label de reputation */}
      {showLabel && (
        <div className={`text-center py-1.5 rounded-lg ${colorClasses.bg}/10`}>
          <span className={`text-sm font-medium ${colorClasses.text}`}>
            {labelFr}
          </span>
        </div>
      )}
    </div>
  );
}

// Export pour utilisation dans d'autres composants
export { getReputationLabel, getReputationColor };
