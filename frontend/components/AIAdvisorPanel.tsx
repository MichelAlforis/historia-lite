'use client';

import { useState, useEffect, useCallback } from 'react';
import { useGameStore } from '@/stores/gameStore';
import {
  getAIStrategicAdvice,
  getAIAnnualBriefing,
  getAIMediaComment,
  getAIDiplomaticDialogue,
  getAIAdvisorStatus,
  AIStrategicAdvice,
  AIAnnualBriefing,
  AIMediaComment,
  AIDiplomaticDialogue,
} from '@/lib/api';
import { COUNTRY_FLAGS } from '@/lib/types';
import {
  Brain,
  Newspaper,
  FileText,
  MessageSquare,
  Loader2,
  AlertTriangle,
  TrendingUp,
  Shield,
  Handshake,
  Swords,
  Building,
  Sparkles,
  ChevronRight,
  RefreshCw,
  Target,
  Zap,
  Globe,
} from 'lucide-react';

interface AIAdvisorPanelProps {
  countryId: string;
  targetCountryId?: string;
  year: number;
}

type AITab = 'advice' | 'briefing' | 'media' | 'dialogue';

export default function AIAdvisorPanel({
  countryId,
  targetCountryId,
  year,
}: AIAdvisorPanelProps) {
  const [activeTab, setActiveTab] = useState<AITab>('advice');
  const [aiAvailable, setAiAvailable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [advices, setAdvices] = useState<AIStrategicAdvice[]>([]);
  const [briefing, setBriefing] = useState<AIAnnualBriefing | null>(null);
  const [mediaComment, setMediaComment] = useState<AIMediaComment | null>(null);
  const [dialogue, setDialogue] = useState<AIDiplomaticDialogue | null>(null);

  // Check AI status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getAIAdvisorStatus();
        setAiAvailable(status.available);
      } catch {
        setAiAvailable(false);
      }
    };
    checkStatus();
  }, []);

  // Fetch data based on active tab
  const fetchData = useCallback(async () => {
    if (!countryId || !aiAvailable) return;

    setLoading(true);
    setError(null);

    try {
      switch (activeTab) {
        case 'advice': {
          const result = await getAIStrategicAdvice(countryId);
          if (result.success) {
            setAdvices(result.advices);
          } else {
            setError(result.error || 'Erreur lors de la generation des conseils');
          }
          break;
        }
        case 'briefing': {
          const result = await getAIAnnualBriefing(countryId);
          if (result.success && result.briefing) {
            setBriefing(result.briefing);
          } else {
            setError(result.error || 'Briefing deja genere cette annee');
          }
          break;
        }
        case 'media': {
          const result = await getAIMediaComment(countryId);
          if (result.success && result.comment) {
            setMediaComment(result.comment);
          } else {
            setError(result.error || 'Erreur lors de la generation du commentaire');
          }
          break;
        }
        case 'dialogue': {
          if (!targetCountryId) {
            setError('Selectionnez un pays cible pour les dialogues');
            break;
          }
          const result = await getAIDiplomaticDialogue(countryId, targetCountryId, 'general');
          if (result.success && result.dialogue) {
            setDialogue(result.dialogue);
          } else {
            setError(result.error || 'Erreur lors de la generation du dialogue');
          }
          break;
        }
      }
    } catch (err) {
      setError('Erreur de communication avec l\'IA');
      console.error('AI Advisor error:', err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, countryId, targetCountryId, aiAvailable]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!aiAvailable) {
    return (
      <div className="p-6 text-center">
        <Brain className="w-12 h-12 text-stone-300 mx-auto mb-3" />
        <p className="text-stone-500">Conseiller IA non disponible</p>
        <p className="text-stone-400 text-sm mt-1">
          Verifiez que le serveur Ollama est actif
        </p>
      </div>
    );
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'economy': return <TrendingUp className="w-4 h-4" />;
      case 'military': return <Swords className="w-4 h-4" />;
      case 'diplomacy': return <Handshake className="w-4 h-4" />;
      case 'security': return <Shield className="w-4 h-4" />;
      case 'stability': return <Building className="w-4 h-4" />;
      default: return <Target className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200';
      default: return 'bg-stone-100 text-stone-600 border-stone-200';
    }
  };

  const getThreatColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-amber-600';
      default: return 'text-stone-500';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return <TrendingUp className="w-4 h-4 text-emerald-500" />;
      case 'negative': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Globe className="w-4 h-4 text-stone-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-stone-100 pb-3">
        <TabButton
          active={activeTab === 'advice'}
          onClick={() => setActiveTab('advice')}
          icon={<Brain className="w-4 h-4" />}
        >
          Conseils IA
        </TabButton>
        <TabButton
          active={activeTab === 'briefing'}
          onClick={() => setActiveTab('briefing')}
          icon={<FileText className="w-4 h-4" />}
        >
          Briefing {year}
        </TabButton>
        <TabButton
          active={activeTab === 'media'}
          onClick={() => setActiveTab('media')}
          icon={<Newspaper className="w-4 h-4" />}
        >
          Presse
        </TabButton>
        {targetCountryId && (
          <TabButton
            active={activeTab === 'dialogue'}
            onClick={() => setActiveTab('dialogue')}
            icon={<MessageSquare className="w-4 h-4" />}
          >
            Dialogue
          </TabButton>
        )}
      </div>

      {/* Refresh button */}
      <div className="flex justify-end">
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 text-sm text-stone-500 hover:text-stone-700 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-3" />
          <p className="text-stone-500">Generation en cours...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="p-4 bg-red-50 rounded-xl border border-red-100">
          <div className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Content */}
      {!loading && !error && (
        <>
          {/* Strategic Advice Tab */}
          {activeTab === 'advice' && advices.length > 0 && (
            <div className="space-y-3">
              {advices.map((advice, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border ${getPriorityColor(advice.priority)}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(advice.category)}
                      <h4 className="font-medium">{advice.title_fr}</h4>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/50">
                      {advice.priority === 'critical' ? 'Critique' :
                       advice.priority === 'high' ? 'Important' :
                       advice.priority === 'medium' ? 'Modere' : 'Faible'}
                    </span>
                  </div>
                  <p className="text-sm opacity-90 mb-2">{advice.advice_fr}</p>
                  <p className="text-xs opacity-70 italic">{advice.reasoning_fr}</p>
                  {advice.suggested_action && (
                    <div className="mt-3 pt-3 border-t border-current/10">
                      <div className="flex items-center gap-1 text-xs">
                        <Zap className="w-3 h-3" />
                        <span className="font-medium">Action suggeree:</span>
                        <span className="opacity-80">{advice.suggested_action}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Briefing Tab */}
          {activeTab === 'briefing' && briefing && (
            <div className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  <h4 className="font-medium text-indigo-800">
                    Briefing annuel {briefing.year}
                  </h4>
                </div>
                <p className="text-sm text-indigo-700">{briefing.executive_summary_fr}</p>
              </div>

              {/* Threats */}
              {briefing.threats.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-stone-600 mb-2 flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    Menaces identifiees
                  </h5>
                  <div className="space-y-2">
                    {briefing.threats.map((threat, idx) => (
                      <div key={idx} className="p-3 bg-red-50 rounded-lg border border-red-100">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{COUNTRY_FLAGS[threat.country] || ''}</span>
                          <span className="font-medium text-red-800">{threat.country}</span>
                          <span className={`text-xs ${getThreatColor(threat.threat_level)}`}>
                            ({threat.threat_level})
                          </span>
                        </div>
                        <p className="text-sm text-red-700">{threat.description_fr}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Opportunities */}
              {briefing.opportunities.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-stone-600 mb-2 flex items-center gap-1">
                    <Sparkles className="w-4 h-4 text-emerald-500" />
                    Opportunites
                  </h5>
                  <div className="space-y-2">
                    {briefing.opportunities.map((opp, idx) => (
                      <div key={idx} className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                        <span className="text-xs font-medium text-emerald-600 uppercase">
                          {opp.domain}
                        </span>
                        <p className="text-sm text-emerald-700 mt-1">{opp.description_fr}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {briefing.recommendations.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-stone-600 mb-2 flex items-center gap-1">
                    <ChevronRight className="w-4 h-4" />
                    Recommandations
                  </h5>
                  <ul className="space-y-1">
                    {briefing.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-stone-600 flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Media Tab */}
          {activeTab === 'media' && mediaComment && (
            <div className="p-4 bg-stone-50 rounded-xl border border-stone-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Newspaper className="w-5 h-5 text-stone-600" />
                  <span className="font-medium text-stone-700">{mediaComment.source}</span>
                </div>
                {getSentimentIcon(mediaComment.sentiment)}
              </div>
              <h4 className="text-lg font-semibold text-stone-800 mb-2">
                {mediaComment.headline_fr}
              </h4>
              <p className="text-sm text-stone-600 italic">
                &quot;{mediaComment.excerpt_fr}&quot;
              </p>
            </div>
          )}

          {/* Dialogue Tab */}
          {activeTab === 'dialogue' && dialogue && (
            <div className="p-4 bg-gradient-to-r from-sky-50 to-blue-50 rounded-xl border border-sky-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{COUNTRY_FLAGS[dialogue.speaker_country] || ''}</span>
                <div>
                  <h4 className="font-medium text-sky-800">{dialogue.speaker_name}</h4>
                  <p className="text-xs text-sky-600">{dialogue.speaker_title}</p>
                </div>
                <span className={`ml-auto px-2 py-0.5 text-xs rounded-full ${
                  dialogue.tone === 'friendly' ? 'bg-emerald-100 text-emerald-700' :
                  dialogue.tone === 'hostile' ? 'bg-red-100 text-red-700' :
                  dialogue.tone === 'formal' ? 'bg-blue-100 text-blue-700' :
                  'bg-stone-100 text-stone-600'
                }`}>
                  {dialogue.tone === 'friendly' ? 'Amical' :
                   dialogue.tone === 'hostile' ? 'Hostile' :
                   dialogue.tone === 'formal' ? 'Formel' : 'Neutre'}
                </span>
              </div>
              <div className="bg-white/50 rounded-lg p-3">
                <p className="text-sky-800 italic">&quot;{dialogue.message_fr}&quot;</p>
              </div>
              {dialogue.context && (
                <p className="text-xs text-sky-600 mt-2">Contexte: {dialogue.context}</p>
              )}
            </div>
          )}

          {/* Empty states */}
          {activeTab === 'advice' && advices.length === 0 && !error && (
            <EmptyState message="Aucun conseil disponible pour le moment." />
          )}
          {activeTab === 'briefing' && !briefing && !error && (
            <EmptyState message="Le briefing annuel sera disponible au debut de l'annee." />
          )}
          {activeTab === 'media' && !mediaComment && !error && (
            <EmptyState message="Aucun commentaire de presse disponible." />
          )}
          {activeTab === 'dialogue' && !dialogue && !targetCountryId && !error && (
            <EmptyState message="Selectionnez un pays pour voir les dialogues diplomatiques." />
          )}
        </>
      )}
    </div>
  );
}

// Tab button component
function TabButton({
  children,
  active,
  onClick,
  icon,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
        active
          ? 'bg-purple-100 text-purple-700'
          : 'text-stone-500 hover:bg-stone-100'
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

// Empty state
function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-8">
      <Brain className="w-10 h-10 text-stone-300 mx-auto mb-2" />
      <p className="text-stone-500 text-sm">{message}</p>
    </div>
  );
}
