'use client';

import { useState, useEffect, useCallback } from 'react';
import { useGameStore } from '@/stores/gameStore';
import { getStrategicAdvice } from '@/lib/api';
import { StrategicAdvice, StrategicRecommendation, StrategicThreat, COUNTRY_FLAGS } from '@/lib/types';
import AIAdvisorPanel from './AIAdvisorPanel';
import {
  TrendingUp,
  Swords,
  Handshake,
  Building,
  AlertTriangle,
  Shield,
  Atom,
  Target,
  Users,
  Sparkles,
  Loader2,
  X,
  ChevronRight,
  Brain,
  Crown,
  AlertCircle,
  Bot,
} from 'lucide-react';

interface ConseilModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ConseilModal({ isOpen, onClose }: ConseilModalProps) {
  const { playerCountryId, sendPlayerCommand, isLoading, world } = useGameStore();
  const [advice, setAdvice] = useState<StrategicAdvice | null>(null);
  const [loadingAdvice, setLoadingAdvice] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'threats' | 'opportunities' | 'diplomatic' | 'ai'>('recommendations');

  // Fetch strategic advice when modal opens
  const fetchAdvice = useCallback(async () => {
    if (!playerCountryId) return;

    setLoadingAdvice(true);
    setError(null);

    try {
      const data = await getStrategicAdvice(playerCountryId, true);
      setAdvice(data);
    } catch (err) {
      setError('Erreur lors du chargement des conseils strategiques');
      console.error('Strategic advice error:', err);
    } finally {
      setLoadingAdvice(false);
    }
  }, [playerCountryId]);

  useEffect(() => {
    if (isOpen && playerCountryId) {
      fetchAdvice();
    }
  }, [isOpen, playerCountryId, fetchAdvice]);

  const handleExecuteRecommendation = async (rec: StrategicRecommendation) => {
    if (rec.command) {
      await sendPlayerCommand(rec.command);
      onClose();
    }
  };

  const getActionIcon = (action: string) => {
    const iconClass = "w-5 h-5";
    switch (action) {
      case 'ECONOMIE': return <TrendingUp className={iconClass} />;
      case 'MILITAIRE': return <Swords className={iconClass} />;
      case 'TECHNOLOGIE': return <Sparkles className={iconClass} />;
      case 'STABILITE': return <Building className={iconClass} />;
      case 'INFLUENCE': return <Users className={iconClass} />;
      case 'SANCTIONS': return <AlertTriangle className={iconClass} />;
      case 'ALLIANCE': return <Handshake className={iconClass} />;
      case 'NUCLEAIRE': return <Atom className={iconClass} />;
      default: return <Target className={iconClass} />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'ECONOMIE': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'MILITAIRE': return 'bg-red-50 text-red-700 border-red-200';
      case 'TECHNOLOGIE': return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'STABILITE': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'INFLUENCE': return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'SANCTIONS': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'ALLIANCE': return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'NUCLEAIRE': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-stone-50 text-stone-700 border-stone-200';
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'medium': return 'bg-amber-100 text-amber-700';
      case 'low': return 'bg-stone-100 text-stone-600';
      default: return 'bg-stone-100 text-stone-600';
    }
  };

  const getThreatLevelText = (level: string) => {
    switch (level) {
      case 'critical': return 'Critique';
      case 'high': return 'Eleve';
      case 'medium': return 'Modere';
      case 'low': return 'Faible';
      default: return 'Inconnu';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-stone-900/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-3xl mx-4 max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 pt-6 pb-4 border-b border-stone-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-xl">
                <Brain className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-stone-800">
                  Conseils strategiques
                </h2>
                {advice && (
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-stone-500">
                      Objectif: <span className="font-medium text-stone-700">{advice.strategic_goal_fr}</span>
                    </span>
                    <span className="text-stone-300">|</span>
                    <span className="text-sm text-stone-500">
                      Rang: <span className="font-medium text-stone-700">#{advice.power_rank}/{advice.total_countries}</span>
                    </span>
                    {advice.ollama_available && (
                      <>
                        <span className="text-stone-300">|</span>
                        <span className="flex items-center gap-1 text-xs text-emerald-600">
                          <Sparkles className="w-3 h-3" />
                          IA Active
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-stone-100 rounded-xl transition"
            >
              <X className="w-5 h-5 text-stone-400" />
            </button>
          </div>

          {/* Tabs */}
          {advice && (
            <div className="flex gap-2 mt-4">
              <TabButton
                active={activeTab === 'recommendations'}
                onClick={() => setActiveTab('recommendations')}
                count={advice.recommendations.length}
              >
                Recommandations
              </TabButton>
              <TabButton
                active={activeTab === 'threats'}
                onClick={() => setActiveTab('threats')}
                count={advice.threats.length}
                danger={advice.threats.some(t => t.level === 'critical' || t.level === 'high')}
              >
                Menaces
              </TabButton>
              <TabButton
                active={activeTab === 'opportunities'}
                onClick={() => setActiveTab('opportunities')}
                count={advice.opportunities.length}
              >
                Opportunites
              </TabButton>
              <TabButton
                active={activeTab === 'diplomatic'}
                onClick={() => setActiveTab('diplomatic')}
              >
                Diplomatie
              </TabButton>
              <TabButton
                active={activeTab === 'ai'}
                onClick={() => setActiveTab('ai')}
                ai
              >
                <Bot className="w-4 h-4 mr-1" />
                IA Ollama
              </TabButton>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {loadingAdvice ? (
            <div className="text-center py-16">
              <Loader2 className="w-12 h-12 text-amber-400 animate-spin mx-auto mb-4" />
              <p className="text-stone-500">Analyse strategique en cours...</p>
              <p className="text-stone-400 text-sm mt-1">Evaluation de votre situation</p>
            </div>
          ) : error ? (
            <div className="text-center py-16">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-stone-600">{error}</p>
              <button
                onClick={fetchAdvice}
                className="mt-4 px-4 py-2 bg-amber-500 text-white rounded-xl hover:bg-amber-600 transition"
              >
                Reessayer
              </button>
            </div>
          ) : advice ? (
            <>
              {/* Ollama AI advice banner */}
              {advice.ollama_advice && (
                <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl border border-purple-100">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Brain className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-purple-800 mb-1">Analyse IA</h4>
                      <p className="text-sm text-purple-700 whitespace-pre-wrap">{advice.ollama_advice}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommendations Tab */}
              {activeTab === 'recommendations' && (
                <div className="space-y-4">
                  {advice.recommendations.length === 0 ? (
                    <EmptyState message="Aucune recommandation specifique pour le moment." />
                  ) : (
                    advice.recommendations.map((rec, index) => (
                      <div
                        key={`${rec.action}-${index}`}
                        className={`p-5 rounded-2xl border-2 transition-all hover:shadow-md ${getActionColor(rec.action)}`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getActionIcon(rec.action)}
                            <div>
                              <h3 className="font-medium">{rec.action_fr}</h3>
                              {rec.target_name_fr && (
                                <span className="text-sm opacity-70 flex items-center gap-1">
                                  <ChevronRight className="w-3 h-3" />
                                  {COUNTRY_FLAGS[rec.target || ''] || ''} {rec.target_name_fr}
                                </span>
                              )}
                            </div>
                          </div>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            rec.priority === 1 ? 'bg-red-100 text-red-700' :
                            rec.priority === 2 ? 'bg-amber-100 text-amber-700' :
                            'bg-stone-100 text-stone-600'
                          }`}>
                            {rec.priority === 1 ? 'Prioritaire' : rec.priority === 2 ? 'Important' : 'Optionnel'}
                          </span>
                        </div>

                        <p className="text-sm opacity-80 mb-4">
                          {rec.reason_fr}
                        </p>

                        {rec.command && (
                          <div className="flex items-center justify-between">
                            <p className="text-xs italic opacity-60 flex-1 mr-4 line-clamp-1">
                              &quot;{rec.command}&quot;
                            </p>
                            <button
                              onClick={() => handleExecuteRecommendation(rec)}
                              disabled={isLoading}
                              className="px-4 py-2 bg-white/80 rounded-xl text-sm font-medium
                                hover:bg-white transition disabled:opacity-50 shadow-sm"
                            >
                              Executer
                            </button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Threats Tab */}
              {activeTab === 'threats' && (
                <div className="space-y-3">
                  {advice.threats.length === 0 ? (
                    <EmptyState message="Aucune menace majeure detectee. Situation stable." icon={Shield} />
                  ) : (
                    advice.threats.map((threat, index) => (
                      <ThreatCard key={`${threat.id}-${index}`} threat={threat} />
                    ))
                  )}
                </div>
              )}

              {/* Opportunities Tab */}
              {activeTab === 'opportunities' && (
                <div className="space-y-3">
                  {advice.opportunities.length === 0 ? (
                    <EmptyState message="Aucune opportunite identifiee pour le moment." />
                  ) : (
                    advice.opportunities.map((opp, index) => (
                      <div
                        key={`${opp.type}-${index}`}
                        className="p-4 rounded-xl bg-emerald-50 border border-emerald-100"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {opp.type === 'alliance' && <Handshake className="w-5 h-5 text-emerald-600" />}
                            {opp.type === 'economic_growth' && <TrendingUp className="w-5 h-5 text-emerald-600" />}
                            {opp.type === 'nuclear_program' && <Atom className="w-5 h-5 text-emerald-600" />}
                            {opp.type === 'influence_expansion' && <Crown className="w-5 h-5 text-emerald-600" />}
                            <span className="font-medium text-emerald-800">
                              {opp.description_fr || opp.type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            opp.priority === 'high' ? 'bg-emerald-200 text-emerald-800' :
                            opp.priority === 'medium' ? 'bg-emerald-100 text-emerald-700' :
                            'bg-stone-100 text-stone-600'
                          }`}>
                            {opp.priority === 'high' ? 'Prioritaire' : opp.priority === 'medium' ? 'Important' : 'Optionnel'}
                          </span>
                        </div>
                        {opp.target_name_fr && (
                          <p className="text-sm text-emerald-700">
                            {COUNTRY_FLAGS[opp.target_id || ''] || ''} {opp.target_name_fr}
                            {opp.relation !== undefined && (
                              <span className="ml-2 text-emerald-600">(Relations: {opp.relation > 0 ? '+' : ''}{opp.relation})</span>
                            )}
                          </p>
                        )}
                        {opp.potential && (
                          <p className="text-sm text-emerald-600">Potentiel: {opp.potential}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Diplomatic Tab */}
              {activeTab === 'diplomatic' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <StatCard
                      label="Allies"
                      value={advice.diplomatic_summary.allies_count}
                      icon={Handshake}
                      color="emerald"
                    />
                    <StatCard
                      label="Rivaux"
                      value={advice.diplomatic_summary.rivals_count}
                      icon={Swords}
                      color="red"
                    />
                    <StatCard
                      label="Guerres"
                      value={advice.diplomatic_summary.wars_count}
                      icon={AlertTriangle}
                      color={advice.diplomatic_summary.at_war ? 'red' : 'stone'}
                    />
                    <StatCard
                      label="Sanctions"
                      value={advice.diplomatic_summary.sanctions_active}
                      icon={AlertCircle}
                      color="amber"
                    />
                  </div>

                  {advice.diplomatic_summary.blocs.length > 0 && (
                    <div className="p-4 bg-sky-50 rounded-xl border border-sky-100">
                      <h4 className="text-sm font-medium text-sky-800 mb-2">Blocs et alliances</h4>
                      <div className="flex flex-wrap gap-2">
                        {advice.diplomatic_summary.blocs.map(bloc => (
                          <span key={bloc} className="px-3 py-1 bg-sky-100 text-sky-700 rounded-full text-sm">
                            {bloc}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {Object.keys(advice.diplomatic_summary.superpower_relations).length > 0 && (
                    <div className="p-4 bg-stone-50 rounded-xl border border-stone-100">
                      <h4 className="text-sm font-medium text-stone-700 mb-3">Relations avec les grandes puissances</h4>
                      <div className="space-y-2">
                        {Object.entries(advice.diplomatic_summary.superpower_relations).map(([countryId, relation]) => (
                          <div key={countryId} className="flex items-center justify-between">
                            <span className="flex items-center gap-2">
                              <span className="text-lg">{COUNTRY_FLAGS[countryId] || ''}</span>
                              <span className="text-sm text-stone-600">{countryId}</span>
                            </span>
                            <span className={`text-sm font-medium ${
                              relation > 30 ? 'text-emerald-600' :
                              relation > 0 ? 'text-emerald-500' :
                              relation > -30 ? 'text-stone-500' :
                              'text-red-500'
                            }`}>
                              {relation > 0 ? '+' : ''}{relation}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* AI Advisor Tab */}
              {activeTab === 'ai' && playerCountryId && (
                <AIAdvisorPanel
                  countryId={playerCountryId}
                  year={world?.year || 2025}
                />
              )}
            </>
          ) : (
            <EmptyState message="Selectionnez un pays pour obtenir des conseils." />
          )}
        </div>

        {/* Footer */}
        <div className="px-8 py-4 border-t border-stone-100 bg-stone-50 flex justify-between items-center">
          <button
            onClick={fetchAdvice}
            disabled={loadingAdvice}
            className="text-sm text-stone-500 hover:text-stone-700 transition flex items-center gap-1"
          >
            <Brain className="w-4 h-4" />
            Actualiser l'analyse
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2 text-stone-600 hover:bg-stone-100 rounded-xl transition"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

// Tab button component
function TabButton({
  children,
  active,
  onClick,
  count,
  danger,
  ai,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
  count?: number;
  danger?: boolean;
  ai?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center ${
        ai
          ? active
            ? 'bg-purple-100 text-purple-800'
            : 'text-purple-500 hover:bg-purple-50'
          : active
            ? 'bg-amber-100 text-amber-800'
            : 'text-stone-500 hover:bg-stone-100'
      }`}
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className={`ml-1.5 px-1.5 py-0.5 text-xs rounded-full ${
          danger ? 'bg-red-100 text-red-700' :
          active ? (ai ? 'bg-purple-200 text-purple-800' : 'bg-amber-200 text-amber-800') : 'bg-stone-200 text-stone-600'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}

// Threat card component
function ThreatCard({ threat }: { threat: StrategicThreat }) {
  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-50 border-red-200';
      case 'high': return 'bg-orange-50 border-orange-200';
      case 'medium': return 'bg-amber-50 border-amber-200';
      case 'low': return 'bg-stone-50 border-stone-200';
      default: return 'bg-stone-50 border-stone-200';
    }
  };

  const getThreatBadgeColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'medium': return 'bg-amber-100 text-amber-700';
      case 'low': return 'bg-stone-100 text-stone-600';
      default: return 'bg-stone-100 text-stone-600';
    }
  };

  const getThreatLevelText = (level: string) => {
    switch (level) {
      case 'critical': return 'Critique';
      case 'high': return 'Eleve';
      case 'medium': return 'Modere';
      case 'low': return 'Faible';
      default: return 'Inconnu';
    }
  };

  return (
    <div className={`p-4 rounded-xl border ${getThreatLevelColor(threat.level)}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">{COUNTRY_FLAGS[threat.id] || ''}</span>
          <div>
            <h4 className="font-medium text-stone-800">{threat.name_fr}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-stone-500">
                {threat.type === 'war' ? 'En guerre' : threat.type === 'rival' ? 'Rival' : 'Systemique'}
              </span>
              {threat.power_diff !== 0 && (
                <span className={`text-xs ${threat.power_diff > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  (Puissance: {threat.power_diff > 0 ? '+' : ''}{threat.power_diff})
                </span>
              )}
            </div>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getThreatBadgeColor(threat.level)}`}>
          {getThreatLevelText(threat.level)}
        </span>
      </div>
    </div>
  );
}

// Stat card component
function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  const colors: Record<string, string> = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    stone: 'bg-stone-50 text-stone-600 border-stone-100',
  };

  return (
    <div className={`p-4 rounded-xl border ${colors[color] || colors.stone}`}>
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5" />
        <div>
          <p className="text-2xl font-semibold">{value}</p>
          <p className="text-xs opacity-70">{label}</p>
        </div>
      </div>
    </div>
  );
}

// Empty state component
function EmptyState({ message, icon: Icon = Target }: { message: string; icon?: React.ElementType }) {
  return (
    <div className="text-center py-12">
      <Icon className="w-12 h-12 text-stone-300 mx-auto mb-3" />
      <p className="text-stone-500">{message}</p>
    </div>
  );
}
