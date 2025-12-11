'use client';

import { useMemo } from 'react';
import { SubnationalRegion, AttackInfo } from '@/lib/types';

interface AttackCostPreviewProps {
  region: SubnationalRegion;
  attackInfo: AttackInfo | null;
  attackType: string;
}

interface AttackCost {
  successChance: number;
  estimatedCasualties: { min: number; max: number };
  estimatedDamage: { min: number; max: number };
  diplomaticCost: number;
  resourceCost: number;
}

export default function AttackCostPreview({
  region,
  attackInfo,
  attackType,
}: AttackCostPreviewProps) {
  const cost = useMemo((): AttackCost => {
    const difficulty = attackInfo?.attack_difficulty || 50;
    const strategicImp = attackInfo?.strategic_importance || 50;

    // Base success chance by attack type
    const baseChance: Record<string, number> = {
      limited_strike: 70,
      invasion: 30,
      blockade: 50,
    };

    // Calculate success chance
    const successChance = Math.max(10, (baseChance[attackType] || 50) - Math.floor(difficulty / 2));

    // Estimated casualties
    const casualtyBase = attackType === 'invasion' ? 50 : attackType === 'blockade' ? 10 : 25;
    const casualtyModifier = difficulty / 50;
    const estimatedCasualties = {
      min: Math.floor(casualtyBase * casualtyModifier * 0.5),
      max: Math.floor(casualtyBase * casualtyModifier * 1.5),
    };

    // Estimated damage to region
    const damageBase = attackType === 'invasion' ? 40 : attackType === 'blockade' ? 10 : 25;
    const estimatedDamage = {
      min: Math.floor(damageBase * 0.6),
      max: Math.floor(damageBase * 1.4),
    };

    // Diplomatic cost
    let diplomaticCost = 30; // Base
    if (region.is_capital_region) diplomaticCost += 50;
    if (strategicImp > 70) diplomaticCost += 20;
    if (region.has_oil || region.has_strategic_resources) diplomaticCost += 10;

    // Resource cost (military points)
    const resourceCost = attackType === 'invasion' ? 30 : attackType === 'blockade' ? 15 : 20;

    return {
      successChance,
      estimatedCasualties,
      estimatedDamage,
      diplomaticCost: Math.min(100, diplomaticCost),
      resourceCost,
    };
  }, [region, attackInfo, attackType]);

  const getChanceColor = (chance: number) => {
    if (chance >= 60) return 'text-green-400';
    if (chance >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-slate-700/50 rounded-lg p-3 text-sm">
      <h5 className="text-slate-300 font-medium mb-2 text-xs uppercase tracking-wider">
        Estimation des couts
      </h5>

      <div className="space-y-2">
        {/* Success chance */}
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Chance de succes</span>
          <span className={`font-semibold ${getChanceColor(cost.successChance)}`}>
            {cost.successChance}%
          </span>
        </div>

        {/* Estimated casualties */}
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Pertes estimees</span>
          <span className="text-amber-400">
            {cost.estimatedCasualties.min}-{cost.estimatedCasualties.max}
          </span>
        </div>

        {/* Estimated damage */}
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Degats region</span>
          <span className="text-orange-400">
            {cost.estimatedDamage.min}-{cost.estimatedDamage.max}%
          </span>
        </div>

        {/* Diplomatic cost */}
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Cout diplomatique</span>
          <div className="flex items-center gap-1">
            <div className="w-16 h-1.5 bg-slate-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500"
                style={{ width: `${cost.diplomaticCost}%` }}
              />
            </div>
            <span className="text-red-400 text-xs">-{cost.diplomaticCost}</span>
          </div>
        </div>

        {/* Resource cost */}
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Cout militaire</span>
          <span className="text-blue-400">-{cost.resourceCost} pts</span>
        </div>
      </div>

      {/* Warnings */}
      {(region.is_capital_region || cost.successChance < 30) && (
        <div className="mt-3 pt-2 border-t border-slate-600">
          {region.is_capital_region && (
            <div className="text-xs text-red-400 flex items-center gap-1">
              <span>!</span>
              <span>Attaque sur capitale - risque extreme</span>
            </div>
          )}
          {cost.successChance < 30 && (
            <div className="text-xs text-amber-400 flex items-center gap-1">
              <span>!</span>
              <span>Faible chance de succes</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
