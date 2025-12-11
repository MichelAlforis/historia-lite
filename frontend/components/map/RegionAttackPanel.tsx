'use client';

import { useState, useEffect } from 'react';
import { SubnationalRegion, AttackInfo, COUNTRY_FLAGS, ATTACK_RISK_NAMES, RESOURCE_TYPE_NAMES } from '@/lib/types';
import { getRegionAttackInfo } from '@/lib/api';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import AttackCostPreview from './AttackCostPreview';

interface RegionAttackPanelProps {
  region: SubnationalRegion;
  attackerId: string;
  onAttack?: (regionId: string, attackType: string) => void;
  onClose?: () => void;
}

export default function RegionAttackPanel({
  region,
  attackerId,
  onAttack,
  onClose,
}: RegionAttackPanelProps) {
  const [attackInfo, setAttackInfo] = useState<AttackInfo | null>(null);
  const [selectedAttackType, setSelectedAttackType] = useState<string>('limited_strike');
  const [isLoading, setIsLoading] = useState(true);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    getRegionAttackInfo(region.id)
      .then(setAttackInfo)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [region.id]);

  // Check if attack is high-risk (capital or strategic importance > 70)
  const isHighRiskAttack = region.is_capital_region || (attackInfo?.strategic_importance || 0) > 70;

  const handleAttackClick = () => {
    if (isHighRiskAttack) {
      setShowConfirmDialog(true);
    } else {
      executeAttack();
    }
  };

  const executeAttack = () => {
    setShowConfirmDialog(false);
    if (onAttack) {
      onAttack(region.id, selectedAttackType);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'high': return 'text-orange-400';
      case 'extreme': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-lg p-4 w-80">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-700 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg shadow-xl border border-slate-700 w-96">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span>{COUNTRY_FLAGS[region.country_id] || ''}</span>
              <span>Ciblage : {region.name_fr}</span>
            </h3>
            <p className="text-slate-400 text-sm">{region.country_id} - {region.region_type}</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors"
            >
              x
            </button>
          )}
        </div>
      </div>

      {/* Region Stats */}
      <div className="p-4 border-b border-slate-700">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Caracteristiques</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-slate-400">Population</span>
            <div className="text-white font-medium">{region.population_share}% du pays</div>
          </div>
          <div>
            <span className="text-slate-400">Economie</span>
            <div className="text-white font-medium">{region.economic_share}% du PIB</div>
          </div>
          <div>
            <span className="text-slate-400">Presence militaire</span>
            <div className="text-white font-medium">{region.military_presence}/100</div>
          </div>
          <div>
            <span className="text-slate-400">Valeur strategique</span>
            <div className="text-white font-medium">{region.strategic_value}/10</div>
          </div>
        </div>

        {/* Special characteristics */}
        <div className="mt-3 flex flex-wrap gap-2">
          {region.is_capital_region && (
            <span className="px-2 py-1 bg-amber-600/30 text-amber-400 text-xs rounded">
              Capitale
            </span>
          )}
          {region.is_coastal && (
            <span className="px-2 py-1 bg-blue-600/30 text-blue-400 text-xs rounded">
              Cotiere
            </span>
          )}
          {region.is_border_region && (
            <span className="px-2 py-1 bg-purple-600/30 text-purple-400 text-xs rounded">
              Frontaliere
            </span>
          )}
          {region.has_oil && (
            <span className="px-2 py-1 bg-yellow-600/30 text-yellow-400 text-xs rounded">
              Petrole
            </span>
          )}
          {region.has_strategic_resources && region.resource_type && (
            <span className="px-2 py-1 bg-green-600/30 text-green-400 text-xs rounded">
              {RESOURCE_TYPE_NAMES[region.resource_type] || region.resource_type}
            </span>
          )}
        </div>
      </div>

      {/* Attack Types */}
      {attackInfo && (
        <div className="p-4 border-b border-slate-700">
          <h4 className="text-sm font-semibold text-slate-300 mb-3">Type d'attaque</h4>
          <div className="space-y-2">
            {attackInfo.attack_types.map((attack) => (
              <label
                key={attack.type}
                className={`block p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedAttackType === attack.type
                    ? 'border-amber-500 bg-amber-500/10'
                    : 'border-slate-600 hover:border-slate-500'
                }`}
              >
                <input
                  type="radio"
                  name="attackType"
                  value={attack.type}
                  checked={selectedAttackType === attack.type}
                  onChange={() => setSelectedAttackType(attack.type)}
                  className="sr-only"
                />
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-white font-medium">{attack.name_fr}</div>
                    <div className="text-slate-400 text-xs mt-1">{attack.description}</div>
                  </div>
                  <span className={`text-xs font-semibold ${getRiskColor(attack.risk)}`}>
                    {ATTACK_RISK_NAMES[attack.risk] || attack.risk}
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Attack Cost Preview */}
      {attackInfo && (
        <div className="p-4 border-b border-slate-700">
          <AttackCostPreview
            region={region}
            attackInfo={attackInfo}
            attackType={selectedAttackType}
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="p-4 flex gap-3">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
        >
          Annuler
        </button>
        <button
          onClick={handleAttackClick}
          className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors font-semibold ${
            isHighRiskAttack
              ? 'bg-red-700 hover:bg-red-600'
              : 'bg-red-600 hover:bg-red-500'
          }`}
        >
          {isHighRiskAttack ? 'Attaque a haut risque' : 'Confirmer l\'attaque'}
        </button>
      </div>

      {/* High-risk attack confirmation dialog */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        type="danger"
        title="Attaque a haut risque"
        message={
          region.is_capital_region
            ? `Vous etes sur le point d'attaquer ${region.name_fr}, la CAPITALE de ${region.country_id}. Cela declenchera tres probablement une guerre totale.`
            : `${region.name_fr} a une importance strategique elevee (${attackInfo?.strategic_importance}/100). Une intervention internationale est probable.`
        }
        details={
          <div className="text-slate-300 space-y-1">
            <div className="flex justify-between">
              <span>Difficulte:</span>
              <span className="text-amber-400">{attackInfo?.attack_difficulty}/100</span>
            </div>
            <div className="flex justify-between">
              <span>Type d'attaque:</span>
              <span className="text-white">{selectedAttackType}</span>
            </div>
            {region.is_capital_region && (
              <div className="text-red-400 mt-2 font-semibold">
                GUERRE TOTALE PROBABLE
              </div>
            )}
          </div>
        }
        confirmText="Lancer l'attaque"
        cancelText="Annuler"
        onConfirm={executeAttack}
        onCancel={() => setShowConfirmDialog(false)}
      />
    </div>
  );
}
