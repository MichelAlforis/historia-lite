'use client';

import { useMemo } from 'react';
import { Crown, Shield, Sword, Scale, Handshake, TrendingUp, AlertTriangle, Sparkles } from 'lucide-react';

interface LeaderTrait {
  id: string;
  name_fr: string;
  description_fr: string;
  effects: Record<string, number>;
}

interface Leader {
  name: string;
  title: string;
  title_fr: string;
  start_year: number;
  traits: string[];
  traits_data: LeaderTrait[];
  portrait: string;
  ideology: string;
  approval_rating: number;
  years_in_power: number;
}

interface LeaderCardProps {
  leader: Leader | null;
  countryId: string;
  countryName: string;
  compact?: boolean;
}

// Map trait IDs to colors
function getTraitColor(traitId: string): string {
  const colors: Record<string, string> = {
    // Positive traits - green/blue
    diplomatic: 'bg-sky-100 text-sky-700 border-sky-200',
    pragmatic: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    moderate: 'bg-teal-100 text-teal-700 border-teal-200',
    charismatic: 'bg-violet-100 text-violet-700 border-violet-200',
    experienced: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    multilateral: 'bg-cyan-100 text-cyan-700 border-cyan-200',
    conciliatory: 'bg-green-100 text-green-700 border-green-200',
    reformist: 'bg-blue-100 text-blue-700 border-blue-200',
    pro_climate: 'bg-lime-100 text-lime-700 border-lime-200',

    // Neutral traits - amber/stone
    nationalist: 'bg-amber-100 text-amber-700 border-amber-200',
    conservative: 'bg-stone-100 text-stone-700 border-stone-200',
    populist: 'bg-orange-100 text-orange-700 border-orange-200',
    strategic: 'bg-slate-100 text-slate-700 border-slate-200',
    cautious: 'bg-zinc-100 text-zinc-700 border-zinc-200',
    centrist: 'bg-neutral-100 text-neutral-700 border-neutral-200',

    // Aggressive traits - red/rose
    militarist: 'bg-red-100 text-red-700 border-red-200',
    hawkish: 'bg-rose-100 text-rose-700 border-rose-200',
    revisionist: 'bg-pink-100 text-pink-700 border-pink-200',
    authoritarian: 'bg-red-100 text-red-800 border-red-300',
    totalitarian: 'bg-red-200 text-red-900 border-red-400',

    // Religious/ideological - purple
    islamist: 'bg-purple-100 text-purple-700 border-purple-200',
    theocratic: 'bg-purple-100 text-purple-700 border-purple-200',

    // Western alignment
    pro_western: 'bg-blue-100 text-blue-700 border-blue-200',
    pro_american: 'bg-blue-100 text-blue-700 border-blue-200',
    pro_european: 'bg-blue-100 text-blue-700 border-blue-200',
    european: 'bg-blue-100 text-blue-700 border-blue-200',

    // Eastern alignment
    anti_western: 'bg-red-100 text-red-700 border-red-200',
    pro_china: 'bg-red-100 text-red-700 border-red-200',
  };
  return colors[traitId] || 'bg-gray-100 text-gray-700 border-gray-200';
}

// Get icon for trait category
function getTraitIcon(traitId: string) {
  const iconClass = "w-3 h-3";

  if (['militarist', 'hawkish', 'revisionist'].includes(traitId)) {
    return <Sword className={iconClass} />;
  }
  if (['diplomatic', 'multilateral', 'conciliatory'].includes(traitId)) {
    return <Handshake className={iconClass} />;
  }
  if (['authoritarian', 'totalitarian', 'theocratic'].includes(traitId)) {
    return <Crown className={iconClass} />;
  }
  if (['cautious', 'moderate', 'conservative'].includes(traitId)) {
    return <Shield className={iconClass} />;
  }
  if (['reformist', 'economic_reformer', 'modernizer'].includes(traitId)) {
    return <TrendingUp className={iconClass} />;
  }
  if (['populist', 'nationalist', 'polarizing'].includes(traitId)) {
    return <AlertTriangle className={iconClass} />;
  }
  if (['charismatic', 'experienced', 'strategic'].includes(traitId)) {
    return <Sparkles className={iconClass} />;
  }
  return <Scale className={iconClass} />;
}

// Translate ideology to French
function getIdeologyFr(ideology: string): string {
  const translations: Record<string, string> = {
    liberal_democracy: 'Democratie liberale',
    social_democracy: 'Social-democratie',
    conservative_democracy: 'Democratie conservatrice',
    state_capitalism: 'Capitalisme d\'Etat',
    authoritarian_nationalism: 'Nationalisme autoritaire',
    hindu_nationalism: 'Nationalisme hindou',
    islamic_theocracy: 'Theocratie islamique',
    islamist_nationalism: 'Nationalisme islamiste',
    right_wing_nationalism: 'Nationalisme de droite',
    right_wing_populism: 'Populisme de droite',
    left_populism: 'Populisme de gauche',
    libertarian_populism: 'Populisme libertarien',
    nationalist_populism: 'Populisme nationaliste',
    military_authoritarianism: 'Autoritarisme militaire',
    authoritarian_monarchy: 'Monarchie autoritaire',
    juche_totalitarianism: 'Totalitarisme Juche',
    centrist: 'Centrisme',
    centrist_liberal: 'Liberalisme centriste',
  };
  return translations[ideology] || ideology;
}

export default function LeaderCard({ leader, countryId, countryName, compact = false }: LeaderCardProps) {
  if (!leader) {
    return (
      <div className="bg-stone-50 rounded-lg p-3 border border-stone-200">
        <p className="text-sm text-stone-500 italic">Aucun dirigeant connu</p>
      </div>
    );
  }

  const yearsInPower = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return currentYear - leader.start_year;
  }, [leader.start_year]);

  if (compact) {
    return (
      <div className="flex items-center gap-3 bg-stone-50 rounded-lg p-2 border border-stone-200">
        {/* Portrait placeholder */}
        <div className="w-10 h-10 bg-gradient-to-br from-stone-300 to-stone-400 rounded-full flex items-center justify-center">
          <Crown className="w-5 h-5 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-stone-800 truncate">{leader.name}</span>
          </div>
          <span className="text-xs text-stone-500">{leader.title_fr}</span>
        </div>

        {/* Top 2 traits */}
        <div className="flex gap-1">
          {leader.traits_data.slice(0, 2).map((trait) => (
            <span
              key={trait.id}
              className={`px-1.5 py-0.5 text-[10px] rounded border ${getTraitColor(trait.id)}`}
              title={trait.description_fr}
            >
              {trait.name_fr}
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-sm">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-stone-700 to-stone-800 px-4 py-3 text-white">
        <div className="flex items-center gap-3">
          {/* Portrait placeholder */}
          <div className="w-14 h-14 bg-gradient-to-br from-stone-400 to-stone-500 rounded-full flex items-center justify-center shadow-inner">
            <Crown className="w-7 h-7 text-white/80" />
          </div>

          <div className="flex-1">
            <h3 className="font-semibold text-lg leading-tight">{leader.name}</h3>
            <p className="text-stone-300 text-sm">{leader.title_fr} de {countryName}</p>
            <p className="text-stone-400 text-xs mt-0.5">
              Au pouvoir depuis {leader.start_year} ({yearsInPower} ans)
            </p>
          </div>
        </div>
      </div>

      {/* Traits section */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-medium text-stone-500 uppercase tracking-wide">Traits</span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {leader.traits_data.map((trait) => (
            <span
              key={trait.id}
              className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-lg border ${getTraitColor(trait.id)} cursor-help transition hover:scale-105`}
              title={trait.description_fr}
            >
              {getTraitIcon(trait.id)}
              {trait.name_fr}
            </span>
          ))}
        </div>

        {/* Ideology */}
        <div className="mt-3 pt-3 border-t border-stone-100">
          <div className="flex items-center justify-between">
            <span className="text-xs text-stone-500">Ideologie</span>
            <span className="text-xs font-medium text-stone-700">
              {getIdeologyFr(leader.ideology)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Export types for use in other components
export type { Leader, LeaderTrait };
